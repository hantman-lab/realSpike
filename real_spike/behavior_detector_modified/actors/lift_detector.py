from improv.actor import ZmqActor
import logging
import time
import serial
import numpy as np
import pandas as pd

from real_spike.utils import BehaviorLogger, LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LIFT_DETECTED = False


class LiftDetector(ZmqActor):
    def __init__(self, *args, **kwargs):
        """Actor responsible for detecting lifts using a fixed bounding box."""
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "LiftDetector"
        self.latency = LatencyLogger(
            name="lift_detector",
            max_size=50_000,
        )

    def __str__(self):
        """Returns the name of the actor and the most recent frame."""
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        """
        Sets up the actor.

        Defines the bounding box region, sets up serial port to the NIDAQ for turning the laser on,
        initializes a behavior logger.
        """
        self.trial_num = 0
        self.frame_num = None
        self.reshape_size = (290, 448)
        self.crop = [136, 155, 207, 220]
        self.crop = [170, 189, 207, 220]
        self.behavior_logger = BehaviorLogger("test-logger-holography")

        # serial port to send out laser signal
        self.ser = serial.Serial("/dev/ttyACM0", 115200)

        self.experiment_conditions = np.load(
            "/home/clewis/repos/realSpike/scripts/behavior_detector/preset_patterns.npy"
        )

        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        """Stops the actor and cleans up resources."""
        self.improv_logger.info("Lift detector stopping")
        self.behavior_logger.save()
        self.ser.close()
        self.latency.save()
        return 0

    def _trigger_laser(self):
        """Triggers the laser, writing out the appropriate command."""
        # get the current pattern
        pattern = self.experiment_conditions[self.trial_num]

        # if the trial is not a control trial, trigger the laser once during the behavior and once after
        if pattern.any():
            self.ser.write(b"STIM 13 4 0 5000 10000 1\n")
            self.improv_logger.info("LASER SIGNAL SENT")
            self.ser.flush()
            time.sleep(12)
            self.ser.write(b"STIM 13 4 0 5000 10000 1\n")
            self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
            self.ser.flush()
        else:
            self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNALS SENT")

    def run_step(self):
        """
        Runs a single step of the actor.

        Unpacks the frame and frame number, crops the frame to the region defined by bounding box,
        and tries to detect lift.
        If lift is detected, will trigger the laser.
        """
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

            if self.frame_num == 852:
                if not LIFT_DETECTED:
                    self.behavior_logger.log(self.trial_num, "LIFT NOT DETECTED", None)
                    self.improv_logger.info(
                        f"TRIAL {self.trial_num}, FRAME {self.frame_num}, LIFT NOT DETECTED"
                    )
                LIFT_DETECTED = False
                self.trial_num += 1
                self.frame_num = -1
                return

            # lift already detected for this trial
            if LIFT_DETECTED:
                return

            # y-dim comes first (height, width)
            frame = self.frame[self.crop[2] : self.crop[3], self.crop[0] : self.crop[1]]

            if (frame != 0).sum() >= 180:
                self.improv_logger.info(f"LIFT DETECTED: frame {self.frame_num}")
                self._trigger_laser()
                # output detection
                self.behavior_logger.log(self.trial_num, self.frame_num, self.frame)
                LIFT_DETECTED = True
                self.trial_num += 1

            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
