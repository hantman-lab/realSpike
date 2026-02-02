"""Use this file when working on the same system. Streaming locally."""

import os
import glob
import numpy as np
import zmq
import cv2
import time

VIDEO_DIR = "/home/clewis/repos/holo-nbs/data/videos/test/side/"

ip_address = "localhost"
port = 4147

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")

current_folder = None
current_frame = None


def get_latest_folder(base_dir):
    """Return the most recently made folder (most recent trial)."""
    subdirs = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    latest = max(subdirs, key=os.path.getmtime)
    return latest


def get_latest_frame(folder):
    """Get the most recent frame from the given folder (most recent frame in trial)."""
    try:
        files = glob.glob(os.path.join(folder, "*.jpg"))
        g = max(
            files,
            key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split("_")[-1]),
        )
    except ValueError:
        time.sleep(0.005)
        files = glob.glob(os.path.join(folder, "*.jpg"))
        g = max(
            files,
            key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split("_")[-1]),
        )
    return g


def retry_frame_grab(path, max_wait=0.006, sleep_time=0.0005):
    deadline = time.perf_counter() + max_wait
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    while img is None and time.perf_counter() < deadline:
        time.sleep(sleep_time)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return img


while True:
    # Wait for client request
    message = socket.recv_string()

    # get the latest folder
    current_folder = get_latest_folder(VIDEO_DIR)
    # get the most recent frame
    current_frame = get_latest_frame(current_folder)

    # get the trial num to send with the grayscale image
    trial_num = int(current_frame.split("/")[-1].split(".")[0].split("_")[-1])

    img = cv2.imread(current_frame, cv2.IMREAD_GRAYSCALE)

    if img is None:
        img = retry_frame_grab(current_frame)

        # append the frame number
    data = np.append(img.ravel(), trial_num).astype(np.uint32)

    # Send as raw bytes
    print("sending frame")
    socket.send(data.tobytes())
