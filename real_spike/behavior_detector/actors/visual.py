from improv.actor import ZmqActor
import logging
import zmq
import time
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Visual(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in kwargs:
            self.name = kwargs["name"]

    def setup(self):
        if not hasattr(self, "name"):
            self.name = "Visual"
        self.frame_num = 500
        self.frame = None

        self.reshape_size = (133, 139)

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://127.0.0.1:5557")

        self.improv_logger.info("Completed setup for Visual")

    def stop(self):
        self.improv_logger.info(f"Visual stopping: {self.frame_num} frames seen")
        self.socket.close()
        return 0

    def run_step(self):
        data_id = None
        try:
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            # no need to convert in and out of bytes here
            self.frame = self.client.client.get(data_id)
            self.socket.send(self.frame)
            self.frame_num += 1