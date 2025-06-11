from improv.actor import ZmqActor
import tifffile
import logging
import time
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger
from real_spike.utils.sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Generator"
        self.frame_num = 0
        # self.latency = LatencyLogger(name="generator")


    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # create a spikeglx handle
        self.hSglx = sglx.c_sglx_createHandle()

        # connect to a given ip_address and port number
        ip_address = "10.172.16.169"
        port = 4142

        if sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port):
            self.improv_logger.info("Successfully connected to SpikeGLX")
            self.improv_logger.info("version <{}>\n".format(sglx.c_sglx_getVersion(self.hSglx)))
        else:
            self.improv_logger.info("error [{}]\n".format(sglx.c_sglx_getError(self.hSglx)))
            raise Exception

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")

        # close the connection and handler
        sglx.c_sglx_close(self.hSglx)
        sglx.c_sglx_destroyHandle(self.hSglx)
        # self.latency.save()
        return 0

    def run_step(self):
        if self.frame_num < 10:
            self.improv_logger.info("Generator step")
        else:
            return
        self.frame_num += 1
