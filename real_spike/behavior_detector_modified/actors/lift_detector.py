from improv.actor import ZmqActor
import logging
import time
import numpy as np
import zmq
import os
import uuid

from real_spike.utils import BehaviorLogger, LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LiftDetector(ZmqActor):
    def __init__(self, *args, **kwargs):
        """Actor responsible for detecting lifts using a fixed bounding box."""
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "LiftDetector"
        self.trial_actions = set()

        # define loggers
        self.latency = LatencyLogger(
            name="lift_detector",
            max_size=50_000,
        )
        self.behavior_logger = BehaviorLogger("test-logger")

    def __str__(self):
        """Returns the name of the actor and the most recent frame."""
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        """
        Sets up the actor.

        Defines the bounding box region, sets up serial port to the NIDAQ for turning the laser on,
        initializes a behavior logger.
        """
        self.frame_num = None

        self.reshape_size = (290, 448)

        # TODO: update with the desired crop
        self.crop = [136, 155, 207, 220]
        #   self.crop = [165, 184, 208, 221]
        # self.crop = [182, 201, 208, 221]
        self.crop = [157, 177, 199, 212]

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
        self.behavior_logger.save()
        self.socket.close()
        self.latency.save()
        return 0

    def run_step(self):
        """
        Runs a single step of the actor.

        Unpacks the frame and frame number, crops the frame to the region defined by bounding box,
        and tries to detect lift.
        If lift is detected, will send signal to LaserTrigger actor to trigger the laser.
        """
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            t = time.perf_counter_ns()
            data = np.frombuffer(self.client.client.get(data_id), np.uint32)
            self.trial_num = int(data[-2])
            self.frame_num = int(data[-1])
            self.frame = data[:-2].reshape(*self.reshape_size)

            # action already taken
            if self.trial_num in self.trial_actions:
                self.improv_logger.info(
                    f"ACTION ALREADY TAKEN FOR TRIAL {self.trial_num}"
                )
                return

            if self.frame_num < 600:
                return

            if not self.frame.any():
                self.improv_logger.info(
                    f"BLANK FRAME, {self.trial_num}, {self.frame_num}"
                )

            # in the event that we do not detect lift
            if self.frame_num >= 900:
                self.behavior_logger.log(self.trial_num, "LIFT NOT DETECTED", None)
                self.improv_logger.info(
                    f"TRIAL {self.trial_num}, FRAME {self.frame_num}, LIFT NOT DETECTED"
                )
                self.socket.send_string("1")
                self.trial_actions.add(self.trial_num)
                return

            # y-dim comes first (height, width)
            frame = self.frame[
                self.crop[2] : self.crop[3], self.crop[0] : self.crop[1]
            ].copy()
            # need to set background pixels to 0
            frame[frame < 11] = 0

            # check number of non-zero pixels
            if (frame != 0).sum() >= 180:
                self.improv_logger.info(
                    f"LIFT DETECTED: TRIAL {self.trial_num}, FRAME {self.frame_num}"
                )
                # send signal to trigger laser
                p_id = str(os.getpid()) + str(uuid.uuid4())
                self.client.client.set(p_id, self.trial_num, nx=False)
                self.q_out.put(p_id)

                # tell frame grabber to stop grabbing
                self.socket.send_string("1")

                # output detection
                self.behavior_logger.log(self.trial_num, self.frame_num, self.frame)
                self.trial_actions.add(self.trial_num)

            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
