from improv.actor import ZmqActor
import logging
import time
import nidaqmx

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

STIM_LENGTH_TIME = 0.005
LAST_STIM = time.time()


class LaserTrigger(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "LaserTrigger"
        # start the video from queue
        self.frame_num = None
        self.trial_num = None
        self.latency = LatencyLogger(
            name="laser_trigger",
            max_size=50_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # TODO: nidaqmx stuff setup
        self.improv_logger.info("Completed setup for laser trigger")

    def stop(self):
        self.improv_logger.info("Laser trigger stopping")
        self.latency.save()
        return 0

    def run_step(self):
        global STIM_LENGTH_TIME
        data_id = None

        try:
            # get data_id from queue in
            data_id = self.q_in.get(timeout=0.05)
        except Exception as e:
            pass

        if data_id is not None:
            t = time.perf_counter_ns()
            detected = self.client.client.get(data_id)
            if detected:
                self.improv_logger.info("SENDING LASER SIGNAL")
                with nidaqmx.Task() as task:
                    task.ao_channels.add_ao_voltage_chan("Dev1/ao1")

                    stim_time = time.perf_counter_ns()
                    task.write(5.0)

                    # hold pattern for stim length time
                    time.sleep(STIM_LENGTH_TIME)

                    task.write(0.0)

            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
