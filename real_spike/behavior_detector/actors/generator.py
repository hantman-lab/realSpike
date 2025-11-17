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
GRAB = True

# use session rb50/20250125
video_dir = Path("/home/clewis/repos/holo-nbs/data/videos/")

class Generator(ZmqActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.name = "Generator"
        # start the video from queue
        self.frame_num = 600
        self.latency = LatencyLogger(name="generator_behavior_detector",
                                     max_size=20_000,
                                    )

    def __str__(self):
        return f"Name: {self.name}, Data: {self.frame}"

    def setup(self):
        # check to make sure I mounted the wasabi directory
        if not video_dir.is_dir():
            raise FileNotFoundError(f"Video directory {video_dir} not found. Directory needs to be mounted from Wasabi.")

        # get single_reach idxs of all videos
        single_reach = h5py.File("/home/clewis/wasabi/reaganbullins2/ProjectionProject/rb50/20250125/MAT_FILES/rb50_20250125_datastruct_pt3.mat", 'r')['data']['single']
        self.idxs = np.where(single_reach)[0]

        self.__iter__()
        # use lazy video to make array for reading frames from disk during run step
        self.video = next(self)
        self.offset = 0

        assert self.video[0].shape == (290, 448, 3), "Frame shape is not (290, 448, 3). Pre-set crop measurement and bounding box assumptions might not work."

        # set crop parameters
        # in the format (x_min, x_max, y_min, y_max)
        if GRAB:
             # [128:139, 250:254]
            self.crop = [250, 254, 128, 139]
        else:
            self.crop = [56, 195, 170, 291]

        self.improv_logger.info("Completed setup for Generator")

    def __iter__(self):
        self._current_iter = iter(range(self.idxs.shape[0]))
        return self

    def __next__(self):
        try:
            i = self._current_iter.__next__()
        except StopIteration:
            self.video = None
            return
        idx = self.idxs[i]
        if idx < 9:
            num = f"00{idx + 1}"
        elif idx < 99:
            num = f"0{idx + 1}"
        else:
            num = str(idx+1)

        video_path = video_dir.joinpath(f"rb50_20250125_side_v{num}.avi") # zero-indexing in python vs. trial indexing; add 1
        return LazyVideo(video_path)

    def stop(self):
        self.improv_logger.info(f"Generator stopping: {self.frame_num} frames generated")
        self.latency.save()
        return 0

    def run_step(self):
        if self.video is None:
            # iterated through all
            return
        if self.frame_num == 850:
            # get next video
            self.frame_num = 600
            self.video = next(self)
            if self.video is None:
                return
            self.offset += 1

        # get the next frame
        # lazy loading, so do not want to include in timing for right now
        # will include when actually fetching
        self.frame = self.video[self.frame_num]
        t = time.perf_counter_ns()
        # convert to grayscale
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        # y-dim comes first (height, width)
        self.frame = self.frame[self.crop[2]:self.crop[3], self.crop[0]:self.crop[1]]
        # make a data_id
        data_id = str(os.getpid()) + str(uuid.uuid4())
        self.client.client.set(data_id, self.frame.tobytes(), nx=True)
        try:
            self.q_out.put(data_id)
            t2 = time.perf_counter_ns()
            self.latency.add(self.frame_num + self.offset, t2-t)
            self.frame_num += 1

        except Exception as e:
            self.improv_logger.error(f"Generator Exception: {e}")