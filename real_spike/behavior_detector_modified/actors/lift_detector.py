from improv.actor import ZmqActor
import logging
import time
import serial
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
        self.trial_num = 0
        self.reshape_size = (290, 448)
        self.crop = [136, 155, 207, 220]
        self.behavior_logger = BehaviorLogger("test-logger")

        # serial port to send out laser signal
        # self.ser = serial.Serial("/dev/ttyACM0", 115200)

        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        self.improv_logger.info("Lift detector stopping")
        self.ser.close()
        self.latency.save()
        self.behavior_logger.save()
        return 0

    def _trigger_laser(self):
        self.ser.write(b"STIM 13 4 0 5000 10000 1\n")
        self.ser.flush()

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
            self.frame = data[:-1].reshape(*self.reshape_size)

            # will never see a lift before the pellet actually comes forward
            if self.frame_num <= 600:
                return

            if self.frame_num >= 849:
                if not LIFT_DETECTED:
                    self.behavior_logger.log(self.trial_num, "LIFT NOT DETECTED", None)
                    self.improv_logger.info("LIFT NOT DETECTED")
                LIFT_DETECTED = False
                self.trial_num += 1
                return

            # lift already detected for this trial
            if LIFT_DETECTED:
                return

            # y-dim comes first (height, width)
            frame = self.frame[self.crop[2] : self.crop[3], self.crop[0] : self.crop[1]]

            if (frame != 0).sum() >= 180:
                self.improv_logger.info(f"LIFT DETECTED: frame {self.frame_num}")
                self.improv_logger.info("SENDING LASER SIGNAL")
                # self._trigger_laser()
                # output detection
                self.behavior_logger.log(self.trial_num, self.frame_num, self.frame)
                LIFT_DETECTED = True
                self.trial_num += 1

            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
