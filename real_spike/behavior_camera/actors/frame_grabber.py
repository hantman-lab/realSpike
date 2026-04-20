from improv.actor import ZmqActor
import logging
import time
import uuid
import os
import zmq
import numpy as np

import pyflycap2.interface as fc2
from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CameraGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        """Grabs the most recent frame off of the bias computer."""
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CameraGenerator"

    def __str__(self):
        """Returns the actor name and the most recent data."""
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        """Sets up the actor. Makes a ZMQ connection to the bias computer for making frame requests."""
        # every time we get a new cue, want to increment trial number
        self.frame_num = 0

        # connect to camera
        self.camera = fc2.Camera(index=0, context_type="IIDC")
        self.camera.connect()
        # configure camera with proper settings
        self._configure_camera()

        # open PUB/SUB socket with lift detector actor to get back when lift detected
        ip_address = "localhost"
        port = 4143

        context = zmq.Context()
        self.stop_socket = context.socket(zmq.SUB)
        self.stop_socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.stop_socket.connect(f"tcp://{ip_address}:{port}")

        self.improv_logger.info("Completed setup for Camera Generator")

    def stop(self):
        """Stops the actor and cleans up resources."""
        self.improv_logger.info("Camera generator stopping")
        self.camera.disconnect()
        self.stop_socket.close()
        return 0

    def _configure_camera(self):
        # config camera
        pass

    def _write_video(self):
        # will need to do all of the video writing
        # will also need to output frames to lift detector, only frames 550 - 900
        data_id = str(os.getpid()) + str(uuid.uuid4())
        data = np.random.rand(512, 512).ravel().tobytes()

        self.client.client.set(data_id, data, nx=False)
        try:
            self.q_out.put(data_id)
            self.client.client.expire(data_id, 25)
        except Exception as e:
            self.improv_logger.error(f"FrameGrabber Exception: {e}")
        pass

    def run_step(self):
        """
        Run a single step of the actor.

        When cue signal is received, fetches 118 frames off the camera to try detecting lift on.
        """
        # cue not detected, try to get it
        data_id = None
        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        # did get a cue
        if data_id is not None:
            self.trial_num = self.client.client.get(data_id)
            self.improv_logger.info(
                f"RECEIVED CUE TRIAL {self.trial_num}, START FETCHING FRAMES"
            )
            self._write_video()
