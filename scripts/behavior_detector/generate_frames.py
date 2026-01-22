"""Script for sending most recent frame saved to disk. Place on the bias computer."""

import os
import glob
import numpy as np
import zmq
import cv2

# TODO: replace with path on bias computer
VIDEO_DIR = "/home/clewis/repos/holo-nbs/data/videos/test/side/"

# TODO: replace with netgear ip address
ip_address = "192.168.0.102"
ip_address = "localhost"
port = 4147

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


def get_latest_frame(folder):
    """Get the most recent frame from the given folder (most recent frame in trial)."""
    files = glob.glob(os.path.join(folder, "*.jpg"))
    return max(
        files,
        key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split("_")[-1]),
    )


"-----------------------------------------------------------------------------------------------------"

while True:
    # Wait for client request
    message = socket.recv_string()

    # get the latest folder
    current_folder = get_latest_folder(VIDEO_DIR)
    # get the most recent frame
    current_frame = get_latest_frame(current_folder)

    # get the trial num to send with the grayscale image
    trial_num = int(current_frame.split("/")[-1].split(".")[0].split("_")[-1])

    # convert to gray scale
    img = cv2.imread(current_frame, cv2.IMREAD_GRAYSCALE)

    data = np.append(img.ravel(), trial_num).astype(np.uint32)

    socket.send(data.tobytes())
