from improv.actor import Actor
import logging;
from .sglx_pkg import sglx as sglx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Acquirer(Actor):
    """Establish a connection with SpikeGLX and acquire data to be put into a queue for the visualizer to take."""
    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.name = "Acquirer"

    def __str__(self):
        return f"Name: {self.name}, Data: {self.data}"

    def setup(self):
        # create a spikeglx connection handle
        self.hSglx = sglx.c_sglx_createHandle()
        # connect to spikeglx running on acquisition machine
        ip_address = "192.168.0.101"
        port = 4142
        c_sglx_connect( hSglx, ip_address.encode, port)
        #ok = sglx.c_sglx_connect(self.hSglx, "localhost".encode(), 4142)
        # start data acquisition
        logger.info('Completed setup for Acquirer')

    def stop(self):
        print("Stopping acquisition")
        # stop acquisition
        sglx.c_sglx_stopRun(self.hSglx)
        # close connection handle
        sglx.c_sglx_close(self.hSglx)
        # destroy handle
        sglx.c_sglx_destroyHandle(self.hSglx)

    def runStep(self):
        # start acquisition
        #sglx.c_sglx_startRun(self.hSglx)
        pass
