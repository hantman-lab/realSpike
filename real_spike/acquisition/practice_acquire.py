from time import time
from ctypes import *

from real_spike.utils.sglx_pkg import sglx as sglx


def connect(ip_address: str, port: int):
    """Check that connection can be made to SpikeGLX running on acquisition machine."""
    print("Calling connect...\n\n")
    hSglx = sglx.c_sglx_createHandle()

    if sglx.c_sglx_connect(hSglx, ip_address.encode(), port):
        print("Successfully connected to SpikeGLX")
        print("version <{}>\n".format(sglx.c_sglx_getVersion(hSglx)))
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def check_inits(ip_address: str, port: int):
    """
    Check initial conditions of SpikeGLX before attempting to fetch.

    1.) Checks if SpikeGLX has completed its startup initialization and is ready to run.
    2.) If initialization is True, will check if SpikeGLX is currently acquiring data.
    """
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        ready = c_bool()
        ok = sglx.c_sglx_isInitialized(byref(ready), hSglx)
        if not ok:
            print("SpikeGLX has NOT completed its startup initialization")
            print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

            sglx.c_sglx_close(hSglx)
            sglx.c_sglx_destroyHandle(hSglx)
            return
        else:
            print("SpikeGLX has completed startup initialization, checking if running...")
            # check if running
            running = c_bool()
            ok = sglx.c_sglx_isRunning(byref(running), hSglx)
            if ok:
                print("SpikeGLX is running")
                sglx.c_sglx_close(hSglx)
                sglx.c_sglx_destroyHandle(hSglx)
                return

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_params(ip_address: str, port: int):
    """Gets the most recent run parameters used for SpikeGLX."""
    print("Get params...")
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        print("Successfully connected to SpikeGLX")
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

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_datadir(ip_address: str, port: int):
    """Gets the global data directory."""
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        data_dir = c_char_p()
        ok = sglx.c_sglx_getDataDir(byref(data_dir), hSglx, 0)

        if ok:
            print(data_dir.value)
        if not ok:
            print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

            sglx.c_sglx_close(hSglx)
            sglx.c_sglx_destroyHandle(hSglx)
            return

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_probes(ip_address: str, port: int):
    """
    Gets the list of available probe list. Should return in the format:
    (probeID,nShanks,partNumber)
    """
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        list = c_char_p()
        ok = sglx.c_sglx_getProbeList(byref(list), hSglx)
        if ok:
            #print(sglx.c_sglx_getstr(list))
            print(list.value)
    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_imec_params(ip_address: str, port: int, ip=0):
    """
    Get parameters for a given imec probe. Probe id specified by `ip`.

    To get params of all available probes, see c_sglx_getParamsImecCommon.
    """
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        nval = c_int()
        ok = sglx.c_sglx_getParamsImecProbe(byref(nval), hSglx, ip)
        if ok:
            kv = {}
            for i in range(0, nval.value):
                line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
                parts = line.split('=')
                kv.update({parts[0]: parts[1]})
            print("{}".format(kv.items()))
    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def fetch_data(ip_address: str, port: int, ip=0):
    """
    Fetching data.

    Currently, get the number of available channels for the specified probe and
    then attempts to fetch for a given sample length.
    """
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        js = 2
        data = POINTER(c_short)()
        ndata = c_int()

        # first get the number of channels for a given probe
        nval = c_int()
        ok = sglx.c_sglx_getStreamAcqChans(byref(nval), hSglx, js, ip)

        if ok:
            num_chan = sglx.c_sglx_getint(nval)
            print(f"Number of channels available for probe {ip} = {num_chan}")

        if not ok:
            print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
            sglx.c_sglx_close(hSglx)
            sglx.c_sglx_destroyHandle(hSglx)
            return

        # collect from channels on the probe given by getStreamAcqChans
        py_chans = [i for i in range(num_chan)]

        # number of channels getting data from
        n_cs = len(py_chans)

        # channel_subset is an array of specific channels to fetch, optionally,
        #      -1 = all acquired channels, or,
        #      -2 = all saved channels.
        channel_subset = (c_int * n_cs)(*py_chans)

        # downsample = every nth sample
        downsample = 1

        # get number of samples since current run started
        # use as start sample
        fromCt = sglx.c_sglx_getStreamSampleCount(hSglx, js, ip)
        print(f"fromCt = {fromCt}")

        # max_samps = max # of samples to aquire
        max_samps = 120

        if fromCt > 0:
            # get time it takes to fetch
            t = time()
            headCt = sglx.c_sglx_fetch(byref(data), byref(ndata), hSglx, js, ip, int(fromCt), max_samps, channel_subset,
                                       n_cs, downsample)
            print(time() - t)

            # looks like fetchLatest takes the same params except doesn't use max_samps, will just fetch one time
            #headCt = sglx.c_sglx_fetchLatest(byref(data), byref(ndata), hSglx, js, ip, int(fromCt), channel_subset,
                                     #  n_cs, downsample)

            if headCt == 0:
                print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
                sglx.c_sglx_close(hSglx)
                sglx.c_sglx_destroyHandle(hSglx)
                return

            print(data.value)
        elif fromCt == 0:
            print("fromCt is 0, check if acquisition is set up properly")

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


if __name__ == "__main__":
    # practice connection
    ip_address = "10.172.68.138"
    port = 4142
    connect(ip_address=ip_address, port=port)
    # get initial conditions and if spikeglx is acquiring
    #check_inits(ip_address="192.168.0.101", port=4142)
    # get parameters
    #get_params(ip_address="192.168.0.101", port=4142)
    # get the main data_dir
    #get_datadir(ip_address="192.168.0.101", port=4142)
    # get probes
    #get_probes(ip_address="192.168.0.101", port=4142)
    # get imec probe params for a given probe
    #get_imec_params(ip_address="192.168.0.101", port=4142, ip=3)
    # fetch data
    fetch_data(ip_address=ip_address, port=4142, ip=3)
