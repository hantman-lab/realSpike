from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import random

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger, get_vmax, get_imax, get_gain, get_meta, fetch, get_sample_data, get_sample_rate
from real_spike.utils.sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0
        self.latency = LatencyLogger(name=f"generator_acquisition_netgear")

        # specify num channels to take
        self.num_channels = 150
        self.channel_ids = [i for i in range(50, 50+self.num_channels)]

    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # create a spikeglx handle
        self.hSglx = sglx.c_sglx_createHandle()

        # connect to a given ip_address and port number
        ip_address = "192.168.0.101"
        port = 4142
 
        if sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port):
            self.improv_logger.info("Successfully connected to SpikeGLX")
            self.improv_logger.info("version <{}>\n".format(sglx.c_sglx_getVersion(self.hSglx)))

            # get vmax, imax, and gain
            self.Vmax = get_vmax(self.hSglx)
            self.Imax = get_imax(self.hSglx)
            self.gain = get_gain(self.hSglx)
            
            self.sample_rate = get_sample_rate(self.hSglx)
            self.window = int(1 * self.sample_rate / 1_000)
        else:
            self.improv_logger.info("error [{}]\n".format(sglx.c_sglx_getError(self.hSglx)))
            raise Exception

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")

        # close the connection and handler
        sglx.c_sglx_close(self.hSglx)
        sglx.c_sglx_destroyHandle(self.hSglx)
        # save the latency
        self.latency.save()
        return 0

    def run_step(self):
        if self.frame_num % 1000 == 0:
            self.improv_logger.info(f"{self.frame_num} frames")
        # TODO: monitor the store size and stop generator if it is too close to the max
        if self.frame_num > 2500:
            return
      
        # fetch using sglx handler
        t = time.perf_counter_ns()
        data = fetch(self.hSglx, channel_ids=self.channel_ids)

        # convert the data from analog to voltage
        data = 1e6 * data * self.Vmax / self.Imax / self.gain
        data = data.reshape(self.num_channels, self.window).T

        # send to processor
        data_id = str(os.getpid()) + str(uuid.uuid4())
        self.client.client.set(data_id, data.tobytes(), nx=True)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.client.client.expire(data_id, 15)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
