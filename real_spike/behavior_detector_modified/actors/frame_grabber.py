from improv.actor import ZmqActor
import logging
import time
import uuid
import os
import numpy as np
import zmq

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CUE_DETECTED = False


class CameraGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        """Grabs the most recent frame off of the bias computer."""
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CameraGenerator"
        self.latency = LatencyLogger(
            name="generator_camera",
            max_size=20_000,
        )

    def __str__(self):
        """Returns the actor name and the most recent data."""
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        """Sets up the actor. Makes a ZMQ connection to the bias computer for making frame requests."""
        # every time we get a new cue, want to increment trial number
        self.trial_num = -1
        self.frame_num = 0
        self.fetch_counter = 0

        # open REQ/REP socket to bias computer over netgear switch
        ip_address = "192.168.0.103"
        # ip_address = "localhost"
        port = 4148

        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{ip_address}:{port}")

        self.improv_logger.info("Completed setup for Camera Generator")

    def stop(self):
        """Stops the actor and cleans up resources."""
        self.improv_logger.info("Camera generator stopping")
        self.latency.save()
        self.socket.close()
        return 0

    def run_step(self):
        """
        Run a single step of the actor.

        When cue signal is received, fetches 118 frames off the camera to try detecting lift on.
        """
        global CUE_DETECTED
        t = time.perf_counter()

        # cue not detected, try to get it
        if not CUE_DETECTED:
            data_id = None
            try:
                # get data_id from queue in
                data_id = self.q_in.get(timeout=0.05)
            except Exception as e:
                pass

            # did get a cue
            if data_id is not None:
                self.trial_num += 1
                self.improv_logger.info(
                    f"RECEIVED CUE TRIAL {self.trial_num}, START FETCHING FRAMES"
                )
                CUE_DETECTED = True
            # no cue yet
            else:
                return

        # at end of fetch
        if self.fetch_counter >= 118:
            # reset cue detector
            CUE_DETECTED = False
            # reset frame num
            self.fetch_counter = 0
            return
        else:
            # fetch a frame
            self.improv_logger.info("FETCHING FRAME")
            self.socket.send_string("fetch()")
            # get reply
            data = self.socket.recv()

            data_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(data_id, data, nx=False)
            try:
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
                self.frame_num += 1
                self.fetch_counter += 1
            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
