from improv.actor import ZmqActor
import logging
import time
import serial
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

EXPERIMENT_TYPE = "holography"


class LaserTrigger(ZmqActor):
    def __init__(self, *args, **kwargs):
        """Actor responsible for triggering the laser."""
        super().__init__(*args, **kwargs)
        self.name = "LaserTrigger"

    def __str__(self):
        """Returns the name of the actor and the most recent frame."""
        return f"Name: {self.name}, Experiment type: {EXPERIMENT_TYPE}"

    def setup(self):
        """
        Sets up the actor.

        Open the serial port for sending out laser signals. Load the experiment-specific pre-defined trial conditions.
        Patterns for holography and commands for fiber.
        """
        self.trial_num = -1

        # serial port to send out laser signal
        self.ser = serial.Serial("/dev/ttyACM0", 115200)

        # load the experiment conditions
        if EXPERIMENT_TYPE == "holography":
            self.experiment_conditions = np.load(
                "/home/clewis/repos/realSpike/scripts/behavior_detector/preset_patterns.npy"
            )
        else:
            self.experiment_conditions = pd.read_pickle(
                "/home/clewis/repos/realSpike/scripts/behavior_detector/preset_fiber.pkl"
            )

        self.improv_logger.info("Completed setup for laser trigger")

    def stop(self):
        """Stops the actor and cleans up resources."""
        self.improv_logger.info("Laser trigger stopping")
        # clean up resources
        self.ser.close()
        return 0

    # TODO: delete this method when done
    def _fake_trigger(self):
        # get the current pattern
        pattern = self.experiment_conditions[self.trial_num]
        # if the trial is not a control trial, trigger the laser once during the behavior and once after
        if pattern.any():
            self.improv_logger.info("LASER SIGNAL SENT")
            time.sleep(10)
            self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
            self.improv_logger.info(" ")
        else:
            self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNALS SENT")
            self.improv_logger.info(" ")

    def _trigger_laser(self):
        """Triggers the laser, writing out the appropriate command."""
        if EXPERIMENT_TYPE == "holography":
            # get the current pattern
            pattern = self.experiment_conditions[self.trial_num]

            # if the trial is not a control trial, trigger the laser once during the behavior and once after
            if pattern.any():
                self.ser.write(b"STIM 13 4 0 5000 10000 1\n")
                self.improv_logger.info("LASER SIGNAL SENT")
                self.ser.flush()
                time.sleep(10)
                self.ser.write(b"STIM 13 4 0 5000 10000 1\n")
                self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
                self.improv_logger.info(" ")
                self.ser.flush()
            else:
                self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNALS SENT")
                self.improv_logger.info(" ")
        else:  # experiment is fiber
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
                self.improv_logger.info(" ")
                self.ser.flush()
            else:
                self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNALS SENT")
                self.improv_logger.info(" ")

    def run_step(self):
        """
        Runs a single step of the actor.

        Triggers the laser.
        """
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        # trigger the laser
        if data_id is not None:
            self.trial_num += 1
            # self._fake_trigger()
            self._trigger_laser()
