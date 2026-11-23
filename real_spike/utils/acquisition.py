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
        The type of stream (imec=2, nidaq=0)
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


def get_multiplier(hSglx, js=0, ip=0, chan=2):
    """Returns multiplier to convert digital signal to voltage."""
    multiplier = c_double()
    ok = sglx.c_sglx_getStreamI16ToVolts(byref(multiplier), hSglx, js, ip, chan)
    if ok:
        return multiplier.value
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
        return 1


def get_meta(file_path: str) -> Dict[str, str]:
    """
    Returns a dictionary of metadata associated with a previous SpikeGLX acquisition run.

    Parameters
    ----------
    file_path : str
        File name containing the metadata
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    metadata = dict()
    for line in file_path.read_text().splitlines():
        if "=" not in line:  # skip blank or malformed lines
            continue
        key, val = line.split(
            "=", 1
        )  # split on the first "=" only, values can contain "="
        metadata[key.lstrip("~")] = val  # table keys start with "~"

    return metadata


def get_sample_data(file_path: str, meta_data: Dict[str, str]) -> np.memmap:
    """
    Returns a (samples, channels) int16 memmap of data from a previous SpikeGLX acquisition run.
    Values are raw ADC counts.

    Parameters
    ----------
    file_path : str
        File name of the binary file containing the data
    meta_data : Dict[str, str]
        Dictionary containing metadata needed to load the data in the correct format
    """
    n_chan = int(meta_data["nSavedChans"])
    n_samp = Path(file_path).stat().st_size // (
        2 * n_chan
    )  # from the actual file size, in case the run was cut short

    data = np.memmap(
        file_path,
        dtype="int16",
        mode="r",
        shape=(
            n_samp,
            n_chan,
        ),  # samples are stored one after another, all channels per sample
        offset=0,
        order="C",
    )

    return data
