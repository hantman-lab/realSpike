from improv.actor import ZmqActor
import logging
import zmq
import time
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger

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
        self.frame_num = 27
        self.frame = None

        self.latency = LatencyLogger("visual")

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://127.0.0.1:5557")

        self.improv_logger.info("Completed setup for Visual")

    def stop(self):
        self.improv_logger.info(f"Visual stopping: {self.frame_num} frames seen")
        self.socket.close()
        self.latency.save()
        return 0

    def run_step(self):
        data_id = None
        t = time.perf_counter_ns()
        try:
            data_id = self.q_in.get(timeout=0.05)[0]
        except Exception as e:
            pass

        if data_id is not None:
            self.done = False
            self.frame = np.frombuffer(self.client.client.get(data_id)).reshape(384, 150)

            self.socket.send(self.frame.ravel())
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

            # delete data from store
            self.client.client.delete(data_id)

