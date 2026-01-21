"""Put onto bias computer. Make sure to run this file first and then check_crop.py."""

import zmq
import cv2

# TODO: copy and paste path to desired image here
PATH = "/home/clewis/repos/holo-nbs/data/videos/test/side/v001/image_615.jpg"

# TODO: update with netgear ip_address
ip_address = "localhost"
port = 5555

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{ip_address}:{port}")
print(f"ZMQ REQ/REP server listening on port {port}")


# Wait for client request
message = socket.recv_string()
print("Received message:", message)

img = cv2.imread(PATH, cv2.IMREAD_GRAYSCALE)


# Send as raw bytes
print("sending frame")
socket.send(img.ravel().tobytes())
