"""Small script for making requests to the server. Repeatedly make requests and measure the round trip time across the
network. Use the RTT / 2 as a proxy for the average network latency. Client = pattern display computer."""

import zmq
import pandas as pd
import time
import os
import datetime
from tqdm import tqdm

df = pd.DataFrame(columns=["request_num", "RTT"])

# make a zmq REQ
address = "10.172.69.230"
port = 5558

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f"tcp://{address}:{port}")

print(f"Connected socket to address {address} on port {port}")

for i in tqdm(range(5_000)):
    request_message = b"Hello"
    # send request
    t = time.perf_counter_ns()
    socket.send(request_message)

    # Get the reply
    message = socket.recv()
    t2 = time.perf_counter_ns()

    df.loc[len(df.index)] = [i, (t2 - t) / 1e6]

print("finished requesting")

# save dataframe
parent_dir = os.path.dirname(os.path.abspath(__file__))
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
path = os.path.join(parent_dir, "timing", f"network-test_{timestamp}.pkl")

df.to_pickle(path)

