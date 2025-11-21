import queue

import fastplotlib as fpl
import numpy as np

import zmq

"------------------------------------------------------------"
# zmq stuff
def connect(address: str = "127.0.0.1", port_number: int = 5558):
    """
    Connect to the pattern generator actor via zmq. Make sure that ports match and are different from visual
    actor ports.
    """
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, b"")

    # address must match publisher in actor
    sub.connect(f"tcp://{address}:{port_number}")

    print(f"Made connection on port {port_number} at address {address}")

    return sub


def get_buffer(sub):
    """Gets the buffer from the publisher."""
    try:
        b = sub.recv(zmq.NOBLOCK)
    except zmq.Again:
        pass
    else:
        return b

    return None

"------------------------------------------------------------"
# define reshape size
RESHAPE_SIZE = (290, 448)

# connect to the viz actor via ZMQ
sub = connect(port_number=5557)

"------------------------------------------------------------"

# setup figure
figure = fpl.Figure(size=(1_000, 600),
                names=["side"])

for sp in figure:
    sp.axes.visible = False
    sp.camera.local.scale_y *= -1

IMAGE = None

"------------------------------------------------------------"
i = 0

def update_figure(p):
    """Fetch the data from the socket, deserialize it, and put it in the queue for visualization."""
    global IMAGE
    global i

    buff = get_buffer(sub)
    if buff is not None:
        # Deserialize the buffer into a NumPy array
        data = np.frombuffer(buff, dtype=np.uint64)
        data = data[:-1]

        data = data.reshape(*RESHAPE_SIZE)

        if IMAGE is None:
            IMAGE = figure["side"].add_image(data, cmap="gray")
            figure["side"].auto_scale()
        else:
            IMAGE.data = data
        i += 1


figure.show()

figure[0, 0].add_animations(update_figure)

if __name__ == "__main__":
    fpl.loop.run()