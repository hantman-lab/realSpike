from improv.actor import ZmqActor
import fastplotlib as fpl
import numpy as np
import logging

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
        self.improv_logger.info("Completed setup for Processor")

    def stop(self):
        self.improv_logger.info("Processor stopping")
        return 0

    def run_step(self):
        """Gets from the input queue and calculates the average.

        Receives an ObjectID, references data in the store using that
        ObjectID, calculates the average of that data, and finally prints
        to stdout.
        """
        frame = None
        try:
            frame = self.q_in.get(timeout=0.05)
        except Exception as e:
            logger.error(f"{self.name} could not get frame! At {self.frame_num}: {e}")
            pass

        if frame is not None and self.frame_num is not None:
            self.done = False
            self.frame = self.client.get(frame)
            self.frame_num += 1