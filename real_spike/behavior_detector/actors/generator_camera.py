from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import os
import cv2
from threading import Event
import nidaqmx
from nidaqmx.constants import AcquisitionType

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Generator"
        self.latency = LatencyLogger(
            name="generator_behavior_camera",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # TODO: any kind of connection to the machine that gets the frames from the camera; probably a zmq port

        # bool for setting whether cue has been received
        # put in separate thread from the nidaq task to make sure it gets set properly
        self.cue_signal = Event()

        self.trial_num = 0
        self.frame_num = 500

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")
        self.latency.save()
        return 0

    def run_step(self):
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            t = time.perf_counter_ns()
            self.trial_num = self.client.client.get(data_id)
            self.improv_logger.info("RECEIVED CUE, START FETCHING FRAMES")

            # TODO: get the frame via some request

            self.frame = np.random.rand(512, 512)

            # convert to grayscale
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY).astype(np.uint16)
            # make a data_id
            data_id = str(os.getpid()) + str(uuid.uuid4())

            data = np.append(self.frame.ravel(), self.trial_num).astype(np.uint32)
            data = np.append(data, self.frame_num).astype(np.uint32)

            self.client.client.set(data_id, data.tobytes(), nx=False)
            try:
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
                self.frame_num += 1

            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
