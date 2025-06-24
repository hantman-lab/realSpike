from ctypes import *

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


def console_test(ip_address: str, port: int):
    print( "Console test...\n" )
    hSglx = sglx.c_sglx_createHandle()
    ok    = sglx.c_sglx_connect( hSglx, ip_address.encode(), port )

    if ok:
        hid = c_bool()
        ok  = sglx.c_sglx_isConsoleHidden( byref(hid), hSglx )
        if ok:
            print( "Console hidden: {}\n".format( bool(hid) ) )

    if not ok:
        print( "error [{}]\n".format( sglx.c_sglx_getError( hSglx ) ) )

    sglx.c_sglx_close( hSglx )
    sglx.c_sglx_destroyHandle( hSglx )


if __name__ == "__main__":
    # practice connection
    ip_address = "10.172.16.169"
    port = 4142
    console_test(ip_address=ip_address, port=port)
    check_initialization(ip_address=ip_address, port=port)
    get_datadir(ip_address=ip_address, port=port)
