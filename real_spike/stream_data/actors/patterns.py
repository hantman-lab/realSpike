from improv.actor import ZmqActor
import logging
import time
import numpy as np
import matplotlib.pyplot as plt

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PATTERN_PATH = "/home/clewis/repos/realSpike/real_spike/utils/patterns.npy"

class PatternGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in kwargs:
            self.name = kwargs["name"]

    def setup(self):
        if not hasattr(self, "name"):
            self.name = "Pattern Generator"
        self.frame_num = 27
        # load the patterns during setup
        self.patterns = np.load(PATTERN_PATH)

        self.latency = LatencyLogger("pattern-generator")

        self.improv_logger.info("Completed setup for Pattern Generator")

    def stop(self):
        self.improv_logger.info("Pattern generation stopping")
        self.latency.save()
        return 0

    def run_step(self):
        # want to randomly select a pattern to generate and show
        data_id = None
        t = time.perf_counter_ns()
        try:
            data_id = self.q_in.get(timeout=0.05)[1]
        except Exception as e:
            pass

        if data_id is not None:
            self.done = False
            pattern_id = int.from_bytes(self.client.client.get(data_id))
            # get the pattern
            current_pattern = self.patterns[pattern_id]

            if self.frame_num % 100 == 0:
                self.improv_logger.info(f"Pattern for frame {self.frame_num}, "
                                        f"Pattern selected: {pattern_id},"
                                        f" Pattern: {current_pattern}")

            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

            self.client.client.delete(data_id)


