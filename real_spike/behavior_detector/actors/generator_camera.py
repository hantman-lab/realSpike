from improv.actor import ZmqActor
import tifffile
import logging
import time
import uuid
import numpy as np
from pathlib import Path
import sys
import os
import cv2
import h5py

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import LatencyLogger, LazyVideo

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# toggle for which behavior to detect
GRAB = False

# use session rb50/20250125
video_dir = Path("/home/clewis/repos/holo-nbs/data/videos/")


class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Generator"
        # start the video from queue
        if GRAB:
            self.frame_num = 600  # grabs start later
            _ = "grab"
        else:
            self.frame_num = 500
            _ = "lift"
        self.latency = LatencyLogger(
            name=f"generator_behavior_detector_{_}",
            max_size=20_000,
        )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # check to make sure I mounted the wasabi directory
        if not video_dir.is_dir():
            raise FileNotFoundError(f"Video directory {video_dir} not found.")

        data = h5py.File(
            "/home/clewis/wasabi/reaganbullins2/ProjectionProject/rb50/20250125/MAT_FILES/rb50_20250125_datastruct_pt3.mat",
            "r",
        )["data"]
        # get single_reach idxs of all videos
        single_reach = data["single"]
        self.idxs = np.where(single_reach)[0]

        if GRAB:
            self.grabs = data["grab_ms"]
        else:
            self.lifts = data["lift_ms"]
        self.i = 0
        # use lazy video to make array for reading frames from disk during run step
        self.video = self.get_video()
        self.offset = 0

        assert self.video[0].shape == (290, 448, 3), (
            "Frame shape is not (290, 448, 3). Pre-set crop measurement and bounding box assumptions might not work."
        )

        self.improv_logger.info("Completed setup for Generator")

    def get_video(self):
        if self.i > self.idxs.shape[0] - 1:
            self.video = None
            return

        idx = self.idxs[self.i]
        self.improv_logger.info(f"Trial: {idx}")
        if GRAB:
            self.improv_logger.info(f"ACTUAL: {500 + self.grabs[idx] / 2}")
        else:
            self.improv_logger.info(f"ACTUAL: {500 + self.lifts[idx] / 2}")
        if idx < 9:
            num = f"00{idx + 1}"
        elif idx < 99:
            num = f"0{idx + 1}"
        else:
            num = str(idx + 1)

        video_path = video_dir.joinpath(
            f"rb50_20250125_side_v{num}.avi"
        )  # zero-indexing in python vs. trial indexing; add 1
        return LazyVideo(video_path)

    def stop(self):
        self.improv_logger.info(
            f"Generator stopping: {self.frame_num} frames generated"
        )
        self.latency.save()
        return 0

    def run_step(self):
        # emulate camera, sleep for 2ms between frames
        time.sleep(0.002)
        if self.video is None:
            # iterated through all
            return
        if self.frame_num == 850:
            # get next video
            if GRAB:
                self.frame_num = 600
            else:
                self.frame_num = 500
            self.i += 1
            self.video = self.get_video()
            if self.video is None:
                return
            self.offset = 250 * self.i
            return

        # get the next frame
        # lazy loading, so do not want to include in timing for right now
        # will include when actually fetching
        # inclusion of frame rate 500Hz, 1 frame every

        self.frame = self.video[self.frame_num]
        t = time.perf_counter_ns()
        # convert to grayscale
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY).astype(np.uint16)
        # make a data_id
        data_id = str(os.getpid()) + str(uuid.uuid4())

        data = np.append(self.frame.ravel(), self.frame_num).astype(np.uint16)
        self.client.client.set(data_id, data.tobytes(), nx=False)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num + self.offset, t2 - t)
            self.client.client.expire(data_id, 5)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")
