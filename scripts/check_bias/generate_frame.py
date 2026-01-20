"""Use this file when working on the same system. Streaming locally. File will generate frames at 500Hz."""

import os
import glob
import numpy as np
import zmq
import cv2

VIDEO_DIR = "/home/clewis/repos/holo-nbs/data/videos/test/side/"

ip_address = "localhost"
port = 5555

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")

current_folder = None
current_frame = None


def get_latest_folder(base_dir):
    subdirs = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    if not subdirs:
        return None
    latest = max(subdirs, key=os.path.getmtime)
    return latest


def get_latest_frame(folder):
    files = glob.glob(os.path.join(folder, "*.jpg"))
    if not files:
        return None

    return max(
        files,
        key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split("_")[-1]),
    )


while True:
    # Wait for client request
    message = socket.recv_string()
    print("Received message:", message)

    latest_folder = get_latest_folder(VIDEO_DIR)
    if latest_folder != current_folder:
        current_folder = latest_folder

    if current_folder is None:
        continue

    # Get the most recent frame
    current_frame = get_latest_frame(current_folder)
    if current_frame is None:
        continue

    # get the trial num to send with the grayscale image
    trial_num = int(current_frame.split("/")[-1].split(".")[0].split("_")[-1])

    img = cv2.imread(current_frame, cv2.IMREAD_GRAYSCALE)

    # append the frame number
    data = np.append(img.ravel(), trial_num).astype(np.uint32)

    # Send as raw bytes
    print("sending frame")
    socket.send(data)
