from improv.actor import ZmqActor
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

        # specify step size, send 5 ms of data at a time
        self.sample_rate = 30_000
        # 5ms = 1 sec of data (30_000 time points) / 1_000 * 5
        self.window = 5 * self.sample_rate / 1_000


    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        file_path = "/home/clewis/repos/holo-nbs/rb26_20240111/raw_voltage_chunk.tif"
        # load the data
        self.data = tifffile.memmap(file_path) # (channels, time)

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")
        return 0

    def run_step(self):
        if self.frame_num == 100:
            return
        if self.frame_num == ((self.data.shape[1] - 1) / self.window) - 1:
            return
        # new data, send 5ms
        l_time = int(self.frame_num * self.window)
        r_time = int((self.frame_num * self.window) + self.window)
        data = self.data[:, l_time:r_time]
        data_id = self.client.put(data)
        try:
            self.q_out.put(data_id)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
