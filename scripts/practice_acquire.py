from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p, c_double
import numpy as np
import time
from tqdm import tqdm

from real_spike.utils.sglx_pkg import sglx as sglx


def connect(ip_address: str, port: int):
    """Check that a connection can be made to SpikeGLX running on an acquisition machine."""
    print("Calling connect...\n")
    hSglx = sglx.c_sglx_createHandle()

    if sglx.c_sglx_connect(hSglx, ip_address.encode(), port):
        print("Successfully connected to SpikeGLX")
        print("version <{}>\n".format(sglx.c_sglx_getVersion(hSglx)))
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def check_initialization(ip_address: str, port: int):
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
            print(
                "SpikeGLX has completed startup initialization, checking if running..."
            )
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
    print("Getting params...")
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        nval = c_int()
        len = c_int()
        ok = sglx.c_sglx_getParams(byref(nval), hSglx)
        if ok:
            kv = {}
            for i in range(0, nval.value):
                line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
                parts = line.split("=")
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
        len = c_int()
        ok = sglx.c_sglx_getParamsImecProbe(byref(nval), hSglx, ip)
        if ok:
            kv = {}
            for i in range(0, nval.value):
                line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
                parts = line.split("=")
                kv.update({parts[0]: parts[1]})
            print("{}".format(kv.items()))
    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_imec_common(ip_address: str, port: int, ip=0):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        nval = c_int()
        len = c_int()
        ok = sglx.c_sglx_getParamsImecCommon(byref(nval), hSglx, ip)
        if ok:
            kv = {}
            for i in range(0, nval.value):
                line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
                parts = line.split("=")
                kv.update({parts[0]: parts[1]})
            print("{}".format(kv.items()))
    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_vmax(ip_address: str, port: int, ip=0, js=2):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        vMin = c_double()
        vMax = c_double()
        ok = sglx.c_sglx_getStreamVoltageRange(byref(vMin), byref(vMax), hSglx, js, ip)
        if ok:
            print(vMax.value)

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_gain(ip_address: str, port: int, ip=0, chan=0):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        APgain = c_double()
        LFgain = c_double()
        ok = sglx.c_sglx_getImecChanGains(byref(APgain), byref(LFgain), hSglx, ip, chan)
        if ok:
            print(APgain.value)

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_imax(ip_address: str, port: int, ip=0, js=2):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        maxInt = c_int()
        ok = sglx.c_sglx_getStreamMaxInt(byref(maxInt), hSglx, js, ip)
        if ok:
            print(maxInt.value)

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def console_test(ip_address: str, port: int):
    print("Console test...\n")
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        hid = c_bool()
        ok = sglx.c_sglx_isConsoleHidden(byref(hid), hSglx)
        if ok:
            print("Console hidden: {}\n".format(bool(hid)))

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def get_i2v(ip_address: str, port: int, ip=0, js=2, chan=1):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        mult = c_double()
        ok = sglx.c_sglx_getStreamI16ToVolts(byref(mult), hSglx, js, ip, chan)
        if ok:
            print(mult.value)

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def fetch_latest(ip_address: str, port: int, ip=0, js=2):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        data = POINTER(c_short)()
        n_data = c_int()
        py_chans = [i for i in range(150)]
        nC = len(py_chans)
        channels = (c_int * nC)(*py_chans)

        max_samps = 150

        APgain = c_double()
        LFgain = c_double()
        sglx.c_sglx_getImecChanGains(byref(APgain), byref(LFgain), hSglx, ip, 1)
        maxInt = c_int()
        sglx.c_sglx_getStreamMaxInt(byref(maxInt), hSglx, js, ip)
        vMin = c_double()
        vMax = c_double()
        sglx.c_sglx_getStreamVoltageRange(byref(vMin), byref(vMax), hSglx, js, ip)

        imax = maxInt.value
        vmax = vMax.value
        gain = APgain.value

        d = c_double()
        sglx.c_sglx_getStreamI16ToVolts(d, hSglx, js, ip, 0)

        headCt = sglx.c_sglx_fetchLatest(
            byref(data), byref(n_data), hSglx, js, ip, max_samps, channels, nC, 1
        )

        if headCt > 0:
            nt = int(n_data.value / nC)
            # print(nt)

            # a = np.ctypeslib.as_array(data, shape=(nt*nC,))
            a = np.ctypeslib.as_array(data, shape=(n_data.value,))
            # print(a)
            a = 1e6 * a * vmax / imax / gain
            a = a.reshape(nC, nt)

        sglx.c_sglx_close(hSglx)
        sglx.c_sglx_destroyHandle(hSglx)

        return a


def fetch(ip_address: str, port: int, ip=0, js=2, count=None):
    hSglx = sglx.c_sglx_createHandle()
    ok = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        data = POINTER(c_short)()
        n_data = c_int()
        py_chans = [i for i in range(150)]
        nC = len(py_chans)
        channels = (c_int * nC)(*py_chans)

        max_samps = 150

        APgain = c_double()
        LFgain = c_double()
        sglx.c_sglx_getImecChanGains(byref(APgain), byref(LFgain), hSglx, ip, 1)
        maxInt = c_int()
        sglx.c_sglx_getStreamMaxInt(byref(maxInt), hSglx, js, ip)
        vMin = c_double()
        vMax = c_double()
        sglx.c_sglx_getStreamVoltageRange(byref(vMin), byref(vMax), hSglx, js, ip)

        imax = maxInt.value
        vmax = vMax.value
        gain = APgain.value

        d = c_double()
        sglx.c_sglx_getStreamI16ToVolts(d, hSglx, js, ip, 0)

        if count is None:
            count = sglx.c_sglx_getStreamSampleCount(hSglx, js, ip)

        headCt = sglx.c_sglx_fetch(
            byref(data), byref(n_data), hSglx, js, ip, count, max_samps, channels, nC, 1
        )

        if headCt > 0:
            nt = int(n_data.value / nC)
            # print(nt)

            a = np.ctypeslib.as_array(data, shape=(nt * nC,))
            # print(a)
            a = 1e6 * a * vmax / imax / gain
            a = a.reshape(nC, nt)

        sglx.c_sglx_close(hSglx)
        sglx.c_sglx_destroyHandle(hSglx)

        return count, a


if __name__ == "__main__":
    # practice connection
    ip_address = "10.172.21.39"
    port = 4142
    # console_test(ip_address=ip_address, port=port)
    # check_initialization(ip_address=ip_address, port=port)
    # get_datadir(ip_address=ip_address, port=port)
    #
    # get_probes(ip_address=ip_address, port=port)
    #
    # get_params(ip_address=ip_address, port=port)
    # get_imec_params(ip_address=ip_address, port=port)
    # get_imec_common(ip_address=ip_address, port=port)
    # get_gain(ip_address=ip_address, port=port)
    # get_vmax(ip_address=ip_address, port=port)
    # get_imax(ip_address=ip_address, port=port)
    # get_i2v(ip_address=ip_address, port=port)

    # count, b = fetch(ip_address, port, ip=0, js=2)
    a = fetch_latest(ip_address=ip_address, port=port)
