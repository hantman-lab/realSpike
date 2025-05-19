from improv.actor import ZmqActor
import logging
import zmq
import time
from .latency import Latency

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

        self.latency = Latency("visual")

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://127.0.0.1:5557")

        self.improv_logger.info("Completed setup for Visual")

    def stop(self):
        self.improv_logger.info("Visual stopping")
        self.socket.close()
        self.latency.save()
        return 0

    def run_step(self):
        frame = None
        t = time.perf_counter_ns()
        try:
            frame = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if frame is not None:
            self.done = False
            self.frame = self.client.get(frame)

            self.socket.send(self.frame.ravel())
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

