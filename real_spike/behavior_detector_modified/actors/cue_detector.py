from improv.actor import ZmqActor
import logging
import time
import zmq
import os
import uuid

from real_spike.utils import LatencyLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

EXPERIMENT_TYPE = "test"

NUM_TRIALS = 300


class CueGenerator(ZmqActor):
    def __init__(self, *args, **kwargs):
        """
        Receives cue signal from a separate process.

        If doing holography: triggers the PDM to update the current display and the frame grabber to start
                             grabbing frames.
        If doing fiber: just triggers the frame grabber to start grabbing frames
        """
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "CueGenerator"
        self.latency = LatencyLogger(
            name="generator_cue",
            max_size=20_000,
        )

    def __str__(self):
        """Returns the name of the actor and the experiment type."""
        return f"Name: {self.name}, Experiment type: {EXPERIMENT_TYPE}"

    def setup(self):
        """
        Initialize the actor. Creates one ZMQ connection to the cue file to receive cue signals and another ZMQ
        connection to the PDM to trigger a change in the pattern.
        """
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

        # only need PDM computer for holography
        if EXPERIMENT_TYPE == "holography":
            # TODO: change to netgear address of this computer
            address = "192.168.0.100"
            # address = "localhost"
            port_number = 4146

            context = zmq.Context()
            self.PMD_socket = context.socket(zmq.PUB)
            self.PMD_socket.bind(f"tcp://{address}:{port_number}")

        # open PUB/SUB socket to laser trigger for odd trials that will have no behavior
        ip_address = "localhost"
        port = 5553
        context = zmq.Context()
        self.laser_socket = context.socket(zmq.PUB)
        self.laser_socket.bind(f"tcp://{ip_address}:{port}")

        self.improv_logger.info("Completed setup for CueGenerator")

    def stop(self):
        """
        Stop the actor.

        Cleans up resources and saves out logging information.
        """
        self.improv_logger.info("Cue generator stopping")
        self.latency.save()

        # clean up resources
        self.cue_socket.close()
        self.laser_socket.close()

        if EXPERIMENT_TYPE == "holography":
            self.PMD_socket.close()

        return 0

    def run_step(self):
        """
        A single step of the cue generator.

        Tries to unpack data from the external cue monitoring process.
        If successful, outputs a signal to the frame grabber to start grabbing frames. If doing holography,
        will also output signal to the PDM to trigger a change in the pattern.
        """
        t = time.perf_counter_ns()
        # try to receive something from cue script
        try:
            buff = self.cue_socket.recv(zmq.NOBLOCK)
        except zmq.Again:
            buff = None

        # stop at end of trials so we don't get out of bounds errors
        if self.trial_num >= NUM_TRIALS:
            return

        # cue received
        if buff is not None:
            # make a data_id
            data_id = str(os.getpid()) + str(uuid.uuid4())

            self.client.client.set(data_id, self.trial_num, nx=False)
            try:
                self.improv_logger.info("   ")
                self.improv_logger.info(f"CUE DETECTED, TRIAL: {self.trial_num}")

                if self.trial_num % 2 == 1:
                    self.laser_socket.send_string("1")
                    self.improv_logger.info("ODD TRIAL, NO BEHAVIOR DETECTION WILL BE DONE")
                else:
                    # send to frame grabber
                    self.q_out.put(data_id)
                # only need to update a display if doing holography
                if EXPERIMENT_TYPE == "holography":
                    # send to PMD
                    self.PMD_socket.send_string("1")
                t2 = time.perf_counter_ns()
                self.latency.add(self.trial_num, self.frame_num, t2 - t)
                self.client.client.expire(data_id, 5)
                self.trial_num += 1
                self.frame_num += 1
            except Exception as e:
                self.improv_logger.error(f"Generator Exception: {e}")
        else:  # cue not received, just log the frame
            t2 = time.perf_counter_ns()
            self.latency.add(self.trial_num, self.frame_num, t2 - t)
            self.frame_num += 1
