from improv.actor import ZmqActor
import logging
import time
import zmq
import os
import uuid

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CueGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CueGenerator"
        self.latency = LatencyLogger(
            name="generator_cue",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # every time we get a new cue, want to increment trial number
        self.trial_num = 0
        self.frame_num = 0

        address = "localhost"
        port = 5552

        context = zmq.Context()
        self.cue_socket = context.socket(zmq.SUB)
        self.cue_socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.cue_socket.connect(f"tcp://{address}:{port}")

        self.improv_logger.info(f"Connected socket to address {address} on port {port}")

        # TODO: change to netgear address of this computer
        address = "192.168.0.100"
        # address = "localhost"
        port_number = 4146

        context = zmq.Context()
        self.PMD_socket = context.socket(zmq.PUB)
        self.PMD_socket.bind(f"tcp://{address}:{port_number}")

        self.improv_logger.info("Completed setup for CueGenerator")

    def stop(self):
        self.improv_logger.info("Cue generator stopping")
        self.latency.save()

        # clean up resources
        self.cue_socket.close()
        self.PMD_socket.close()

        return 0

    def run_step(self):
        t = time.perf_counter_ns()
        # try to receive something from cue script
        try:
            buff = self.cue_socket.recv(zmq.NOBLOCK)
        except zmq.Again:
            buff = None

        # cue received
        if buff is not None:
            # make a data_id
            data_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(data_id, self.trial_num, nx=False)
            try:
                self.improv_logger.info(f"CUE DETECTED, TRIAL: {self.trial_num}")
                # send to frame grabber
                self.q_out.put(data_id)
                # send to PMD
                self.PMD_socket.send_string("1")
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
                self.trial_num += 1
            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
        else:
            return

        t2 = time.perf_counter_ns()
        self.latency.add(self.trial_num, self.frame_num, t2 - t)
        self.frame_num += 1
