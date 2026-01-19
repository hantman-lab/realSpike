from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import os
import serial

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

        self.ser = serial.Serial("/dev/ttyACM0", 9600, timeout=5)
        # self.ser.reset_input_buffer()
        # self.ser.flush()

        self.improv_logger.info("Opened serial port")
        # self.ser.flush()

        # TODO: open zmq to PDM to send cue for pattern refresh

        # connect to spikeglx
        # ip_address = "192.168.0.101"
        # port = 4142
        #
        # # create a spikeglx handle
        # self.hSglx = sglx.c_sglx_createHandle()
        #
        # if sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port):
        #     self.improv_logger.info("Successfully connected to SpikeGLX")
        #     self.improv_logger.info(
        #         "version <{}>\n".format(sglx.c_sglx_getVersion(self.hSglx))
        #     )
        #
        # self.conversion_factor = get_multiplier(self.hSglx)

        self.improv_logger.info("Completed setup for Cue Generator")

    def stop(self):
        self.improv_logger.info("Cue generator stopping")
        self.latency.save()

        # close serial port
        self.ser.close()

        # close the connection and handler
        # sglx.c_sglx_close(self.hSglx)
        # sglx.c_sglx_destroyHandle(self.hSglx)
        return 0

    def run_step(self):
        t = time.perf_counter_ns()

        # fetch latest data for nidaq channel 2 and see if there is a threshold crossing
        # fetching for the most recent 3ms of data
        # data = fetch(self.hSglx, js=0, num_samps=90, channel_ids=[2])
        # data = data * self.conversion_factor

        # detected a cue
        # if np.any(data > 4.0):

        bytes_available = self.ser.in_waiting
        if bytes_available > 0:
            raw = self.ser.read(bytes_available).decode(errors="ignore").strip()
            self.improv_logger.info(f"Received {raw}")
            dig_vector = [int(c) for c in raw if c.isdigit()]

            if dig_vector:  # make sure list is not empty
                analog_from_port = max(dig_vector)
                self.improv_logger.info(f"Received {analog_from_port}")

                if analog_from_port == 1:
                    # Trigger received
                    self.improv_logger.info("Cue detected!")
                    self.ser.reset_input_buffer()

            # if line == "1":
            #     # make a data_id
            #     data_id = str(os.getpid()) + str(uuid.uuid4())
            #
            #     self.client.client.set(data_id, self.trial_num, nx=False)
            #     try:
            #         self.improv_logger.info(f"CUE DETECTED, TRIAL: {self.trial_num}")
            #         self.q_out.put(data_id)
            #         t2 = time.perf_counter_ns()
            #         self.latency.add(self.trial_num, self.frame_num, t2 - t)
            #         self.client.client.expire(data_id, 5)
            #         self.trial_num += 1
            #         self.ser.flush()
            #         self.ser.reset_input_buffer()
            #     except Exception as e:
            #         self.improv_logger.error(f"Generator Exception: {e}")

        t2 = time.perf_counter_ns()
        self.latency.add(self.trial_num, self.frame_num, t2 - t)
        self.frame_num += 1
