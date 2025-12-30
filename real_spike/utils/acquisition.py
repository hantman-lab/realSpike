from ctypes import byref, POINTER, c_int, c_short, c_double
import numpy as np
from pathlib import Path
from typing import Dict

from .sglx_pkg import sglx


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
    ok = sglx.c_sglx_getStreamMaxInt(byref(max_int), hSglx, js, ip)
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
    num_channels = len(channel_ids)
    channels = (c_int * num_channels)(*channel_ids)

    headCt = sglx.c_sglx_fetchLatest(
        byref(data), byref(n_data), hSglx, js, ip, num_samps, channels, num_channels, 1
    )

    if headCt > 0:
        # should equal the number of samples
        nt = int(n_data.value / num_channels)

        # turn into an array
        a = np.ctypeslib.as_array(data, shape=(nt * num_channels,))
        return a


def get_sample_rate(hSglx, js=2, ip=0):
    """Returns the samples rate."""
    srate = sglx.c_sglx_getStreamSampleRate(hSglx, js, ip)
    return srate


def get_meta(file_path: str) -> Dict[str, str]:
    """
    Returns a dictionary of metadata associated with a previous SpikeGLX acquisition run.
    Only used when DEBUG_MODE=True.

    Should be a file_path that ends in `.meta`

    Parameters
    ----------
    file_path : str
        File name containing the metadata
    """
    # conver to path object
    file_path = Path(file_path)

    # initialize dictionary
    metadata = dict()

    if file_path.exists():
        with file_path.open() as f:
            mdata = f.read().splitlines()
            for m in mdata:
                item = m.split(sep="=")
                if item[0][0] == "~":
                    key = item[0][1 : len(item[0])]
                else:
                    key = item[0]
                metadata.update({key: item[1]})
    else:
        raise FileNotFoundError(file_path)

    return metadata


def get_sample_data(file_path: str, meta_data: Dict[str, str]):
    """
    Returns a numpy array of data from a previous SpikeGLX acquisition run.

    Should be a file_path that ends in `.bin`

    Parameters
    ----------
    file_path : str
        File name of the binary file containing the data
    meta_data : Dict[str, str]
        Dictionary containing metadata needed to load the data in the correct format
    """
    nChan = int(meta_data["nSavedChans"])
    nFileSamp = int(int(meta_data["fileSizeBytes"]) / (2 * nChan))

    data = np.memmap(
        file_path,
        dtype="int16",
        mode="r",
        shape=(nChan, nFileSamp),
        offset=0,
        order="F",
    )

    return data
