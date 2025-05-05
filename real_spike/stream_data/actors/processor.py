from improv.actor import ZmqActor
import logging
import scipy.signal
import numpy as np
from typing import List

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
        self.improv_logger.info(f"Processor processed {self.frame_num} frames")
        return 0

    def run_step(self):
        frame = None
        try:
            frame = self.q_in.get(timeout=0.05)
        except Exception as e:
            logger.error(f"{self.name} could not get frame! At {self.frame_num}: {e}")
            pass

        if frame is not None and self.frame_num is not None:
            self.done = False
            self.frame = self.client.get(frame)

            # high pass filter
            data = butter_filter(self.frame, 1000, 30_000)

            # get spike counts and report
            ixs = get_spike_events(data)

            # sum spike events across channels
            spike_counts = [np.count_nonzero(arr) for arr in ixs]
            self.improv_logger.info("Processed frame, spike counts: {}".format(spike_counts))

            # send filtered data to viz
            data_id = self.client.put(data)
            try:
                self.improv_logger.info("Sending frame!")
                self.q_out.put(data_id)
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

def get_spike_events(data: np.ndarray, n_deviations: int = 4) -> List[np.ndarray]:
    """
    Calculates the median and MAD estimator. Returns a list of indices along each channel where
    threshold crossing is made (above absolute value of median + (n_deviations * MAD).
    """
    median = np.median(data, axis=1)
    mad = scipy.stats.median_abs_deviation(data, axis=1)

    thresh = (n_deviations * mad) + median

    indices = [np.where(np.abs(data)[i] > thresh[i])[0] for i in range(data.shape[0])]

    return indices