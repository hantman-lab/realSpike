from improv.actor import ZmqActor
import logging
import time


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
        self.data = list()

        self.num_channels = 384

        self.latency = LatencyLogger("processor_acquisition")
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
            # really getting a data_id in here
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None and self.frame_num is not None:
            self.done = False

            self.frame = np.frombuffer(self.client.client.get(data_id), np.float64).reshape(self.num_channels, 150)

            # accumulate 4 seconds of data
            if self.frame_num < 27:
                d = butter_filter(self.frame, 1000, 30_000)
                self.data.append(d)
                # self.data_ids.append(data_id)
                self.frame_num += 1
                return
            # use accumulated data to calculate median
            elif self.frame_num == 27:
                self.improv_logger.info("Initialized median")
                self.median = np.median(np.concatenate(np.array(self.data), axis=1), axis=1)
                self.frame_num += 1
                return

            # high pass filter
            data = butter_filter(self.frame, 1000, 30_000)

            # get spike counts and report
            spike_times, spike_counts = get_spike_events(data, self.median)
            #
            # if self.frame_num % 100 == 0:
            #     # sum spike events across channels
            # self.improv_logger.info(f"Processed frame {self.frame_num}, spike counts: {spike_counts}")

            # reuse data id from before
            self.client.client.set(data_id, data.tobytes(), nx=False)

            try:
                # output the data
                # self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.frame_num, t2 - t)
                self.frame_num += 1
                self.client.client.delete(data_id)

            except Exception as e:
                self.improv_logger.error(f"Processor Exception: {e}")