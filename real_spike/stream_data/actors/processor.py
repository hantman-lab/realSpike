from improv.actor import ZmqActor
import logging
import time
import pickle

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
        # initialize median with first 4 seconds of data (26 frames)
        self.median = None
        self.data = list()

        self.latency = LatencyLogger("processor")
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
            logger.error(f"{self.name} could not get frame! At {self.frame_num}: {e}")
            pass

        if data_id is not None and self.frame_num is not None:
            self.done = False

            self.frame = self.client.get(data_id)

            # accumulate 4 seconds of data
            if self.frame_num < 27:
                d = butter_filter(self.frame, 1000, 30_000)
                self.data.append(d)
                self.frame_num += 1
                return
            # use accumulated data to calculate median
            elif self.frame_num == 27:
                self.improv_logger.info("Initialized median")
                self.median = np.median(np.concatenate(np.array(self.data), axis=1), axis=1)

            # high pass filter
            data = butter_filter(self.frame, 1000, 30_000)

            # get spike counts and report
            # ixs = get_spike_events(data, self.median)
            #
            # if self.frame_num % 100 == 0:
            #     # sum spike events across channels
            #     spike_counts = [np.count_nonzero(arr) for arr in ixs]
            #     self.improv_logger.info(f"Processed frame {self.frame_num}, spike counts: {spike_counts}")

            # reuse data id from before
            data = pickle.dumps(data, protocol=5)
            self.client.client.set(data_id, data, nx=True)
            try:
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.frame_num, t2 - t)
                self.frame_num += 1

            except Exception as e:
                self.improv_logger.error(f"Processor Exception: {e}")