import time
import numpy as np
import zmq
import cv2
import os
import glob

VIDEO_DIR = "/home/clewis/repos/holo-nbs/data/videos/test/side2"


ip_address = "localhost"
port = 4148

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")

EOI = b"\xff\xd9"  # JPEG end-of-image marker
SOI = b"\xff\xd8"  # JPEG start-of-image marker

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
    for _ in range(2):
        for path in paths:
            img = try_to_read_frame(path)
            if img is not None:
                return img, path
        time.sleep(0.0005)
    return None, None


def try_to_read_frame(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return None

        # Quick structural checks to avoid decoding partial files
    if len(data) < 4 or (not data.startswith(SOI)) or (not data.endswith(EOI)):
        return None

    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    return img


while True:
    # Wait for client request
    message = socket.recv_string()

    # get the latest folder
    current_folder = get_latest_folder(VIDEO_DIR)
    trial_num = int(current_folder.split("v")[-1]) - 1
    # get the most recent frame
    most_recent_frames = get_latest_frames(current_folder)
    while len(most_recent_frames) < 3:
        most_recent_frames = get_latest_frames(current_folder)
    current_frame = most_recent_frames[0]

    # get the trial num to send with the grayscale image
    frame_num = int(current_frame.split("/")[-1].split(".")[0].split("_")[-1])

    # convert to gray scale
    img = try_to_read_frame(current_frame)

    # sometimes the most recent frame is one that is still being written
    # just want to buffer for a second and try to get it again
    if img is None:
        img, path = retry_frame_grab(most_recent_frames)
        frame_num = int(path.split("/")[-1].split(".")[0].split("_")[-1])

    # if still image is none just skip
    if img is None:
        print(f"IMAGE IS STILL NONE, frame {frame_num}")
        img = np.zeros((290, 448))

    data = np.append(img.ravel(), trial_num).astype(np.uint32)
    data = np.append(data, frame_num).astype(np.uint32)

    socket.send(data.tobytes())
