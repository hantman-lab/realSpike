import zmq
import time

address = "localhost"
port_number = 5559

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(f"tcp://{address}:{port_number}")
print(f"Opened socket on {address}:{port_number}")

CUE_NUM = 0


for _ in range(20):
    time.sleep(2)
    print("Sending cue")
    socket.send_string(f"CUE_{CUE_NUM}")
    time.sleep(5)


print("done")
