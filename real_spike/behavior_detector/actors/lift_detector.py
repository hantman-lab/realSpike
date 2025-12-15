import pickle

from improv.actor import ZmqActor
import logging
import time
import cv2
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LIFT_DETECTED = False

class LiftDetector(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Detector"
        # start the video from queue
        self.frame_num = None
        self.latency = LatencyLogger(name="lift_behavior_detector",
                                     max_size=20_000,
                                     )
        self.offset = 0

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        self.reshape_size = (290, 448)
        self.crop = [136, 155, 207, 220]

        # reset the text file
        with open('/home/clewis/repos/realSpike/data/rb50_lift.txt', 'w') as file_object:
            pass
        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        self.improv_logger.info("Lift detector stopping")
        self.latency.save()
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
            data = np.frombuffer(self.client.client.get(data_id), np.uint16)
            self.frame_num = data[-1]
            self.frame = data[:-1].reshape(*self.reshape_size)

            if self.frame_num == 849:
                if not LIFT_DETECTED:
                    with open('/home/clewis/repos/realSpike/data/rb50_lift.txt', 'a') as f:
                        f.write(f"LIFT NOT DETECTED\n")
                    self.improv_logger.info(f"LIFT NOT DETECTED")
                LIFT_DETECTED = False
                self.offset += 250
                return


            if LIFT_DETECTED:
                # lift already detected for this trial
                return

            # y-dim comes first (height, width)
            self.frame = self.frame[self.crop[2]:self.crop[3], self.crop[0]:self.crop[1]]

            if (self.frame != 0).sum() >= 180:
                LIFT_DETECTED = True
                self.improv_logger.info(f"LIFT DETECTED: frame {self.frame_num}")
                # output detection
                with open('/home/clewis/repos/realSpike/data/rb50_lift.txt', 'a') as f:
                    f.write(f"{self.frame_num}\n")

            # for every frame could send a zero or 1 to pattern generator, if 1 that means trigger
            store_id = str(os.getpid()) + str(uuid.uuid4())
            if LIFT_DETECTED:
                detected_value = 1
            else:
                detected_value = 0

            self.client.client.set(store_id, detected_value, nx=False)
            self.client.client.expire(store_id, 15)
            self.q_out.put(store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.offset + self.frame_num, t2 - t)

