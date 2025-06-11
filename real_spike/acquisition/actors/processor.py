from improv.actor import ZmqActor
import logging
import time
import random
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Processor(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in kwargs:
            self.name = kwargs["name"]

    def setup(self):
        if not hasattr(self, "name"):
            self.name = "Processor"
        self.frame = None
        self.frame_num = 1
        self.data = None

        # self.latency = LatencyLogger("processor")
        self.improv_logger.info("Completed setup for Processor")

    def stop(self):
        self.improv_logger.info("Processor stopping")
        self.improv_logger.info(f"Processor processed {self.frame_num} frames")
        # self.latency.save()
        return 0

    def run_step(self):
        if self.frame_num < 10:
            self.improv_logger.info("Processor step")
        else:
            return
        self.frame_num += 1