import logging
import time
import random
import uuid
import numpy as np

from real_spike.utils import LatencyLogger, butter_filter, get_spike_events
from improv.actor import ZmqActor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Processor(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Processor"

    def setup(self):
        self.data = None
        self.frame_num = 0

        # initialize median with the first 100 ms of data
        self.median = None
        self.median_data = list()

        self.num_channels = 150
        self.sample_rate = 30_000
        self.window = int(1 * self.sample_rate / 1_000)

        self.latency = LatencyLogger("processor_stream_disk")
        self.improv_logger.info("Completed setup for Processor")

    def stop(self):
        self.improv_logger.info("Processor stopping")
        self.improv_logger.info(f"Processor processed {self.frame_num} frames")
        self.latency.save()
        return 0

    def run_step(self):
        data_id = None
        t = time.perf_counter_ns()
        try:
            # get data_id from queue
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
                pass

        if data_id is not None and self.frame_num is not None:

            self.data = np.frombuffer(self.client.client.get(data_id), np.float64).reshape(self.num_channels, self.window)

            # accumulate 100ms of data
            if self.frame_num < 100:
                d = butter_filter(self.data, 1_000, 30_000)
                self.median_data.append(d)
                self.frame_num += 1
                return
            # use accumulated data to calculate median
            elif self.frame_num == 100:
                self.median = np.median(np.concatenate(np.array(self.median_data), axis=1), axis=1)
                self.improv_logger.info("Initialized median")
                np.save("/home/clewis/repos/realSpike/real_spike/stream_data/median.npy", self.median)

            # high pass filter
            data = butter_filter(self.data, 1000, 30_000)

            # get spike counts and report
            spike_times, spike_counts = get_spike_events(data, self.median)
            
            # if self.frame_num % 100 == 0:
            #     # sum spike events across channels
            # self.improv_logger.info(f"Processed frame {self.frame_num}, spike counts: {spike_counts}")

            # reuse data id from before
            self.client.client.set(data_id, data.tobytes(), nx=False)

            try:
                # output the data
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.frame_num, t2 - t)
                self.frame_num += 1

            except Exception as e:
                self.improv_logger.error(f"Processor Exception: {e}")