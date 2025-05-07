"""Utility functions for making an MUA viz."""
from typing import List
import h5py
import scipy.signal
import numpy as np


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


def make_raster(ixs: List[np.ndarray]):
    """
    Takes a list of threshold crossings and returns a list of points (channel number, spike time) and colors.
    Used to make a raster plot.
    """
    spikes = list()

    for i, ix in enumerate(ixs):
        ys = np.full(ix.shape, i * 2)
        sp = np.vstack([ix, ys]).T
        spikes.append(sp)

    colors = list()

    for i in spikes:
        # randomly select a color
        c = [np.append(np.random.rand(3), 1)] * len(i)
        colors += c

    return spikes, np.array(colors)