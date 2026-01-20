"""File with functionality that should be integrated into behavior detector pipeline for the FrameGrabber actor."""

import zmq
import pandas as pd
import time
from tqdm import tqdm
import numpy as np
import os
import datetime

RESHAPE_SIZE = (290, 448)

# for timing purposes
df = pd.DataFrame(columns=["request_num", "RTT"])

# TODO: update these with netgear stuff
ip_address = "localhost"
port = 5555

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f"tcp://{ip_address}:{port}")
print(f"Connected to ZMQ server at {ip_address} on port {port}")


if __name__ == "__main__":
    for i in tqdm(range(8_00)):
        t = time.perf_counter_ns()
        print("requesting frame")
        socket.send_string("fetch()")
        data = socket.recv()  # Receive one full frame
        t2 = time.perf_counter_ns()

        df.loc[len(df.index)] = [i, (t2 - t) / 1e6]
        i += 1

        data = np.frombuffer(data, dtype=np.uint32)
        frame_num = data[-1]
        print(frame_num)
        frame = data[:-1].reshape(RESHAPE_SIZE)

    # save dataframe
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(parent_dir, f"bias-network-test_{timestamp}.pkl")

    df.to_pickle(path)
