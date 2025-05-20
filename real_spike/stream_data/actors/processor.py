from improv.actor import ZmqActor
import logging
import scipy.signal
from real_spike.utils.latency import LatencyLogger
import time
import numpy as np
import pickle

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
        # self.latency.save()
        return 0

    def run_step(self):
        frame = None
        t = time.perf_counter_ns()
        try:
            # really getting a data_id in here
            frame = self.q_in.get(timeout=0.05)
            self.improv_logger.info(f"Processor: time to get data id in {(time.perf_counter_ns() - t) / 1e6}")
        except Exception as e:
            logger.error(f"{self.name} could not get frame! At {self.frame_num}: {e}")
            pass

        if frame is not None and self.frame_num is not None:
            self.done = False

            t_get_frame = time.perf_counter_ns()
            self.frame = self.client.get(frame)
            self.improv_logger.info(f"Processor: time to get data from store {(time.perf_counter_ns() - t_get_frame) / 1e6}")

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

            t_filt = time.perf_counter_ns()
            # high pass filter
            data = butter_filter(self.frame, 1000, 30_000)
            self.improv_logger.info(f"Processor: time to filter data {(time.perf_counter_ns() - t_filt) / 1e6}")


            t_spikes = time.perf_counter_ns()
            # get spike counts and report
            ixs = get_spike_events(data, self.median)
            # self.improv_logger.info(f"Time to get spikes: {(time.perf_counter_ns() - t_spikes) / 1e6}")

            if self.frame_num % 100 == 0:
                # sum spike events across channels
                spike_counts = [np.count_nonzero(arr) for arr in ixs]
                self.improv_logger.info(f"Processed frame {self.frame_num}, spike counts: {spike_counts}")

            # send filtered data to viz
            t_send_frame = time.perf_counter_ns()
            # data = zlib.compress(
            #     pickle.dumps(data, protocol=5), level=-1
            # )
            data = pickle.dumps(data, protocol=5)

            self.improv_logger.info(
                f"Processor: time to compress the data {(time.perf_counter_ns() - t_send_frame) / 1e6}")
            t_send_frame = time.perf_counter_ns()
            self.client.client.set(frame, data, nx=True)
            self.improv_logger.info(f"Processor: time to update data in store {(time.perf_counter_ns() - t_send_frame) / 1e6}")
            # data_id = self.client.put(data)
            try:
                # self.q_out.put(data_id)
                t = time.perf_counter_ns()
                self.q_out.put(frame)
                self.improv_logger.info(f"Processor: time to put frame in q out {(time.perf_counter_ns() - t) / 1e6}")
                t2 = time.perf_counter_ns()
                self.latency.add(self.frame_num, t2 - t)
                self.frame_num += 1

            except Exception as e:
                self.improv_logger.error(f"Processor Exception: {e}")



# define filter functions
def butter(cutoff, fs, order=5, btype='high'):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = scipy.signal.butter(order, normal_cutoff, btype=btype, analog=False)
    return b, a


def butter_filter(data, cutoff, fs, order=5, axis=-1, btype='high'):
    b, a = butter(cutoff, fs, order=order, btype=btype)
    y = scipy.signal.filtfilt(b, a, data, axis=axis)
    return y

# get initial spike events from filtered data
def get_spike_events(data: np.ndarray, median: np.ndarray, n_deviations: int = 4):
    """
    Calculates the median and MAD estimator. Returns a list of indices along each channel where
    threshold crossing is made (above absolute value of median + (n_deviations * MAD).
    """
    # median = np.median(data, axis=1)
    mad = scipy.stats.median_abs_deviation(data, axis=1)

    thresh = (n_deviations * mad) + median

    indices = [np.where(np.abs(data)[i] > thresh[i])[0] for i in range(data.shape[0])]

    return indices