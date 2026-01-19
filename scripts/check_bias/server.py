"""File that should be placed on the same machine as bias camera system."""

import os
import glob
import time
import zmq

# TODO: update this with the base directory that jpeg folders for each trial will go to
VIDEO_DIR = "./"

# TODO: also update this with the netgear stuff
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
    files = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    if not files:
        return None
    return files[-1]


while True:
    # Wait for client request
    message = socket.recv_string()

    latest_folder = get_latest_folder(VIDEO_DIR)
    if latest_folder != current_folder:
        current_folder = latest_folder

    if current_folder is None:
        continue

    # Get the most recent frame
    current_frame = get_latest_frame(current_folder)
    if current_frame is None:
        continue

    # Read frame bytes
    with open(current_frame, "rb") as f:
        data = f.read()

    # Send as raw bytes
    socket.send(data)
