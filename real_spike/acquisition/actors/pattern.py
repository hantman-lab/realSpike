from improv.actor import ZmqActor
import logging
import time
import numpy as np
import zmq


from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Pattern(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Pattern"
    
    def __str__(self):
        return f"Name: {self.name}"

    def setup(self):
        self.frame_num = 0
        self.p_id = None

        self.latency = LatencyLogger("pattern_generator_acquisition")
        
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        address = "localhost"
        port = 5559
        self.socket.bind(f"tcp://{address}:{port}")

       
        self.patterns = np.load("/home/clewis/repos/realSpike/real_spike/utils/patterns.npy")

        self.improv_logger.info("Completed setup for Pattern Generator")

    def stop(self):
        self.improv_logger.info(f"Pattern Generator stopping")
        self.socket.close()
        self.latency.save()
        return 0

    def run_step(self):
        data_id = None
        t = time.perf_counter_ns()
        try:
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            self.p_id = np.frombuffer(self.client.client.get(data_id), np.float64)

            # reconstruct pattern
            pattern = self.patterns[self.p_id]
            self.socket.send(pattern.ravel())
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1
