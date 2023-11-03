from sglx_pkg import sglx as sglx
from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p


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


def get_latency(ip_address: str, port: int):
    hSglx = sglx.c_sglx_createHandle()

    sglx.c_sglx_connect(hSglx, ip_address.encode(), port)

    js = 2
    ip = 0

    data = POINTER(c_short)()
    ndata = c_int()
    py_chans = [i for i in range(384, 769)]
    nC = len(py_chans)
    channels = (c_int * nC)(*py_chans)

    mv2i16 = 1.0 / (1200.0 / 250 / 1024)
    thresh = 0.45 * mv2i16
    id = 393 - 384
    level = 0
    line = "Dev4/port0/line5"

    print("Threshold {}\n".format(thresh))

    fromCt = sglx.c_sglx_getStreamSampleCount(hSglx, js, ip)

    if fromCt > 0:
        ok = sglx.c_sglx_setDigitalOut(hSglx, level, line.encode())

        if ok:
            while True:
                headCt = sglx.c_sglx_fetch(byref(data), byref(ndata), hSglx, js, ip, fromCt, 120, channels, nC, 1)

                if headCt == 0:
                    break

                tpts = int(ndata.value / nC)

                if tpts > 1:
                    diff = data[id + (tpts - 1) * nC] - data[id]
                    digOK = True

                    if diff > thresh and level == 0:
                        level = 1
                        digOK = sglx.c_sglx_setDigitalOut(hSglx, level, line.encode())
                    elif diff < -thresh and level == 1:
                        level = 0
                        digOK = sglx.c_sglx_setDigitalOut(hSglx, level, line.encode())

                    if not digOK:
                        break

                    fromCt = headCt + tpts

    sglx.c_sglx_close(hSglx)
    sglx.c_sglx_destroyHandle(hSglx)


if __name__ == "__main__":
    # connect the acquisition machine
    connect(ip_address="192.168.0.101", port=4142)
    # get latency
    #get_latency()

