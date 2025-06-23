from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
from .sglx_pkg import sglx

import numpy as np

def fetch():
    """Return 1s of analog data stored on disk."""
    data = np.load("/home/clewis/repos/realSpike/analog_data.npy")
    # TODO: reformat this data so it will be how it comes off when you call fetchLatest
    return data


def get_meta(hSglx):
    """Returns a dictionary containing the run params for SpikeGLX."""
    nval = c_int()
    len = c_int()
    ok = sglx.c_sglx_getParams(byref(nval), hSglx)
    if ok:
        kv = {}
        for i in range(0, nval.value):
            line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
            parts = line.split('=')
            kv.update({parts[0]: parts[1]})
        print("{}".format(kv.items()))
    return 0