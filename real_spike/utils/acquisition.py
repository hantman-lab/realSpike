from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
from .sglx_pkg import sglx

import numpy as np
import pickle
import random

def fetch():
    """Return 5ms of analog data stored on disk."""
    data = np.load("/home/clewis/repos/realSpike/analog_data.npy")
    # TODO: reformat this data so it will be how it comes off when you call fetchLatest
    i = random.randint(0, data.shape[1] - 151)
    return data[:, i:i+150]


def get_meta(hSglx):
    """Returns a dictionary containing the run params for SpikeGLX."""
    nval = c_int()
    len = c_int()
    ok = sglx.c_sglx_getParams(byref(nval), hSglx)
    if ok:
        kv = {}
        for i in range(0, nval.value):
            line = sglx.c_sglx_getstr(byref(len), hSglx, i).decode()
            parts = line.split('=')
            kv.update({parts[0]: parts[1]})
        # print("{}".format(kv.items()))
    return kv

def get_debug_meta():
    with open("/home/clewis/repos/realSpike/meta.pkl", "rb") as f:
        meta = pickle.load(f)
    return meta

def OriginalChans(meta):
    if meta['snsSaveChanSubset'] == 'all':
        # output = int32, 0 to nSavedChans - 1
        chans = np.arange(0, int(meta['nSavedChans']))
    else:
        # parse the snsSaveChanSubset string
        # split at commas
        chStrList = meta['snsSaveChanSubset'].split(sep=',')
        chans = np.arange(0, 0)  # creates an empty array of int32
        for sL in chStrList:
            currList = sL.split(sep=':')
            if len(currList) > 1:
                # each set of contiguous channels specified by
                # chan1:chan2 inclusive
                newChans = np.arange(int(currList[0]), int(currList[1])+1)
            else:
                newChans = np.arange(int(currList[0]), int(currList[0])+1)
            chans = np.append(chans, newChans)
    return(chans)


def ChanGainsIM(meta):
    # list of probe types with NP 1.0 imro format
    # np1_imro = [0,1020,1030,1200,1100,1120,1121,1122,1123,1300]
    # number of channels acquired
    acqCountList = meta['acqApLfSy'].split(sep=',')
    APgain = np.zeros(int(acqCountList[0]))  # default type = float64
    LFgain = np.zeros(int(acqCountList[1]))  # empty array for 2.0

    if 'imDatPrb_type' in meta:
        probeType = int(meta['imDatPrb_type'])
    else:
        probeType = 0

    # imro + probe allows setting gain independently for each channel
    imroList = meta['imroTbl'].split(sep=')')
    # One entry for each channel plus header entry,
    # plus a final empty entry following the last ')'
    for i in range(0, int(acqCountList[0])):
        currList = imroList[i + 1].split(sep=' ')
        APgain[i] = float(currList[3])
        LFgain[i] = float(currList[4])

    return (APgain, LFgain)


def Int2Volts(meta):
    if 'imMaxInt' in meta:
        maxInt = int(meta['imMaxInt'])
    else:
        maxInt = 512
    fI2V = float(meta['imAiRangeMax'])/maxInt

    return fI2V


def GainCorrectIM(dataArray, meta):
    # Look up gain with acquired channel ID
    chanList = list(range(0,384))
    chans = OriginalChans(meta)
    APgain, LFgain = ChanGainsIM(meta)
    nAP = len(APgain)
    nNu = nAP * 2

    # Common conversion factor
    fI2V = Int2Volts(meta)

    # make array of floats to return. dataArray contains only the channels
    # in chanList, so output matches that shape
    convArray = np.zeros(dataArray.shape, dtype='float')
    for i in range(0, len(chanList)):
        j = chanList[i]     # index into timepoint
        k = chans[j]        # acquisition index
        if k < nAP:
            conv = fI2V / APgain[k]
        elif k < nNu:
            conv = fI2V / LFgain[k - nAP]
        else:
            conv = 1
        # The dataArray contains only the channels in chanList
        convArray[i, :] = dataArray[i, :]*conv
    return(convArray)