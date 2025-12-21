"""Utility functions for doing MUA."""
import scipy
import numpy as np
import tifffile


# define filter functions
def _butter(cutoff, fs, order=5, btype='high'):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = scipy.signal.butter(order, normal_cutoff, btype=btype, analog=False)
    return b, a


def butter_filter(
        data: np.ndarray, 
        cutoff: float = 1_000, 
        fs: float = 30_000, 
        order: int = 5, 
        axis: int = -1, 
        btype='high'
    ):
    """
    High pass filter the raw voltage data. 
    
    Parameters
    ----------
    data: np.ndarray 
        Array representing channels x time 
    cutoff: float, default 1_000 Hz 
        Voltage threshold (in Hz)
    fs: float, default 30_000
        Sampling rate 
    order: int, default 5 
        Controls filter complexity 
    axis: int, default -1 
        Axis to apply the filter along (filter across last dim (rows) by default)
    btype: string, default 'high'
        Type of filter to apply     
    """
    # check the dim of the data 
    if data.ndim != 2:
        raise ValueError(f"Data passed in must be (channels, time). You have paased in an array of dim {data.ndim}.")
    b, a = _butter(cutoff, fs, order=order, btype=btype)
    y = scipy.signal.filtfilt(b, a, data, axis=axis)
    return y


def get_spike_events(data: np.ndarray, median: np.ndarray, num_dev: int = 5):
    """
    Use the MAD to calculate spike times num_dev above and below the provided median.

    Parameters
    ----------
    data: np.ndarray 
        Array representing channels x time 
    median: np.ndarray 
        1D array representing the median value for each channel 
    num_dev: int, default 5
        Number of MAD deviations to threshold spikes above and below the median 
    """
    # validate data
    if data.ndim != 2:
        raise ValueError(f"Data passed in must be (channels, time). You have paased in an array of dim {data.ndim}.")
    # validate median 
    if data.shape[0] != median.shape[0]:
        raise ValueError(f"Number of channels in data array must match number of median values provided. Data shape: {data.shape[0]} != Median shape: {median.shape[0]}")

    # calculate mad
    mad = scipy.stats.median_abs_deviation(data, axis=1)

    # Calculate threshold
    thresh = (num_dev * mad) + median

    # Vectorized computation of absolute data
    abs_data = np.abs(data)

    # Find indices where threshold is crossed for each channel
    spike_indices = [np.where(abs_data[i] > thresh[i])[0] for i in range(data.shape[0])]

    spike_counts = [np.count_nonzero(arr) for arr in spike_indices]

    return spike_indices, spike_counts


def make_raster(ixs, COLORS):
    """
    Takes a list of threshold crossings and returns a list of points (channel number, spike time) and colors.
    Used to make a raster plot.
    """
    spikes = list()

    for i, ix in enumerate(ixs):
        ys = np.full(ix.shape, i * 35)
        sp = np.vstack([ix, ys]).T
        spikes.append(sp)

    colors = list()

    for j, i in enumerate(spikes):
        # randomly select a color
        c = [COLORS[j]] * len(i)
        colors += c

    return spikes, np.array(colors)


def bin_spikes(spikes: np.ndarray, bin_size: int):
    """Bin spikes into bins of given size (in ms)."""
    n_channels, n_timepoints = spikes.shape # (y, x)
    n_bins = n_timepoints // bin_size  # drop remainder

    spikes = spikes[:, :n_bins * bin_size]  # truncate to fit bins

    # Reshape and sum
    binned = spikes.reshape(n_channels, n_bins, bin_size).sum(axis=2)
    return binned




