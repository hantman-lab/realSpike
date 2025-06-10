from improv.actor import ZmqActor
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils.sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Processor(ZmqActor):
    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Processor"

    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        self.improv_logger.info('Completed setup for Processor')

    def stop(self):
        self.improv_logger.info("Stopping Processor")
        return 0

    def runStep(self):
        self.improv_logger.info("run run run")