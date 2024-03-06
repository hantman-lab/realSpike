"""Test latency at different sampling rates."""

from sglx_pkg import sglx as sglx
from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
from time import time
import pandas as pd
import os
from datetime import datetime


def set_up(ip_address: str, port: int):
    """
    Attempt to connect to SpikeGLX SDK running on acquisition machine. If successful, check to make sure
    initialization and data acquisition is in progress.

    Returns `None` if an error occurs in any of the set-up steps. Returns the current SpikeGLX handle being used
    if successful.
    """
    # connect to SpikeGLX
    print("Calling connect...\n\n")
    hSglx = sglx.c_sglx_createHandle()

    if sglx.c_sglx_connect(hSglx, ip_address.encode(), port):
        print("Successfully connected to SpikeGLX")
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

        sglx.c_sglx_close(hSglx)
        sglx.c_sglx_destroyHandle(hSglx)

        return None

    # if connection successful, check SpikeGLX initialization (startup and if data being acquired)
    ready = c_bool()
    ok = sglx.c_sglx_isInitialized(byref(ready), hSglx)
    if not ok:
        print("SpikeGLX has NOT completed its startup initialization")
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

        sglx.c_sglx_close(hSglx)
        sglx.c_sglx_destroyHandle(hSglx)
        return None
    else:
        print("SpikeGLX has completed startup initialization, checking if acquiring data...")
        # check if running
        running = c_bool()
        ok = sglx.c_sglx_isRunning(byref(running), hSglx)
        if ok:
            print("SpikeGLX is running")

            return hSglx
        if not ok:
            print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

            sglx.c_sglx_close(hSglx)
            sglx.c_sglx_destroyHandle(hSglx)

            return None


def data_fetch(
        hSglx,
        channel_num: int,
        sample_num: int,
        ip: int
):
    """
    Get the latency at differing interval and sample rates to be stored in a pandas dataframe.

    Parameters
    ----------
    hSglx:
        Active handle to open SpikeGLX SDK connection
    channel_num: int
        Number of channels on probe to fetch from.
    sample_num: int
        Number of samples to fetch.
    ip: int
        Probe number.
    """

    # load dataframe
    df_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latency_df.h5")

    df = pd.read_hdf(df_path)

    # try to fetch data and add latency to df as new row
    js = 2
    data = POINTER(c_short)()
    ndata = c_int()

    # collect from channels on the probe given by channel_num
    py_chans = [i for i in range(channel_num)]

    # number of channels getting data from
    n_cs = len(py_chans)

    # channel_subset is an array of specific channels to fetch, optionally,
    #      -1 = all acquired channels, or,
    #      -2 = all saved channels.
    channel_subset = (c_int * n_cs)(*py_chans)

    # downsample = every nth sample
    downsample = 1

    # get sampling rate
    srate = sglx.c_sglx_getStreamSampleRate(hSglx, js, ip)
    print("Sample rate {}\n".format(srate))

    if srate == 0:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
        return

    t = time()
    for i in range(sample_num):
        headCt = sglx.c_sglx_fetchLatest(byref(data),
                                         byref(ndata),
                                         hSglx,
                                         js,
                                         ip,
                                         int(srate),
                                         channel_subset,
                                         n_cs,
                                         downsample)

        if headCt > 0:
            nt = int(ndata.value / n_cs)
            print("Head count {}, samples {}\n".format(headCt, nt))
    t2 = time() - t

    # once fetch is done for given sample_rate, channel_num, sample_num
    # add row to df
    # print df
    df.loc[len(df.index)] = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), channel_num, sample_num, srate, t2]

    df.to_hdf(df_path, key="df")

    print(df)

    return


if __name__ == "__main__":
    # check setup before trying to fetch
    hSglx = set_up(ip_address="192.168.0.101", port=4142)

    if hSglx is not None:
        # get available probes
        list = c_char_p()
        ok = sglx.c_sglx_getProbeList(byref(list), hSglx)
        if ok:
            print(list.value)
        # get number of available channels on probe
        nval = c_int()
        ok = sglx.c_sglx_getStreamAcqChans(byref(nval), hSglx, 2, list[0])

        if ok:
            num_chan = sglx.c_sglx_getint(nval)
            print(f"Number of channels available for probe {list[0]} = {num_chan}")

        # data_fetch(hSglx=hSglx,
        #            channel_num=num_chan,
        #            sample_num=1000,
        #            ip=list[0])

        # will need to eventually close connection
        sglx.c_sglx_close(hSglx)
        sglx.c_sglx_destroyHandle(hSglx)
