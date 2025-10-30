from improv.actor import ZmqActor
import tifffile
import logging
import time
import uuid
import numpy as np
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger, LazyVideo

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# use session rb50/20250125
video_dir = Path("/home/clewis/wasabi/reaganbullins2/ProjectionProject/rb50/20250125/videos/")

class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Generator"
        # start the video from queue
        self.frame_num = 500
        self.latency = LatencyLogger(name="generator_behavior_detector")

        # sample rate = 500Hz
        # self.sample_rate = 500

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # check to make sure I mounted the wasabi directory
        if not video_dir.is_dir():
            raise FileNotFoundError(f"Video directory {video_dir} not found. Directory needs to be mounted from Wasabi.")

        # for now, just process 1 video
        idx = 18 # index of single-reach trial in this dataset
        video_path = video_dir.joinpath(f"rb50_20250125_side_v0{idx + 1}.avi") # zero-indexing in python vs. trial indexing; add 1

        # use lazy video to make array for reading frames from disk during run step
        self.video = LazyVideo(video_path)


        assert self.video[0].shape == (290, 448), "Frame shape is not (290, 448). Pre-set crop measurement and bounding box assumptions might not work."

        self.improv_logger.info("Completed setup for Generator")

    def stop(self):
        self.improv_logger.info("Generator stopping")
        self.latency.save()
        return 0

    def run_step(self):
        # at end of video, stop running
        if self.frame_num == self.video.shape[0] - 1:
            return

        t = time.perf_counter_ns()
        # get the next frame
        self.frame = self.video[self.frame_num]
        # TODO: add crop (need to determine good bounding box first)
        # crop the frame to the pre-specified region (around where the hand rests at cue)

        # make a data_id
        data_id = str(os.getpid()) + str(uuid.uuid4())
        self.client.client.set(data_id, self.frame.tobytes(), nx=True)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num, t2-t)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")