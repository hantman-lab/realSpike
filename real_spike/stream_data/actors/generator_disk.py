import os
import tifffile
import logging
import time
import uuid
import numpy as np

from real_spike.utils import LatencyLogger, get_meta, get_sample_data
from improv.actor import ZmqActor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0
        self.latency = LatencyLogger(name="generator_stream_disk")

        self.num_channels = 150


    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # load the data
        self.meta_data = get_meta("/home/clewis/repos/realSpike/data/120s_test/rb50_20250126_g0_t0.imec0.ap.meta")
        self.sample_data = get_sample_data("/home/clewis/repos/realSpike/data/120s_test/rb50_20250126_g0_t0.imec0.ap.bin", self.meta_data)

        # specify step size, send 1 ms of data at a time
        self.sample_rate = float(self.meta_data['imSampRate'])
        # 5ms = 1 sec of data (30_000 time points) / 1_000 * 5
        self.window = int(1 * self.sample_rate / 1_000)

        # get Vmax
        self.Vmax = float(self.meta_data["imAiRangeMax"])
        # get Imax
        self.Imax = float(self.meta_data["imMaxInt"])
        # get gain
        self.gain = float(self.meta_data['imroTbl'].split(sep=')')[1].split(sep=' ')[3])

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")
        self.latency.save()
        return 0
    
    def fetch(self):
        """Return 5ms of analog data stored on disk."""
        l_time = int(self.frame_num * self.window)
        r_time = int((self.frame_num * self.window) + self.window)
        if r_time > self.sample_data.shape[1]:
            return np.full((self.num_channels, self.window), np.nan)
        return self.sample_data[50:self.num_channels+50, l_time:r_time].ravel()

    def run_step(self):
        if self.frame_num % 1000 == 0:
            self.improv_logger.info(f"{self.frame_num} frames")
        if self.frame_num > 5_000:
            return

        t = time.perf_counter_ns()
        data = self.fetch()

        # convert the data from analog to voltage
        data = 1e6 * data * self.Vmax / self.Imax / self.gain
        data = data.reshape(self.num_channels, self.window)


        # send to processor
        data_id = str(os.getpid()) + str(uuid.uuid4())
        self.client.client.set(data_id, data.tobytes(), nx=False)
        try:
            self.q_out.put(data_id)
            self.client.client.expire(data_id, 5)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
