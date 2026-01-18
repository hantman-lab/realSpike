from improv.actor import ZmqActor
import logging
import time
import numpy as np
import serial

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

STIM_LENGTH_TIME = 0.005
LAST_STIM = time.perf_counter()


class LaserTrigger(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "LaserTrigger"
        # start the video from queue
        self.frame_num = 0
        self.latency = LatencyLogger(
            name="laser_trigger",
            max_size=50_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        self.patterns = np.load(
            "/home/clewis/repos/holo-nbs/experiment_data/preset_patterns.npy"
        )
        self.improv_logger.info("Completed setup for laser trigger")

    def stop(self):
        self.improv_logger.info("Laser trigger stopping")
        self.latency.save()
        return 0

    def run_step(self):
        global STIM_LENGTH_TIME, LAST_STIM
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            t = time.perf_counter_ns()
            data = np.from_buffer(self.client.client.get(data_id))
            trial_num = data[0]
            detected = data[1]
            if detected:
                # check for control trial, do not turn on laser if so
                if np.count_nonzero(self.patterns[trial_num]) == 0:
                    self.improv_logger.info("CONTROL TRIAL")
                    return
                if (t - LAST_STIM) / 1e6 <= 0.0025:
                    self.improv_logger.info(
                        "Previous stim occurred less than 2.5ms second ago."
                    )
                    return
                self.improv_logger.info("SENDING LASER SIGNAL")
                stim_time = time.perf_counter_ns()
                # send command out on serial port
                with serial.Serial("/dev/ttyACM0", 115200, timeout=1) as ser:
                    ser.write(b"STIM 13 4 0 5000 10000 1\n")
                LAST_STIM = stim_time

            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
            self.frame_num += 1
