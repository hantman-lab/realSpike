import shutil

import zmq
import os
from pathlib import Path
import time
from real_spike import LazyVideo
import cv2

VIDEOS = list(
    Path("/home/clewis/wasabi/reaganbullins2/ProjectionProject/rb69/20260224/").glob(
        "*side*.avi"
    )
)
print(len(VIDEOS))

VIDEOS.sort()

OUTPUT_PATH = Path("/home/clewis/repos/holo-nbs/data/videos/test/side2/")

# empty output dir
print("removing directory")
for item_name in os.listdir(OUTPUT_PATH):
    item_path = os.path.join(OUTPUT_PATH, item_name)
    shutil.rmtree(item_path)  # Remove the file or link


address = "localhost"
port = 5552

context = zmq.Context()
cue_socket = context.socket(zmq.SUB)
cue_socket.setsockopt(zmq.SUBSCRIBE, b"")
cue_socket.connect(f"tcp://{address}:{port}")


def generate_video(path):
    out = OUTPUT_PATH.joinpath(path.stem.split("_")[-1])
    if not os.path.exists(out):
        os.mkdir(out)
    print(out)
    vid = LazyVideo(path)
    for j in range(501, 903, 3):
        d = vid[j]
        img_bgr = cv2.cvtColor(d, cv2.COLOR_RGB2BGR)
        cv2.imwrite(out.joinpath(f"image_{j}.jpg"), img_bgr)
        time.sleep(0.002)


ix = 0

while True:
    try:
        buff = cue_socket.recv(zmq.NOBLOCK)
    except zmq.Again:
        buff = None

    # cue received
    if buff is not None:
        generate_video(VIDEOS[ix])

        ix += 1
