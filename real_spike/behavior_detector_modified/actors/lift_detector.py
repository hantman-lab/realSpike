from improv.actor import ZmqActor
import logging
import time
import uuid
import os
import numpy as np

from real_spike.utils import BehaviorLogger, LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LIFT_DETECTED = False


class LiftDetector(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "LiftDetector"
        # start the video from queue
        self.frame_num = None
        self.trial_num = None
        self.latency = LatencyLogger(
            name="lift_detector",
            max_size=50_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        self.reshape_size = (290, 448)
        self.crop = [136, 155, 207, 220]
        self.behavior_logger = BehaviorLogger("test-logger")

        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        self.improv_logger.info("Lift detector stopping")
        self.latency.save()
        self.behavior_logger.save()
        return 0

    def run_step(self):
        global LIFT_DETECTED
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            t = time.perf_counter_ns()
            data = np.frombuffer(self.client.client.get(data_id), np.uint32)
            self.frame_num = int(data[-1])
            self.trial_num = int(data[-2])
            self.frame = data[:-2].reshape(*self.reshape_size)

            # will never see a lift before the pellet actually comes forward
            if self.frame_num <= 550:
                return

            if self.frame_num == 850:
                if not LIFT_DETECTED:
                    self.behavior_logger.log(self.trial_num, "LIFT NOT DETECTED")
                    self.improv_logger.info("LIFT NOT DETECTED")
                LIFT_DETECTED = False
                return

            if LIFT_DETECTED:
                # lift already detected for this trial
                return

            # y-dim comes first (height, width)
            self.frame = self.frame[
                self.crop[2] : self.crop[3], self.crop[0] : self.crop[1]
            ]

            if (self.frame != 0).sum() >= 180:
                LIFT_DETECTED = True
                self.improv_logger.info(f"LIFT DETECTED: frame {self.frame_num}")
                # output detection
                self.behavior_logger.log(self.trial_num, self.frame_num)

            # for every frame could send a zero or 1 to laser, if 1 that means trigger
            store_id = str(os.getpid()) + str(uuid.uuid4())
            if LIFT_DETECTED:
                detected_value = 1
            else:
                detected_value = 0

            self.client.client.set(store_id, detected_value, nx=False)
            self.client.client.expire(store_id, 5)
            self.q_out.put(store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
