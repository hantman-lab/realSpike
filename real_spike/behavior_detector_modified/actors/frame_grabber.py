from improv.actor import ZmqActor
import logging
import time
import uuid
import os
import numpy as np
import zmq

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CUE_DETECTED = False


class CameraGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CameraGenerator"
        self.latency = LatencyLogger(
            name="generator_camera",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # every time we get a new cue, want to increment trial number
        self.trial_num = -1
        self.frame_num = -1

        # open REQ/REP socket to bias computer over netgear switch
        ip_address = "192.168.0.102"
        ip_address = "localhost"
        port = 4147

        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{ip_address}:{port}")

        self.improv_logger.info("Completed setup for Camera Generator")

    def stop(self):
        self.improv_logger.info("Camera generator stopping")
        self.latency.save()
        self.socket.close()
        return 0

    def fetch(self):
        # request a frame
        self.socket.send_string("fetch()")
        # get reply
        data = self.socket.recv()

        return data

    def run_step(self):
        global CUE_DETECTED
        t = time.perf_counter()

        # cue not detected, try to get it
        if not CUE_DETECTED:
            data_id = None
            try:
                # get data_id from queue in
                data_id = self.q_in.get(timeout=0.05)
            except Exception as e:
                pass

            if data_id is not None:
                self.trial_num += 1
                self.improv_logger.info(
                    f"RECEIVED CUE TRIAL {self.trial_num}, START FETCHING FRAMES"
                )
                CUE_DETECTED = True
            # no cue yet
            else:
                return

        # at end of fetch
        if self.frame_num == 852:
            # reset cue detector
            CUE_DETECTED = False
            # reset frame num
            self.frame_num = -1
            return
        else:
            # fetch a frame
            self.socket.send_string("fetch()")
            # get reply
            data = self.socket.recv()

            data_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(data_id, data, nx=False)
            try:
                self.q_out.put(data_id)
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
