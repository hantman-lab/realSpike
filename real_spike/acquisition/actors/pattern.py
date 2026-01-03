from improv.actor import ZmqActor
import logging
import time
import numpy as np
import zmq

from real_spike.utils import LatencyLogger, TimingLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TRIAL_NO = 0


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
        self.pattern_logger = TimingLogger("test-improv")

        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        address = "localhost"
        port = 5559
        self.socket.bind(f"tcp://{address}:{port}")

        self.patterns = np.load(
            "/home/clewis/repos/realSpike/real_spike/utils/patterns.npy"
        )

        self.improv_logger.info("Completed setup for Pattern Generator")

    def stop(self):
        self.improv_logger.info("Pattern Generator stopping")
        self.socket.close()
        self.latency.save()
        self.pattern_logger.save()
        return 0

    def run_step(self):
        global TRIAL_NO
        data_id = None
        t = time.perf_counter_ns()
        try:
            data_id = self.q_in.get(timeout=0.05)
        except Exception:
            pass

        if data_id is not None:
            self.p_id = int.from_bytes(self.client.client.get(data_id))

            # reconstruct pattern
            pattern = self.patterns[self.p_id]
            # for now, only send a pattern every 100 frames
            if self.frame_num % 500 == 0:
                # TODO: in the future, would only get a pattern when something is causing stim to trigger would
                #  likely be once per trial stim would need to think of something else if it was multi-stim per trial
                self.socket.send(pattern.ravel().tobytes())
                self.pattern_logger.log(TRIAL_NO, self.frame_num, time.time(), pattern)
                TRIAL_NO += 1
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1
