"""
July 1, 2025. I am seeing increased latency when fetching data from SpikeGLX over Duke network.
I want to check if the latency is network based or the acquisition system.
This file is just for doing the same latency checks as when I pull the data over the network.
Basically running SpikeGLX on the same machine.
"""
import numpy as np
import time

from real_spike.utils import LatencyLogger, get_gain, get_imax, get_vmax, fetch, butter_filter, get_spike_events
from real_spike.utils.sglx_pkg import sglx as sglx

# two loggers, one for processing and one for generation
generator_logger = LatencyLogger(name="generator")
processor_logger = LatencyLogger(name="processor")

# make a connection
port_number = 4142
ip_address = "10.172.20.179"

# create a handle
hSglx = sglx.c_sglx_createHandle()

if sglx.c_sglx_connect(hSglx, ip_address.encode(), port_number):
    print("Successfully connected to SpikeGLX")
    print("version <{}>\n".format(sglx.c_sglx_getVersion(hSglx)))

# get the necesarry metadata
Vmax = get_vmax(hSglx)
Imax = get_imax(hSglx)
gain = get_gain(hSglx)

# store median
median_data = list()

# run a for loop to
for i in range(1000):
    # get the data
    t = time.perf_counter_ns()
    data = fetch(hSglx)

    # convert the data from analog to voltage
    data = 1e6 * data * Vmax / Imax / gain
    data = data.reshape(384, 150)

    # log the latency
    generator_logger.add(i, time.perf_counter_ns() - t)

    if i < 27:
        d = butter_filter(data, 1000, 30_000)
        median_data.append(d)
    elif i == 27:
        print("Initialized median")
        median = np.median(np.concatenate(np.array(median_data), axis=1), axis=1)
    else:
        # process the data
        t = time.perf_counter_ns()
        data = butter_filter(data, 1000, 30_000)
        spike_times, spike_counts = get_spike_events(data, median)


        # log the latency
        processor_logger.add(i, time.perf_counter_ns() - t)

# save latency
processor_logger.save()
generator_logger.save()

# close the connection
sglx.c_sglx_close(hSglx)
sglx.c_sglx_destroyHandle(hSglx)