from improv.actor import ZmqActor
import logging
import random
import time
import uuid
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Model(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in kwargs:
            self.name = kwargs["name"]

    def setup(self):
        if not hasattr(self, "name"):
            self.name = "Model"
        self.frame_num = 27
        self.frame = None

        self.latency = LatencyLogger("model_acquisition")

        # number of channels to expect
        self.num_channels = 150

        self.improv_logger.info("Completed setup for Model")

    def stop(self):
        self.improv_logger.info(f"Model stopping")
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
            self.done = False
            self.frame = np.frombuffer(self.client.client.get(data_id), np.float64).reshape(self.num_channels, 150)

            # generate a random pattern to stimulate (29 options)
            pattern_id = random.randint(0, 28)
            p_store_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(p_store_id, pattern_id.to_bytes(), nx=True)
            self.q_out.put(p_store_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

            # delete data from store
            # self.client.client.delete(data_id)

