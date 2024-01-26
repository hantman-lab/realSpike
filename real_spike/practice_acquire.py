from sglx_pkg import sglx as sglx
from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
from time import time


def connect(ip_address: str, port: int):
    """Check that connection can be made to SpikeGLX running on aquisition machine."""
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
    """Check initial conditions of SpikeGLX before attempting to fetch."""
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        ready = c_bool()
        ok = sglx.c_sglx_isInitialized(byref(ready), hSglx)
        if not ok:
            print("SpikeGLX has NOT completed its startup initialization")

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
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        list = c_char_p()
        ok = sglx.c_sglx_getProbeList(byref(list), hSglx)
        if ok:
            print(list.value)
    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_imec_params(ip_address: str, port: int, ip=0):
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
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        js = 2
        data = POINTER(c_short)()
        ndata = c_int()

        # collect from first 60 channels on the probe
        py_chans = [i for i in range(60)]

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

        if fromCt > 0:
            headCt = sglx.c_sglx_fetch(byref(data), byref(ndata), hSglx, js, ip, fromCt, max_samps, channel_subset,
                                       n_cs, downsample)

            if headCt == 0:
                print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))
                sglx.c_sglx_close(hSglx)
                sglx.c_sglx_destroyHandle(hSglx)
                return

            print(data.value)

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


if __name__ == "__main__":
    # practice connection
    connect(ip_address="192.168.0.101", port=4142)
    # get parameters
    get_params(ip_address="192.168.0.101", port=4142)
    # get the main data_dir
    get_datadir(ip_address="192.168.0.101", port=4142)
    # get probes
    get_probes(ip_address="192.168.0.101", port=4142)
    # get imec probe params for a given probe
    get_imec_params(ip_address="192.168.0.101", port=4142, ip=0)
    # fetch data
    fetch_data(ip_address="192.168.0.101", port=4142, ip=0)
