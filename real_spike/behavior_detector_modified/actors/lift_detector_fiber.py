import pandas as pd
from improv.actor import ZmqActor
import logging
import time
import serial
import numpy as np
import zmq

from real_spike.utils import BehaviorLogger, LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LiftDetector(ZmqActor):
    def __init__(self, *args, **kwargs):
        """Detects lift and sends out appropriate laser signal for doing fiber experiments."""
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "LiftDetector"
        self.LIFT_DETECTED = False

        # define loggers
        self.latency = LatencyLogger(
            name="lift_detector_fiber",
            max_size=50_000,
        )
        self.behavior_logger = BehaviorLogger("test-logger-fiber")

    def __str__(self):
        """Returns the name and most recent data."""
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        """Sets up the actor."""
        self.trial_num = 0
        self.frame_num = None

        self.reshape_size = (290, 448)

        # TODO: update with desired crop
        self.crop = [136, 155, 207, 220]
        self.crop = [170, 189, 207, 220]

        # serial port to send out laser signal
        self.ser = serial.Serial("/dev/ttyACM0", 115200)

        # load the experiment conditions
        self.experiment_conditions = pd.read_pickle(
            "/home/clewis/repos/realSpike/scripts/behavior_detector/preset_fiber.pkl"
        )

        # connect to frame grabber to send stop signal
        ip_address = "localhost"
        port_number = 4143

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind(f"tcp://{ip_address}:{port_number}")

        self.improv_logger.info("Completed setup for behavior detector")

    def stop(self):
        """Stops the actor and cleans up resources."""
        self.improv_logger.info("Lift detector stopping")
        self.ser.close()
        self.socket.close()
        self.latency.save()
        self.behavior_logger.save()
        return 0

    def _trigger_laser(self):
        """Triggers the laser with the appropriate command."""
        # get the current condition
        r = self.experiment_conditions.loc[
            self.experiment_conditions["trial_num"] == self.trial_num
        ]
        condition = r["condition_num"].iat[0]
        cmd = r["command"].iat[0].encode()
        # check to see if it is control trials or not
        if condition > 0:
            self.ser.write(cmd)
            self.improv_logger.info("LASER SIGNAL SENT")
            self.ser.flush()
            # sleep for 12 seconds and then stim again w/ no behavior
            time.sleep(10)
            self.ser.write(cmd)
            self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
            self.ser.flush()
        else:
            self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNALS SENT")

    def run_step(self):
        """Runs one step of the lift detector."""
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

            if not self.frame.any():
                self.improv_logger.info(f"BLANK FRAME, {self.frame_num}")

            # will never see a lift before the pellet actually comes forward
            if self.frame_num <= 600:
                return

            if self.frame_num == 852:
                if not self.LIFT_DETECTED:
                    self.behavior_logger.log(self.trial_num, "LIFT NOT DETECTED", None)
                    self.improv_logger.info(
                        f"TRIAL {self.trial_num}, FRAME {self.frame_num}, LIFT NOT DETECTED"
                    )
                self.LIFT_DETECTED = False
                self.trial_num += 1
                self.frame_num = -1
                return

            # lift already detected for this trial
            if self.LIFT_DETECTED:
                self.improv_logger.info(
                    f"LIFT ALREADY DETECTED, TRIAL {self.trial_num}"
                )
                return

            # y-dim comes first (height, width)
            frame = self.frame[self.crop[2] : self.crop[3], self.crop[0] : self.crop[1]]

            if (frame != 0).sum() >= 180:
                self.improv_logger.info(f"LIFT DETECTED: frame {self.frame_num}")
                # tell frame grabber to stop grabbing
                self.socket.send_string("1")
                self._trigger_laser()
                # output detection
                self.behavior_logger.log(self.trial_num, self.frame_num, self.frame)
                self.LIFT_DETECTED = True
                self.trial_num += 1

            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
