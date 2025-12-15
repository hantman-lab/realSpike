#import real_spike as rsp

import fastplotlib as fpl
import queue
#import zmq
import numpy as np


# specify num channels to expect
NUM_CHANNELS = 150
# number of ms to display at one time
WINDOW = 10

# get the seeded median
#median = get_global_median()
median = np.load("/home/clewis/repos/realSpike/real_spike/acquisition/medians.npy")

# initialize a queue
viz_queue = queue.Queue(maxsize=5_000)

# # connect to the viz actor via ZMQ
# context = zmq.Context()
# sub = context.socket(zmq.PULL)
# address = "localhost"
# port_number = 5557
#
# # address must match publisher in actor
# sub.connect(f"tcp://{address}:{port_number}")
#
# print(f"Made connection on port {port_number} at address {address}")

# initialize colors for each channel
COLORS = np.random.rand(NUM_CHANNELS, 4) # [n_colors, rgba] array
COLORS[:, -1] = 1 # set alpha = 1
"----------------------------------------------------------------------------------------------------------------------"
# setup figure
figure = fpl.Figure(shape=(1, 2),
                    size=(1500, 900),
                    names=["filtered spikes", "raster"],
                    # controller_ids="sync"
                    )

for subplot in figure:
    subplot.axes.visible = False
    subplot.camera.maintain_aspect = False

"----------------------------------------------------------------------------------------------------------------------"


def update():
    """Function to actual update the figure."""
    global viz_queue
    global figure

    # first 5ms
    if len(figure["filtered spikes"].graphics) == 0:
        # first data, fetch 5 chunks
        data = list()
        for _ in range(30):
            data.append(viz_queue.get())
        # concat chunks together and add to viz
        data = np.concatenate(data, axis=1)
        lg = figure["filtered spikes"].add_line_stack(data,
                                                      colors="gray",
                                                      thickness=0.5,
                                                      separation=35,
                                                      name="lg")
    # shift left 1ms and add new chunk
    else:
        # get the current graphic
        lg = figure["filtered spikes"]["lg"]
        # reset the colors
        lg.colors = "gray"

        # fetch 1ms chunk and shift
        chunk = viz_queue.get()

        # get the current data, most recent 4ms
        data = lg.data[30:, 1]

        # concatenate the new chunk to create a 5ms chunk again
        data = np.concatenate([data, chunk], axis=1)

        # update the y-values of the existing data
        for i in range(lg.data[:].shape[0]):
            # lg[i].data[:-30, 1] = lg[i].data[30:, 1]
            # lg[i].data[-30:, 1] = chunk[i]
            lg[i].data[:, 1] = data[i]

        # set first 40 indices using most recent 4ms lg[i].data[:40, 1] = lg[i].data[10:, 1]
        # set last 10 indices using most recent 1ms lg[i].data[40:, 1] = chunk

    # get the spike times
    ixs, _ = rsp.get_spike_events(data, median)


    # color each spike event orange
    for i in range(len(ixs)):
        if ixs[i].shape[0] == 0:
            continue
        lg[i].colors[ixs[i]] = "orange"

    # make a raster plot using the pre-defined channel colors
    spikes, colors = rsp.make_raster(ixs, COLORS)
    spikes = np.concatenate(spikes)

    # clear the old raster plot
    figure["raster"].clear()

    # add new raster
    figure["raster"].add_scatter(spikes, sizes=3, colors=colors)


i = 0

def update_figure(p):
    """Fetch the data from the socket, deserialize it, and put it in the queue for visualization."""
    global viz_queue
    global i
    buff = None

    # try:
    #     buff = sub.recv(zmq.NOBLOCK)
    # except zmq.Again:
    #     pass

    if buff is not None:
        i += 1
        # Deserialize the buffer into a NumPy array
        data = np.frombuffer(buff, dtype=np.float64)

        data = data.reshape(NUM_CHANNELS, 150)

        # split the data into 1ms chunks instead of a single 5ms
        # allows for circular buffer to shift the data stream
        datas = np.split(data, 5, axis=1)

        # put the data in the queue
        for chunk in datas:
            viz_queue.put(chunk)

    # as long as there is something in the queue, update the viz
    if viz_queue.qsize() != 0 and i > 6:
        update()

figure.show()

#figure.add_animations(update_figure)

if __name__ == "__main__":
    fpl.loop.run()