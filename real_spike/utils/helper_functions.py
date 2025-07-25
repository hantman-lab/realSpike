"""Utility functions for making an MUA viz."""
from typing import List
import scipy.signal
import numpy as np
import tifffile
import zmq


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

# TODO: hacky for now, will fix later
def get_global_median():
    file_path = "/home/clewis/repos/holo-nbs/rb26_20240111/raw_voltage_chunk.tif"
    data = tifffile.memmap(file_path)

    median = np.median(butter_filter(data[:, :4000], 1_000, 30_000), axis=1)

    return median

def get_buffer(sub):
    """Gets the buffer from the publisher."""
    try:
        b = sub.recv(zmq.NOBLOCK)
    except zmq.Again:
        pass
    else:
        return b

    return None

def connect(address: str = "127.0.0.1", port_number: int = 5558):
    """
    Connect to the pattern generator actor via zmq. Make sure that ports match and are different from visual
    actor ports.
    """
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, b"")

    # keep only the most recent message
    sub.setsockopt(zmq.CONFLATE, 1)

    # TODO: add in check to make sure specified port number is valid

    # address must match publisher in actor
    sub.connect(f"tcp://{address}:{port_number}")

    print(f"Made connection on port {port_number} at address {address}")

    return sub
