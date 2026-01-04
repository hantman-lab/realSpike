from improv.actor import ZmqActor
import logging
import zmq
import time

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Visual(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Visual"

    def setup(self):
        self.frame_num = 0
        self.data = None

        self.latency = LatencyLogger("acquisition_visual")

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        address = "localhost"
        port = 5557
        self.socket.bind(f"tcp://{address}:{port}")

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
            data_id = self.q_in.get(timeout=0.05)
        except Exception:
            pass

        if data_id is not None:
            # no need to unpack the bytes
            self.data = self.client.client.get(data_id)

            self.socket.send(self.data)
            t2 = time.perf_counter_ns()
            self.latency.add(None, self.frame_num, t2 - t)
            self.frame_num += 1
