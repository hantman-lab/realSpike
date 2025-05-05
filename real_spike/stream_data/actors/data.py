from improv.actor import ZmqActor
import numpy as np
import tifffile
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0

    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        file_path = "/home/clewis/repos/holo-nbs/rb26_20240111/raw_voltage_chunk.tif"
        # load the data
        data = tifffile.memmap(file_path) # (channels, time)
        # choose a window length
        self.window = 1000
        # initialize a chunk of data
        self.data = np.random.rand(512, 512)
        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")
        return 0

    def run_step(self):
        if self.frame_num == 10:
            return
        # new data
        self.data = np.random.rand(512, 512)
        data_id = self.client.put(self.data)
        try:
            self.q_out.put(data_id)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
