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

GRAB_DETECTED = False

class GrabDetector(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Detector"
        # start the video from queue
        self.frame_num = 600
        self.latency = LatencyLogger(name="grab_behavior_detector",
                                     max_size=20_000,
                                     )
        self.offset = 0
        self.counter = 0

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        self.reshape_size = (11, 4)

        # reset the text file
        with open('/home/clewis/repos/realSpike/data/rb50_20250125_single_reach_grab.txt', 'w') as file_object:
            pass
        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        self.improv_logger.info("Detector stopping")
        self.latency.save()
        return 0

    def run_step(self):
        global GRAB_DETECTED
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            if self.frame_num == 850:
                # trial is over, next frame will be for next trial
                self.frame_num = 600
                if not GRAB_DETECTED:
                    with open('/home/clewis/repos/realSpike/data/rb50_20250125_single_reach_grab.txt', 'a') as f:
                        f.write(f"GRAB NOT DETECTED\n")
                    self.improv_logger.info(f"GRAB NOT DETECTED")
                GRAB_DETECTED = False
                self.offset += 1
                self.counter = 0
                return

            t = time.perf_counter_ns()
            if GRAB_DETECTED:
                # grab already detected for this trial
                # update frame num
                self.frame_num += 1
                return

            self.frame = np.frombuffer(self.client.client.get(data_id), np.uint8).reshape(*self.reshape_size)

            if (self.frame != 0).sum() >= 41:
                self.counter += 1
                if self.counter > 9:
                    GRAB_DETECTED = True
                    self.improv_logger.info(f"GRAB DETECTED: frame {self.frame_num}")
                    # output detection
                    with open('/home/clewis/repos/realSpike/data/rb50_20250125_single_reach_grab.txt', 'a') as f:
                        f.write(f"{self.frame_num}\n")

            # for every frame could send a zero or 1 to pattern generator, if 1 that means trigger
            store_id = str(os.getpid()) + str(uuid.uuid4())
            if GRAB_DETECTED:
                detected_value = 1
            else:
                detected_value = 0

            self.client.client.set(store_id, detected_value.to_bytes(), nx=True)
            self.q_out.put(store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.offset + self.frame_num, t2 - t)
            self.frame_num += 1
