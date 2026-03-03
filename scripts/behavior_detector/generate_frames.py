"""Script for sending most recent frame saved to disk. Place on the bias computer."""

import os
import glob
import numpy as np
import zmq
import cv2
import time
from pathlib import Path

# TODO: replace with path on bias computer
VIDEO_DIR = "D:/Reagan/test/side/"
VIDEO_DIR = Path("/home/clewis/repos/holo-nbs/data/videos/test/side2/")

ip_address = "192.168.0.103"
ip_address = "localhost"
port = 4148

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")

current_folder = None
frame = None

while True:
    # Wait for client request
    t = time.perf_counter_ns()

    # get the latest folder
    current_folder = sorted(
        VIDEO_DIR.glob("v*"), key=lambda f: f.stat().st_mtime, reverse=True
    )[0]
    trial_num = int(current_folder.stem.split("v")[-1]) - 1

    # get the most recent frame
    current_frame = sorted(
        current_folder.glob("*jpg"), key=lambda f: f.stat().st_mtime, reverse=True
    )[0]

    # get the trial num to send with the grayscale image
    frame_num = current_frame.stem.split("_")[-1]

    try:
        msg = socket.recv_string(flags=zmq.NOBLOCK)
        # process msg here

        # convert to gray scale
        img = cv2.imread(current_frame, cv2.IMREAD_GRAYSCALE)

        # if still image is none just skip
        if img is None:
            print(f"IMAGE IS STILL NONE, frame {frame_num}")
            img = np.zeros((290, 448))

        header = {
            "trial_num": trial_num,
            "frame_num": frame_num,
            "frame": frame,
            "encoding": "raw",
            "dtype": str(img.dtype),  # "uint8"
        }

        socket.send_json(header, flags=zmq.SNDMORE)
        # send zero-copy where possible
        socket.send(memoryview(img), copy=False)

        # data = np.append(img.ravel(), trial_num).astype(np.uint32)
        # data = np.append(data, frame_num).astype(np.uint32)
        #
        # socket.send(data.tobytes())
    except zmq.Again:
        continue

    print((time.perf_counter_ns() - t) / 1e6)
