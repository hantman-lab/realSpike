"""Small test script to run on improv computer that responds to requests by sending a random pattern back.
Helps to measure round trip latency of the netgear switch."""

import zmq
import numpy as np


# make a zmq REP
address = "10.172.6.138"
port = 5559

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://{address}:{port}")
print(f"Server listening on port {port}...")

while True:
    # Wait for the next request from the client
    message = socket.recv()

    # Send the reply back to the client
    data = np.random.rand(13, 13).ravel()
    socket.send(data.tobytes())
