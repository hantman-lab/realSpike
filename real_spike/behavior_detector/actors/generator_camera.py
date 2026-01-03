from improv.actor import ZmqActor
import logging
import time
import uuid
import numpy as np
import os
import cv2
from threading import Event
import nidaqmx
from nidaqmx.constants import AcquisitionType, WindowTriggerCondition1, Signal

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Generator"
        self.latency = LatencyLogger(
            name="generator_behavior_camera",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def _analog_callback(self, task_handle, signal_type, callback_data):
        print("Analog signal detected")
        self.cue_signal.set()  # flip False -> True
        return 0

    def setup(self):
        # TODO: any kind of connection to the machine that gets the frames from the camera; probably a zmq port

        # bool for setting whether cue has been received
        # put in separate thread from the nidaq task to make sure it gets set properly
        self.cue_signal = Event()

        self.trial_num = 0
        self.frame_num = 500

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")
        self.latency.save()
        return 0

    def _check_cue(self):
        with nidaqmx.Task() as task:
            # TODO: change this with the actual device and channel
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")

            # TODO: change this to a little more than what the actual duration of the cue signal is
            # 50 / 5_000 = 0.01 ms duration of samples
            task.timing.cfg_samp_clk_timing(
                rate=5000, sample_mode=AcquisitionType.FINITE, samps_per_chan=50
            )

            task.start()

            data = np.asarray(task.read(100))

            # TODO: change this to the actual voltage crossing
            if np.any(data > 1.0):
                self.cue_signal.set()

    def run_step(self):
        # fetched enough frames to detect lift, reset and wait for next trial
        if self.frame_num == 850:
            # fetched 350 frames after cue, stop fetching for this trial
            self.frame_num = 500
            self.cue_signal.clear()
            self.trial_num += 1
            return

        # check for a cue signal only if at a new trial (frame num == 500)
        if self.frame_num == 500:
            self._check_cue()

        # check to see if trial cue has been received from NIDAQ
        # will check for cue again on next frame call, might just not be at end of present trial
        if not self.cue_signal.is_set():
            return

        t = time.perf_counter_ns()

        # TODO: get the frame via some request

        self.frame = np.random.rand(512, 512)

        # convert to grayscale
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY).astype(np.uint16)
        # make a data_id
        data_id = str(os.getpid()) + str(uuid.uuid4())

        data = np.append(self.frame.ravel(), self.trial_num).astype(np.uint32)
        data = np.append(data, self.frame_num).astype(np.uint32)

        self.client.client.set(data_id, data.tobytes(), nx=False)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
            self.client.client.expire(data_id, 5)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
