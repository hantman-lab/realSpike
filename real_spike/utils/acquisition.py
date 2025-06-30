from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p, c_double
from .sglx_pkg import sglx

import numpy as np
import pickle
from typing import List, Dict


def get_vmax(hSglx, ip=0, js=2):
    """
    Get the imec probe range max. Same as meta_data['imAiRangeMax'].

    Parameters
    ----------
    hSglx : sglx handler
    ip : int, default 0
        The probe number
    js : int, default 2
        The type of stream (imec=2)
    """
    vmin = c_double()
    vmax = c_double()
    ok = sglx.c_sglx_getStreamVoltageRange(byref(vmin), byref(vmax), hSglx, js, ip)
    if ok:
        return vmax.value
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
        return 1


def get_imax(hSglx, ip=0, js=2):
    """
    Get the imec probe max int. Same as meta_data['imMaxInt'].

    Parameters
    ----------
    hSglx : sglx handler
    ip : int, default 0
        The probe number
    js : int, default 2
        The type of stream (imec=2)
    """
    max_int = c_int()
    ok = sglx.c_sglx_getStreamMaxInt( byref(max_int), hSglx, js, ip )
    if ok:
        return max_int.value
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
        return 1

def get_gain(hSglx, ip=0, chan=0):
    """
    Get the imec probe gain for a given channel.

    Parameters
    ----------
    hSglx : sglx handler
    ip : int, default 0
        The probe number
    chan : int, default 0
        The channel to get the gain for (should be fixed across all channels
    """
    APgain = c_double()
    LFgain = c_double()
    ok = sglx.c_sglx_getImecChanGains(byref(APgain), byref(LFgain), hSglx, ip, chan)
    if ok:
        return APgain.value
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
        return 1

def fetch(hSglx, ip=0, js=2, num_samps=150, channel_ids=None):
    """Fetch data.

    Parameters
    ----------
    hSglx : sglx handler
    ip : int, default 0
        The probe number
    js : int, default 2
        The type of stream (imec=2)
    num_samps : int, default 150
        The number of samples to fetch, 1ms = 30samples (fetching 5ms of data by default)
    channel_ids : List[int], default None
        Specify a subset of channels to fetch data for, otherwise assumed to fetch all 384
    """
    data = POINTER(c_short)()
    n_data = c_int()
    if channel_ids is None:
        channel_ids = [i for i in range(384)]
    nC = len(channel_ids)
    channels = (c_int * nC)(*channel_ids)

    headCt = sglx.c_sglx_fetchLatest(byref(data), byref(n_data), hSglx, js, ip, num_samps, channels, nC, 1)

    if headCt > 0:
        # should equal the number of samples
        nt = int(n_data.value / nC)

        # turn into an array
        a = np.ctypeslib.as_array(data, shape=(nt * nC,))
        return a

def validation_voltage(data):
    ground_truth = np.load("/home/clewis/repos/realSpike/ground_truth_voltage.npy")
    return np.alltrue(data == ground_truth)

def get_debug_meta():
    with open("/home/clewis/repos/realSpike/meta.pkl", "rb") as f:
        meta = pickle.load(f)
    return meta


