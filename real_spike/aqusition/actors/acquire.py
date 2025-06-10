from improv.actor import ZmqActor
import logging
from ctypes import *

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

sglx = CDLL( "../libSglxApi.so", winmode=0 )

class Acquirer(ZmqActor):
    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Acquirer"
        self.latency = LatencyLogger(name="aquirer")

    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # create a spikeglx connection handle
        self.hSglx = sglx.c_sglx_createHandle()
        self.improv_logger.info("SpikeGLX handler created")

        # connect to spikeglx running on acquisition machine
        ip_address = "192.168.0.101"
        port = 4142
        sglx.c_sglx_connect(self.hSglx, ip_address.encode(), port)
        self.improv_logger.info("SpikeGLX connection made")

        self.improv_logger.info('Completed setup for Acquirer')

    def stop(self):
        self.improv_logger.info("Stopping acquisition")
        # stop acquisition
        sglx.c_sglx_stopRun(self.hSglx)
        # close connection handle
        sglx.c_sglx_close(self.hSglx)
        # destroy handle
        sglx.c_sglx_destroyHandle(self.hSglx)
        self.latency.save()
        return 0

    def runStep(self):
        # start acquisition
        # ok = sglx.c_sglx_connect(self.hSglx, "localhost".encode(), 4142)
        # start data acquisition
        #sglx.c_sglx_startRun(self.hSglx)
        self.improv_logger.info("run run run")


