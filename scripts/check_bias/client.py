"""File with functionality that should be integrated into behavior detector pipeline for the FrameGrabber actor."""

import zmq
import fastplotlib as fpl
import numpy as np
import pandas as pd
import time
from tqdm import tqdm
import os
import datetime

RESHAPE_SIZE = (224, 448)

# for timing purposes
df = pd.DataFrame(columns=["request_num", "RTT"])

# TODO: update these with netgear stuff
ip_address = "localhost"
port = 5555

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f"tcp://{ip_address}:{port}")
socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
print(f"Connected to ZMQ server at {ip_address} on port {port}")

figure = fpl.Figure(size=(800, 600))

image = figure[0, 0].add_image(np.random.rand(*RESHAPE_SIZE))

figure.show()

figure[0, 0].axes.visible = False

if __name__ == "__main__":
    fpl.loop.run()

    for i in tqdm(range(1_000)):
        t = time.perf_counter_ns()
        socket.send_string("fetch()")
        data = socket.recv()  # Receive one full frame
        t2 = time.perf_counter_ns()

        df.loc[len(df.index)] = [i, (t2 - t) / 1e6]
        i += 1

        frame = np.frombuffer(data, dtype=np.uint8).reshape(RESHAPE_SIZE)

        # update image
        image.data = frame

    # save dataframe
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(parent_dir, "timing", f"bias-network-test_{timestamp}.pkl")

    df.to_pickle(path)
