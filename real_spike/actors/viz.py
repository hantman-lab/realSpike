from improv.actor import Actor
import logging;
from queue import Empty

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Visualizer(Actor):
    """Get data from acquisition actor and send to jupyterlab for visualization via fastplotlib"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self):
        self.name = "Visualizer"

        logger.info("Completed setup for Visualizer")

    def stop(self):
        logger.info("Visualization stopping")
        return 0

    def runStep(self):
        """Gets data from queue, sends memoryview so zmq subscriber can get the buffer and update the plot"""
        data = None

        try:
            data = self.q_in.get(timeout=0.05)
        except Empty:
            pass
        except:
            logger.error("Could not get data!")

        if data is not None:
            pass
