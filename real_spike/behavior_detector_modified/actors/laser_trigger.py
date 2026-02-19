from improv.actor import ZmqActor
import logging
import time
import serial
import numpy as np
import pandas as pd
import zmq

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
        # self.ser = serial.Serial("/dev/ttyACM0", 115200)

        # load the experiment conditions
        if EXPERIMENT_TYPE == "holography":
            self.experiment_conditions = np.load(
                "/home/clewis/repos/realSpike/scripts/behavior_detector/preset_patterns.npy"
            )
        else:
            self.experiment_conditions = pd.read_pickle(
                "/home/clewis/repos/realSpike/scripts/behavior_detector/preset_fiber.pkl"
            )

        # open SUB socket for odd trials to get laser signal right after cue
        ip_address = "localhost"
        port = 5553
        context = zmq.Context()
        self.laser_socket = context.socket(zmq.SUB)
        self.laser_socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.laser_socket.connect(f"tcp://{ip_address}:{port}")

        self.improv_logger.info("Completed setup for laser trigger")

    def stop(self):
        """Stops the actor and cleans up resources."""
        self.improv_logger.info("Laser trigger stopping")
        self.laser_socket.close()
        # clean up resources
        #self.ser.close()
        return 0

    # TODO: delete this method when done
    def _fake_trigger(self):
        # get the current pattern
        pattern = self.experiment_conditions[self.trial_num]
        # if the trial is not a control trial, trigger the laser once during the behavior and once after
        if pattern.any():
            if self.trial_num % 2 == 0:
                self.improv_logger.info("LASER SIGNAL SENT")
            else:
                self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
        else:
            self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNAL SENT")

    def _trigger_laser_holography(self):
        """Triggers the laser, writing out the appropriate command."""
        # get the current pattern
        pattern = self.experiment_conditions[self.trial_num]

        # if the trial is not a control trial, trigger the laser once during the behavior and once after
        if pattern.any():
            self.ser.write(b"STIM 13 4 0 5000 10000 1\n")
            if self.trial_num % 2 == 0:
                self.improv_logger.info("LASER SIGNAL SENT")
            else:
                self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
            self.ser.flush()
        else:
            self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNAL SENT")

    def _trigger_laser_fiber(self):
            # get the current condition
            r = self.experiment_conditions.loc[
                self.experiment_conditions["trial_num"] == self.trial_num
            ]
            condition = r["condition_num"].iat[0]
            cmd = r["command"].iat[0].encode()
            # check to see if it is control trials or not
            if condition > 0:
                self.ser.write(cmd)
                if self.trial_num % 2 == 0:
                    self.improv_logger.info("LASER SIGNAL SENT")
                else:
                    self.improv_logger.info("NON-BEHAVIOR LASER SIGNAL SENT")
                self.ser.flush()
            else:
                self.improv_logger.info("CONTROL TRIAL, NO LASER SIGNAL SENT")

    def run_step(self):
        """
        Runs a single step of the actor.

        Triggers the laser.
        """
        if self.trial_num % 2 == 1:
            data_id = None

            try:
                # get data_id from queue in
                data_id = self.q_in.get(timeout=0.05)
            except Exception as e:
                pass

            # trigger the laser
            if data_id is not None:
                self.trial_num += 1
                self._fake_trigger()

                # if EXPERIMENT_TYPE == "holography":
                #     self._trigger_laser_holography()
                # else:
                #     self._trigger_laser_fiber()
        else:
            try:
                buff = self.laser_socket.recv(zmq.NOBLOCK)
            except zmq.Again:
                buff = None

            # stop grabbing frames
            if buff is not None:
                self.trial_num += 1
                self._fake_trigger()

                # if EXPERIMENT_TYPE == "holography":
                #     self._trigger_laser_holography()
                # else:
                #     self._trigger_laser_fiber()
