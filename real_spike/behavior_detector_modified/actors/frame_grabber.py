from improv.actor import ZmqActor
import logging
import time
import uuid
import os
import numpy as np

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CUE_DETECTED = False


class CameraGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CameraGenerator"
        self.latency = LatencyLogger(
            name="generator_camera",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # every time we get a new cue, want to increment trial number
        self.trial_num = None
        self.frame_num = None

        # TODO: any connection related things to bias

        self.improv_logger.info("Completed setup for Camera Generator")

    def stop(self):
        self.improv_logger.info("Camera generator stopping")
        self.latency.save()

        # TODO: close any connection related things for bias

        return 0

    def run_step(self):
        global CUE_DETECTED
        t = time.perf_counter()

        # currently in a trial
        if CUE_DETECTED:
            # end of trial
            if self.frame_num == 851:
                self.frame_num = None
                CUE_DETECTED = False
                return
            # otherwise, need to fetch frame from camera
            # TODO: grab a frame camera_fetch()
            frame = np.random.rand(290, 448)

            data = np.append(frame.ravel, self.trial_num)
            data = np.append(data, self.frame_num)
            data_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(data_id, data.astype(np.uint32).tobytes(), nx=False)
            try:
                self.improv_logger.info("SENDING FRAME")
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
                self.frame_num += 1
            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
        else:  # cue has not been detected yet
            data_id = None

            try:
                # get data_id from queue in
                data_id = self.q_in.get(timeout=0.05)
            except Exception as e:
                pass

            if data_id is not None:
                self.trial_num = self.client.client.get(data_id)
                self.improv_logger.info(f"CUE RECEIVED, TRIAL_NUM: {self.trial_num}")
                self.frame_num = 500
                CUE_DETECTED = True
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                return
