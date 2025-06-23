from improv.actor import ZmqActor
import logging
import time
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger, fetch, get_meta
from real_spike.utils.sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEBUG_MODE = True


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0
        self.latency = LatencyLogger(name="generator_acquisition")


    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # create a spikeglx handle
        self.hSglx = sglx.c_sglx_createHandle()

        # connect to a given ip_address and port number
        ip_address = "10.172.16.169"
        port = 4142

        # only make a connection if not in debug mode
        if not DEBUG_MODE:
            if sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port):
                self.improv_logger.info("Successfully connected to SpikeGLX")
                self.improv_logger.info("version <{}>\n".format(sglx.c_sglx_getVersion(self.hSglx)))

                # TODO: if the connection works, also want to get the metadata
                self.meta_data = get_meta(self.hSglx)
            else:
                self.improv_logger.info("error [{}]\n".format(sglx.c_sglx_getError(self.hSglx)))
                raise Exception

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")

        # close the connection and handler
        sglx.c_sglx_close(self.hSglx)
        sglx.c_sglx_destroyHandle(self.hSglx)
        # save the latency
        self.latency.save()
        return 0

    def run_step(self):
        if DEBUG_MODE:
            # use fake fetch function
            t = time.perf_counter_ns()
            data = fetch()
        else:
            # fetch using sglx handler
            t = time.perf_counter_ns()
            data = self.hSglx.fetch()

        # convert the data from analog to voltage

        # send to processor
        data_id = str(os.getpid()) + str(uuid.uuid4())
        self.client.client.set(data_id, data, nx=True)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2 - t)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
