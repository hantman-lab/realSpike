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
        self.frame_num = 500
        self.latency = LatencyLogger(name="lift_behavior_detector",
                                     max_size=20_000,
                                     )
        self.offset = 0
        self.all_magnitudes = list()
        self.trial_magnitudes = list()

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        self.reshape_size = (120, 139)

        # reset the text file
        with open('/data/rb50_20250125_single_reach.txt', 'w') as file_object:
            pass
        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        self.improv_logger.info("Detector stopping")
        self.latency.save()
        # save the magnitude traces to plot
        with open("/home/clewis/repos/realSpike/data/rb50_20250125_single_reach_mags.pk1", "wb") as f:
            pickle.dump(self.all_magnitudes, f)
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
            if self.frame_num == 799:
                # trial is over, next frame will be for next trial
                self.frame_num = 500
                if not LIFT_DETECTED:
                    with open('/data/rb50_20250125_single_reach.txt', 'a') as f:
                        f.write(f"LIFT NOT DETECTED\n")
                    self.improv_logger.info(f"LIFT NOT DETECTED")
                LIFT_DETECTED = False
                self.offset += 1
                self.all_magnitudes.append(self.trial_magnitudes)
                self.trial_magnitudes = list()
                return

            t = time.perf_counter_ns()
            if LIFT_DETECTED:
                # lift already detected for this trial
                # update frame num
                self.frame_num += 1
                return

            self.frame = np.frombuffer(self.client.client.get(data_id), np.uint8).reshape(*self.reshape_size)

            if self.frame_num == 500:
                # first frame for ref
                self.init_frame = self.frame
            else:
                flow = cv2.calcOpticalFlowFarneback(
                    self.init_frame, self.frame, None,
                    pyr_scale=0.5, levels=2, winsize=12,
                    iterations=2, poly_n=3, poly_sigma=1.1, flags=0
                )

                mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])

                fx, fy = flow[..., 0], flow[..., 1]
                angle = np.arctan2(fy, fx) * 180 / np.pi

                mask = (angle > 15) & (angle < 45)

                avg_magnitude = np.mean(mag[mask])
                self.trial_magnitudes.append(avg_magnitude)

                if avg_magnitude > 3.5:
                    LIFT_DETECTED = True
                    self.improv_logger.info(f"LIFT DETECTED: frame {self.frame_num - 500}")
                    # output detection
                    with open('/data/rb50_20250125_single_reach.txt', 'a') as f:
                        f.write(f"{self.frame_num - 500}\n")

            # for every frame could send a zero or 1 to pattern generator, if 1 that means trigger
            store_id = str(os.getpid()) + str(uuid.uuid4())
            if LIFT_DETECTED:
                detected_value = 1
            else:
                detected_value = 0

            self.client.client.set(store_id, detected_value.to_bytes(), nx=True)
            self.q_out.put(store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.offset + self.frame_num, t2 - t)
            self.frame_num += 1

