"""Utility functions for making an MUA viz."""
from typing import List
import scipy.signal
import numpy as np
import tifffile


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


def get_spike_events(data: np.ndarray, median):
    # calculate mad
    mad = scipy.stats.median_abs_deviation(data, axis=1)

    # Calculate threshold
    thresh = (4 * mad) + median

    # Vectorized computation of absolute data
    abs_data = np.abs(data)

    # Find indices where threshold is crossed for each channel
    spike_indices = [np.where(abs_data[i] > thresh[i])[0] for i in range(data.shape[0])]

    spike_counts = [np.count_nonzero(arr) for arr in spike_indices]

    return spike_indices, spike_counts


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

# TODO: hacky for now, will fix later
def get_global_median():
    file_path = "/home/clewis/repos/holo-nbs/rb26_20240111/raw_voltage_chunk.tif"
    data = tifffile.memmap(file_path)

    median = np.median(butter_filter(data[:, :4000], 1_000, 30_000), axis=1)

    return median