from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import os
import serial

from real_spike.utils import LatencyLogger

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

        port_name = "/dev/ttyACM0"
        baud_rate = 9600  # Check your device's documentation for the correct baud rate

        self.ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=1)
        self.improv_logger.info("OPENED PORT")
        self.ser.reset_input_buffer()

        self.improv_logger.info("Completed setup for Cue Generator")

    def stop(self):
        self.improv_logger.info("Cue generator stopping")
        self.latency.save()
        return 0

    def run_step(self):
        t = time.perf_counter_ns()

        bytes_available = self.ser.in_waiting

        if bytes_available > 0:
            line = self.ser.readline().decode(errors="ignore").strip()
            if line == "1":
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

            if self.frame_num % 50 == 0:
                self.ser.reset_input_buffer()
