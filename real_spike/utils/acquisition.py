from ctypes import byref, POINTER, c_int, c_short, c_bool, c_char_p
from .sglx_pkg import sglx

import numpy as np
import pickle
from typing import List, Dict


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

def validation_voltage(data):
    ground_truth = np.load("/home/clewis/repos/realSpike/ground_truth_voltage.npy")
    return np.alltrue(data == ground_truth)

def get_debug_meta():
    with open("/home/clewis/repos/realSpike/meta.pkl", "rb") as f:
        meta = pickle.load(f)
    return meta

def get_channels(meta_data: Dict[str, str]):
    """Returns the channels that were saved from that particular run."""
    if meta_data['snsSaveChanSubset'] == 'all':
        # output = int32, 0 to nSavedChans - 1
        return np.arange(int(meta_data['nSavedChans']), dtype=np.int32)

    channel_list = list()
    # parse the snsSaveChanSubset string
    # split at commas
    for clist in  meta_data['snsSaveChanSubset'].split(sep=','):
        # split each sublist at colon
        ixs = clist.split(sep=':')
        if len(ixs) > 1:
            # each set of contiguous channels specified by
            # chan1:chan2 inclusive
            channel_list.append(np.arange(int(ixs[0]), int(ixs[1])+1))
        else:
            # only one channel listed
            channel_list.append(np.arange(int(ixs[0]), int(ixs[0])+1))
    return np.concatenate(channel_list)


def get_channel_gain(meta_data: Dict[str, str]):
    """Returns the AP gain correction for each channel."""
    # list of probe types with NP 1.0 imro format
    # np1_imro = [0,1020,1030,1200,1100,1120,1121,1122,1123,1300]

    # number of channels acquired for each AP, LF, Sy
    acquire_counts = meta_data['acqApLfSy'].split(sep=',')
    # only need the first entry because we only care about AP correction
    APgain = np.zeros(int(acquire_counts[0]))  # default type = float64

    # if 'imDatPrb_type' in meta_data:
    #     probeType = int(meta_data['imDatPrb_type'])
    # else:
    #     probeType = 0

    # imro + probe allows setting gain independently for each channel
    # One entry for each channel plus header entry,
    # plus a final empty entry following the last ')'
    # TODO: is gain for each channel always constant?
    #  If so, can simply check the first any move on (i.e. could all be 500)
    imro = meta_data['imroTbl'].split(sep=')')[1:-1]

    for i in range(0, int(acquire_counts[0])):
        entry = imro[i].split(sep=' ')
        APgain[i] = float(entry[3])

    return APgain


def int2_volts(meta):
    if 'imMaxInt' in meta:
        maxInt = int(meta['imMaxInt'])
    else:
        maxInt = 512
    fI2V = float(meta['imAiRangeMax'])/maxInt

    return fI2V


def gain_correction(data: np.ndarray, meta_data: Dict[str, str], channel_list: List[int]):
    """Gain correction for an imec probe."""
    # Look up gain with acquired channel ID
    chans = get_channels(meta_data)
    APgain = get_channel_gain(meta_data)
    nAP = len(APgain)
    # nNu = nAP * 2

    # Common conversion factor
    fI2V = int2_volts(meta_data)

    # make array of floats to return. dataArray contains only the channels
    # in chanList, so output matches that shape
    convArray = np.zeros(data.shape, dtype='float')
    for i in range(len(channel_list)):
        j = channel_list[i]     # get channel ix
        k = chans[j]        # get the channel
        if k < nAP: # make sure it is not nidaq channel
            conv = fI2V / APgain[k]
        # elif k < nNu:
        #     conv = fI2V / LFgain[k - nAP]
        else:
            conv = 1
        # The dataArray contains only the channels in chanList
        convArray[i, :] = data[i, :] * conv
    return convArray