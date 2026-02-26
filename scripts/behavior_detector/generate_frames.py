"""Script for sending most recent frame saved to disk. Place on the bias computer."""

import os
import glob
import numpy as np
import zmq
import cv2
import time

# TODO: replace with path on bias computer
VIDEO_DIR = "D:/Reagan/test/side/"

ip_address = "192.168.0.103"
port = 4148

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")


current_folder = None
frame = None


"-----------------------------------------------------------------------------------------------------"


def get_latest_folder(base_dir):
    """Return the most recently made folder (most recent trial)."""
    subdirs = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    latest = max(subdirs, key=os.path.getmtime)
    return latest


def get_latest_frames(folder, n=3):
    """Get the n most recent frames from the given folder."""
    files = glob.glob(os.path.join(folder, "*.jpg"))

    # Sort files by frame number (descending)
    sorted_files = sorted(
        files,
        key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split("_")[-1]),
        reverse=True,
    )

    # Return the top n files
    return sorted_files[:n]


def retry_frame_grab(paths):
    """Attempts to take the last 3 frames and return one of them that has completed writing to disk."""
    img = None
    for path in paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            break
    return img


"-----------------------------------------------------------------------------------------------------"

while True:
    # Wait for client request
    message = socket.recv_string()

    # get the latest folder
    current_folder = get_latest_folder(VIDEO_DIR)
    # get the most recent frame
    most_recent_frames = get_latest_frames(current_folder)
    current_frame = most_recent_frames[0]

    # get the trial num to send with the grayscale image
    frame_num = int(current_frame.split("/")[-1].split(".")[0].split("_")[-1])

    # convert to gray scale
    img = cv2.imread(current_frame, cv2.IMREAD_GRAYSCALE)

    # sometimes the most recent frame is one that is still being written
    # just want to buffer for a second and try to get it again
    if img is None:
        retry_frame_grab(most_recent_frames)

    # if still image is none just skip
    if img is None:
        print(f"IMAGE IS STILL NONE, frame {frame_num}")
        img = np.zeros((290, 448))

    data = np.append(img.ravel(), frame_num).astype(np.uint32)

    socket.send(data.tobytes())
