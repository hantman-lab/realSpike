from improv.actor import ZmqActor
import logging
import time

import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LIFT_DETECTED = False

class Detector(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.frames = list() # store the marked frames from OpenCV to look at after
        self.name = "Detector"
        # start the video from queue
        self.frame_num = 500
        self.latency = LatencyLogger(name="detector_behavior_detector", max_size=2_000)

        # sample rate = 500Hz
        # self.sample_rate = 500

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # setup whatever model is being used here

        self.reshape_size = (133, 139)
        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        self.improv_logger.info("Detector stopping")
        self.latency.save()
        return 0

    def run_step(self):
        global LIFT_DETECTED
        if LIFT_DETECTED:
            # lift already detected for this trial
            # reset frame num
            # update trial num if keeping track of it (undecided for now)
            return
        data_id = None
        t = time.perf_counter_ns()
        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            self.frame = np.frombuffer(self.client.client.get(data_id), np.uint8).reshape(*self.reshape_size)
            #  .reshape(*self.resize_shape)
            # TODO: model running for lift detection
            # if lift detection, send control signal to pattern generator
            # have a running flag for if lift has been detected in this trial (once I start going through more and more videos, can track trial number)
            # should also save out which frame in the video I detected lift on so that I can validate with what Reagan has marked)
            self.frames.append(self.frame)

            # for every frame could send a zero or 1 to pattern generator, if 1 that means trigger
            # TODO: decide if I want to reuse the data_id here or create a new one, create new one for now
            store_id = str(os.getpid()) + str(uuid.uuid4())
            if LIFT_DETECTED:
                detected_value = 1
                LIFT_DETECTED = True
            else:
                detected_value = 0

            self.client.client.set(store_id, detected_value.to_bytes(), nx=True)
            self.q_out.put(store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

