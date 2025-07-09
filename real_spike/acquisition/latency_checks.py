"""Test latency for fetching data using netgear switch."""

from real_spike.utils.sglx_pkg import sglx as sglx
from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
import time
import pandas as pd
import os
from datetime import datetime
from tqdm import tqdm


def connect(ip_address: str, port: int):
    """
    Attempt to connect to SpikeGLX SDK running on acquisition machine. If successful, check to make sure
    initialization and data acquisition is in progress.

    Returns `None` if an error occurs in any of the set-up steps. Returns the current SpikeGLX handle being used
    if successful.
    """
    # connect to SpikeGLX
    print("Calling connect...\n")
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


def fetch(
        hSglx,
        channel_num: int = 384,
        sample_num: int = 150,
        ip: int = 0,
        js: int = 2,
        downsample: int = 1
):
    """
    Get the latency at differing interval and sample rates to be stored in a pandas dataframe.

    Parameters
    ----------
    hSglx:
        SpikeGLX handle
    channel_num: int, default 384
        Number of channels on probe to fetch from.
    sample_num: int, default 150
        Number of samples to fetch. 5ms default
    ip: int, default 0
        Probe number.
    js: int, default 2
        Probe type (imec=2)
    downsample: int, default 1
        Factor to downsample by, every n-th sample taken
    """
    df_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latency_df.h5")
    COLUMN_NAMES = ["datetime", "num_channels", "num_samples", "downsample_factor", "avg_latency", "times"]

    if not os.path.exists(df_path):
        df = pd.DataFrame(
            data=None,
            columns=COLUMN_NAMES
        )
    else:
        df = pd.read_hdf(df_path)

    data = POINTER(c_short)()
    n_data = c_int()
    py_chans = [i for i in range(channel_num)]
    nC = len(py_chans)
    channels = (c_int * nC)(*py_chans)

    times = list()

    for i in tqdm(range(1000)):
        t = time.perf_counter_ns()
        headCt = sglx.c_sglx_fetchLatest(byref(data), byref(n_data), hSglx, js, ip, sample_num, channels, nC, downsample)
        t2 = time.perf_counter_ns() - t
        times.append(t2 / 1e6)

    # append row to end of dataframe
    df.loc[len(df.index)] = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                             channel_num,
                             sample_num,
                             downsample,
                             sum(times) / len(times),
                             times]

    # save the dataframe
    df.to_hdf(df_path, key="df")

    print(df)

    return


if __name__ == "__main__":
    ip_address = "192.168.0.101"
    port = 4142

    hSglx = connect(ip_address="192.168.0.101", port=4142)

    if hSglx is not None:
        # try different fetch parameters and log latency (num channels, num samples, downsample)
        num_channels = [120, 150, 250, 384]
        downsample_factor = [1, 2]  # no downsampling
        num_samples = [30, 60, 90, 150, 300] # 1ms, 2ms, 3ms, 5ms, 10ms

        for d in tqdm(downsample_factor):
            for n in tqdm(num_channels):
                for s in tqdm(num_samples):
                    fetch(hSglx=hSglx,
                               channel_num=n,
                               sample_num=s,
                               ip=0,
                               js=2,
                               downsample=d)

        # will need to eventually close connection
        sglx.c_sglx_close(hSglx)
        sglx.c_sglx_destroyHandle(hSglx)
