import numpy as np
import zmq
from pathlib import Path
import cv2

FOLDER = Path("/home/clewis/repos/holo-nbs/data/videos/test/side")

all_folders = list(FOLDER.glob("*"))

folder_index = 0
frame_index = 501


ip_address = "localhost"
port = 4147

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")


while True:
    # Wait for client request
    message = socket.recv_string()

    if frame_index > 852:
        folder_index += 1
        if folder_index >= len(all_folders):
            print("done")
            socket.close()
            break
        frame_index = 501
        print("new trial")

    path = all_folders[folder_index].joinpath(f"image_{frame_index}.jpg")

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    # append the frame number
    data = np.append(img.ravel(), frame_index).astype(np.uint32)

    socket.send(data.tobytes())

    frame_index += 3
