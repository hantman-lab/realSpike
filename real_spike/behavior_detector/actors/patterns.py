from improv.actor import ZmqActor
import logging
import time
import numpy as np
import zmq

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PATTERN_PATH = "/home/clewis/repos/realSpike/real_spike/utils/patterns.npy"

# flag to keep track of pattern sent on a given trial
SENT_PATTERN = False

class PatternGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in kwargs:
            self.name = kwargs["name"]

    def setup(self):
        if not hasattr(self, "name"):
            self.name = "Pattern Generator"
        self.frame_num = 500
        # load the patterns during setup
        self.patterns = np.load(PATTERN_PATH)

        # set up zmq connection to psychopy file
        context = zmq.Context()
        self.socket = context.socket(zmq.PUSH)
        address = "0.0.0.0"
        port = 5559
        self.socket.bind(f"tcp://{address}:{port}")

        self.latency = LatencyLogger("pattern_behavior_detector")

        self.improv_logger.info("Completed setup for Pattern Generator")

    def stop(self):
        self.improv_logger.info("Pattern generation stopping")
        self.latency.save()
        self.socket.close()
        return 0

    def run_step(self):
        global SENT_PATTERN
        if SENT_PATTERN:
            # already sent pattern for this trial, do not send again
            # need to think of a way to pass this around
            return
        # want to randomly select a pattern to generate and show
        data_id = None
        t = time.perf_counter_ns()
        try:
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            lift_detected = int.from_bytes(self.client.client.get(data_id))
            # get the pattern
            if lift_detected:
                pattern_id = random.randint(0, 28)
                current_pattern = self.patterns[pattern_id]
                # send the pattern
                self.socket.send(current_pattern.ravel().tobytes())

            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

            self.client.client.delete(data_id)