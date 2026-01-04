from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import os

from real_spike.utils import (
    LatencyLogger,
    get_vmax,
    get_imax,
    get_gain,
    get_meta,
    fetch,
    get_sample_data,
    get_sample_rate,
)
from real_spike.utils.sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# streaming from disk flag
# when False, streaming over Duke network
DEBUG_MODE = False


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0
        self.latency = LatencyLogger(name=f"generator_acquisition_disk_{DEBUG_MODE}")

        # specify num channels to take
        self.num_channels = 150
        # get channels 50 to 200
        self.channel_ids = [i for i in range(50, 50 + self.num_channels)]

    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # create a spikeglx handle
        self.hSglx = sglx.c_sglx_createHandle()

        # connect to a given ip_address and port number
        ip_address = "10.172.70.238"
        port = 4142

        # only make a connection if not in debug mode
        if not DEBUG_MODE:
            if sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port):
                self.improv_logger.info("Successfully connected to SpikeGLX")
                self.improv_logger.info(
                    "version <{}>\n".format(sglx.c_sglx_getVersion(self.hSglx))
                )

                # get vmax, imax, and gain
                self.Vmax = get_vmax(self.hSglx)
                self.Imax = get_imax(self.hSglx)
                self.gain = get_gain(self.hSglx)

                self.sample_rate = get_sample_rate(self.hSglx)
                self.window = int(1 * self.sample_rate / 1_000)

            else:
                self.improv_logger.info(
                    "error [{}]\n".format(sglx.c_sglx_getError(self.hSglx))
                )
                raise Exception
        else:
            self.meta_data = get_meta(
                "/home/clewis/repos/realSpike/data/120s_test/rb50_20250126_g0_t0.imec0.ap.meta"
            )
            self.sample_data = get_sample_data(
                "/home/clewis/repos/realSpike/data/120s_test/rb50_20250126_g0_t0.imec0.ap.bin",
                self.meta_data,
            )

            # specify sampling rate
            self.sample_rate = float(self.meta_data["imSampRate"])
            # 1ms = 1 sec of data (30_000 time points) / 1_000 * 1
            self.window = int(1 * self.sample_rate / 1_000)

            # get Vmax
            self.Vmax = float(self.meta_data["imAiRangeMax"])
            # get Imax
            self.Imax = float(self.meta_data["imMaxInt"])
            # get gain
            self.gain = float(
                self.meta_data["imroTbl"].split(sep=")")[1].split(sep=" ")[3]
            )

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")

        # close the connection and handler
        sglx.c_sglx_close(self.hSglx)
        sglx.c_sglx_destroyHandle(self.hSglx)
        # save the latency
        self.latency.save()
        return 0

    def fetch(self):
        """Return 1ms of analog data stored on disk."""
        l_time = int(self.frame_num * self.window)
        r_time = int((self.frame_num * self.window) + self.window)
        if r_time > self.sample_data.shape[1]:
            return np.full((self.num_channels, self.window), np.nan)
        return self.sample_data[: self.num_channels, l_time:r_time].ravel()

    def run_step(self):
        # if self.frame_num > 3_999:
        #     return
        if self.frame_num % 1000 == 0:
            self.improv_logger.info(f"{self.frame_num} frames")

        if DEBUG_MODE:
            # use fake fetch function
            t = time.perf_counter_ns()
            data = self.fetch()
        else:
            # fetch using sglx handler
            t = time.perf_counter_ns()
            data = fetch(
                self.hSglx, num_samps=self.window, channel_ids=self.channel_ids
            )

        # convert the data from analog to voltage
        data = 1e6 * data * self.Vmax / self.Imax / self.gain
        data = data.reshape(self.num_channels, self.window)

        if not DEBUG_MODE:
            data = data.T

        # send to processor
        data_id = str(os.getpid()) + str(uuid.uuid4())
        self.client.client.set(data_id, data.tobytes(), nx=False)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(None, self.frame_num, t2 - t)
            self.client.client.expire(data_id, 15)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
