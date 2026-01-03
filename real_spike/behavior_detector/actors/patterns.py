from improv.actor import ZmqActor
import logging
import time
import numpy as np
import zmq
import random

from real_spike.utils import LatencyLogger, TimingLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Pattern(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Pattern"

    def __str__(self):
        return f"Name: {self.name}"

    def setup(self):
        self.frame_num = None
        self.trial_num = None

        self.latency = LatencyLogger("pattern_generator_behavior_detector")
        self.pattern_logger = TimingLogger("test-improv")

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        address = "localhost"
        port = 5559
        self.socket.bind(f"tcp://{address}:{port}")

        self.patterns = np.load(
            "/home/clewis/repos/realSpike/real_spike/utils/fixed_patterns.npy"
        )

        self.improv_logger.info("Completed setup for Pattern Generator")

    def stop(self):
        self.improv_logger.info("Pattern Generator stopping")
        self.socket.close()
        self.latency.save()
        self.pattern_logger.save()
        return 0

    def run_step(self):
        data_id = None
        t = time.perf_counter_ns()
        try:
            data_id = self.q_in.get(timeout=0.05)
        except Exception:
            pass

        if data_id is not None:
            data = np.frombuffer(self.client.client.get(data_id), np.uint32)
            self.trial_num = int(data[0])
            self.frame_num = int(data[1])
            detected = int(data[2])
            # get the pattern
            if detected == 1:
                # randomly select one of the 5 pattern options
                pattern_id = random.randint(0, 4)
                pattern = self.patterns[pattern_id]
                # send the pattern
                self.improv_logger.info("SENDING PATTERN")
                self.socket.send(pattern.ravel().astype(np.float64).tobytes())
                self.pattern_logger.log(
                    self.trial_num, self.frame_num, time.time(), pattern
                )
            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
