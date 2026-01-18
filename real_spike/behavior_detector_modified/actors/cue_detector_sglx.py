from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import os

from real_spike.utils import LatencyLogger, fetch, get_multiplier
from real_spike.utils.sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CueGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CueGenerator"
        self.latency = LatencyLogger(
            name="generator_cue",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # every time we get a new cue, want to increment trial number
        self.trial_num = 0
        self.frame_num = 0

        # connect to spikeglx
        ip_address = "10.172.7.148"
        port = 4142

        # create a spikeglx handle
        self.hSglx = sglx.c_sglx_createHandle()

        if sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port):
            self.improv_logger.info("Successfully connected to SpikeGLX")
            self.improv_logger.info(
                "version <{}>\n".format(sglx.c_sglx_getVersion(self.hSglx))
            )

        self.conversion_factor = get_multiplier(self.hSglx)

        self.improv_logger.info("Completed setup for Cue Generator")

    def stop(self):
        self.improv_logger.info("Cue generator stopping")
        self.latency.save()

        # close the connection and handler
        sglx.c_sglx_close(self.hSglx)
        sglx.c_sglx_destroyHandle(self.hSglx)
        return 0

    def run_step(self):
        t = time.perf_counter_ns()

        # fetch latest data for nidaq channel 2 and see if there is a threshold crossing
        # fetching for the most recent 3ms of data
        data = fetch(self.hSglx, js=0, num_samps=90, channel_ids=[2])
        data = data * self.conversion_factor

        if np.any(data > 4.0):
            # detected a cue

            # make a data_id
            data_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(data_id, self.trial_num, nx=False)
            try:
                self.improv_logger.info(f"CUE DETECTED, TRIAL: {self.trial_num}")
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
                self.trial_num += 1
            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
        else:
            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
        self.frame_num += 1
