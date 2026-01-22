import zmq
import time

address = "localhost"
port_number = 5552

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(f"tcp://{address}:{port_number}")
print(f"Opened socket on {address}:{port_number}")

CUE_NUM = 0


for _ in range(4):
    time.sleep(10)
    print("Sending cue")
    socket.send_string(f"CUE_{CUE_NUM}")


print("done")
