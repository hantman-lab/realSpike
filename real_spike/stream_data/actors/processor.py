from improv.actor import ZmqActor
import logging
from real_spike.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Processor(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in kwargs:
            self.name = kwargs["name"]

    def setup(self):
        if not hasattr(self, "name"):
            self.name = "Processor"
        self.frame = None
        self.frame_num = 1
        self.improv_logger.info("Completed setup for Processor")

    def stop(self):
        self.improv_logger.info("Processor stopping")
        self.improv_logger.info(f"Processor processed {self.frame_num} frames")
        return 0

    def run_step(self):
        frame = None
        try:
            frame = self.q_in.get(timeout=0.05)
        except Exception as e:
            logger.error(f"{self.name} could not get frame! At {self.frame_num}: {e}")
            pass

        if frame is not None and self.frame_num is not None:
            self.done = False
            self.frame = self.client.get(frame)

            # high pass filter
            data = butter_filter(self.frame, 1000, 30_000)

            # get spike counts and report
            # ixs = get_spike_events(data)
            #
            # # sum spike events across channels
            # spike_counts = [np.count_nonzero(arr) for arr in ixs]
            # self.improv_logger.info("Processed frame, spike counts: {}".format(spike_counts))

            # send filtered data to viz
            data_id = self.client.put(data)
            try:
                self.improv_logger.info("Sending frame!")
                self.q_out.put(data_id)
                self.frame_num += 1

            except Exception as e:
                self.improv_logger.error(f"Processor Exception: {e}")