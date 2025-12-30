from improv.actor import ZmqActor
import logging
import random
import time
import uuid
import numpy as np
import os


from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Model(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Model"

    def __str__(self):
        return f"Name: {self.name}"

    def setup(self):
        self.frame_num = 0
        self.data = None

        self.latency = LatencyLogger("model_acquisition")

        # number of channels to expect
        self.num_channels = 150
        self.sample_rate = 30_000
        self.num_samples = int(1 * self.sample_rate / 1_000)

        self.improv_logger.info("Completed setup for Model")

    def stop(self):
        self.improv_logger.info("Model stopping")
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
            self.data = np.frombuffer(
                self.client.client.get(data_id), np.float64
            ).reshape(self.num_channels, self.num_samples)

            # generate a random pattern to stimulate (29 options)
            pattern_id = random.randint(0, 28)
            p_store_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(p_store_id, pattern_id.to_bytes(), nx=False)
            self.q_out.put(p_store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1
