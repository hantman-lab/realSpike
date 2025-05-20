from improv.actor import ZmqActor
import tifffile
import logging
import time

from real_spike.utils.latency import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0
        self.latency = LatencyLogger(name="generator",
                                     columns=["frame number", "total latency", "data fetch", "store put", "queue put"])

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
        self.latency.save()
        return 0

    def run_step(self):
        if self.frame_num == ((self.data.shape[1] - 1) / self.window) - 1:
            return

        # new data, send 5ms
        l_time = int(self.frame_num * self.window)
        r_time = int((self.frame_num * self.window) + self.window)
        t = time.perf_counter_ns()
        data = self.data[:, l_time:r_time]
        d_fetch = time.perf_counter_ns() - t
        t2 = time.perf_counter_ns()
        data_id = self.client.put(data)
        store_put = time.perf_counter_ns() - t2

        try:
            t2 = time.perf_counter_ns()
            self.q_out.put(data_id)
            q_put = time.perf_counter_ns() - t2
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, [t2-t, d_fetch, store_put, q_put])
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
