from sglx_pkg import sglx as sglx
from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
from time import time

def connect(ip_address: str, port: int):
    print("\nCalling connect...\n\n")
    hSglx = sglx.c_sglx_createHandle()

    # Using default loopback address and port
    if sglx.c_sglx_connect(hSglx, ip_address.encode(), port):
        print("Successfully connected to SpikeGLX")
        print("version <{}>\n".format(sglx.c_sglx_getVersion(hSglx)))
    else:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)

def get_params(ip_address: str, port: int):
    print( "\nGet params...\n\n" )
    hSglx = sglx.c_sglx_createHandle()
    ok    = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        nval = c_int()
        len  = c_int()
        ok   = sglx.c_sglx_getParams(byref(nval), hSglx)
        if ok:
            kv = {}
            for i in range(0, nval.value):
                line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
                parts = line.split( '=' )
                kv.update( {parts[0]: parts[1]} )
            print( "{}".format( kv.items() ) )

    if not ok:
        print( "error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)

def get_probes(ip_address: str, port: int):
    hSglx = sglx.c_sglx_createHandle()
    sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    l = c_char_p()

    ok = sglx.c_sglx_getProbeList(byref(l), hSglx)

    if ok:
        print(l.value)

    if not ok:
        print("bah")

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)

def fetch_data(ip_address: str, port: int):
    hSglx = sglx.c_sglx_createHandle()
    sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    running = POINTER(c_bool)()
    ok = sglx.c_sglx_isRunning(running, hSglx)

    if ok:
        print("yay")

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)
    return

    js = 2
    ip = 0

    #np = sglx.c_sglx_getStreamNP(,hSglx, js)

    fromCt = sglx.c_sglx_getStreamSampleCount(hSglx, js, ip)

    # srate = sglx.c_sglx_getStreamSampleRate(hSglx, js, ip)
    # print(srate)

    #if srate > 0:
    data = POINTER(c_short)()
    ndata = c_int()
    py_chans = [i for i in range(64)]
    nC = len(py_chans)
    channels = (c_int * nC)(*py_chans)

    t = time()
    headCt = sglx.c_sglx_fetch(byref(data), byref(ndata), hSglx, js, ip, fromCt, 120, channels, nC, 1)
    print(time()-t)

    print(byref(data))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


def getShankMap_test(ip_address, port):
    print( "\nGet shank map...\n\n" )
    hSglx = sglx.c_sglx_createHandle()
    ok    = sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    if ok:
        nval = c_int()
        len = c_int()
        ok = sglx.c_sglx_getNIShankMap(byref(nval), hSglx)
        if ok:
            for i in range(0, nval.value):
                print("{}".format(sglx.c_sglx_getstr(byref(len), hSglx, i)))

    if not ok:
        print("error [{}]\n".format(sglx.c_sglx_getError(hSglx)))

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


if __name__ == "__main__":
    # connect the acquisition machine
    #connect(ip_address="192.168.0.101", port=4142)
    # get probes
    #get_probes(ip_address="192.168.0.101", port=4142)
    # get params
    #get_params(ip_address="192.168.0.101", port=4142)
    # fetch data
    fetch_data(ip_address="192.168.0.101", port=4142)
    #getShankMap_test(ip_address="192.168.0.101", port=4142)

