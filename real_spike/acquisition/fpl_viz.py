import fastplotlib as fpl
import queue
import pickle

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import *

"----------------------------------------------------------------------------------------------------------------------"
# specify num channels to expect
NUM_CHANNELS = 150
# number of ms to display at one time
WINDOW = 10

# get the seeded median
#median = get_global_median()
median = np.load("/home/clewis/repos/realSpike/real_spike/acquisition/medians.npy")

# initialize a queue
viz_queue = queue.Queue(maxsize=5_000)

# connect to the viz actor via ZMQ
sub = connect(port_number=5557)

# initialize colors for each channel
COLORS = list()

for i in range(NUM_CHANNELS):
    # randomly select a color
    COLORS.append(np.append(np.random.rand(3), 1))
"----------------------------------------------------------------------------------------------------------------------"
# setup figure
rects = [
    (0, 0, 0.5, 1),  # for image1
    (0.5, 0, 0.5, 1),  # for image2
]

figure = fpl.Figure(rects=rects,
                    size=(1000, 900),
                    names=["filtered spikes", "raster"],
                    # controller_ids="sync"
                    )

for subplot in figure:
    subplot.axes.visible = False
    subplot.camera.maintain_aspect = False

"----------------------------------------------------------------------------------------------------------------------"
SAVED = False

def update():
    """Function to actual update the figure."""
    global viz_queue
    global figure

    # first 5ms
    if len(figure["filtered spikes"].graphics) == 0:
        # first data, fetch 5 chunks
        data = list()
        for _ in range(10):
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
            lg[i].data[:, 1] = data[i]

    # get the spike times
    ixs, _ = get_spike_events(data, median)


    # color each spike event orange
    for i in range(len(ixs)):
        if ixs[i].shape[0] == 0:
            continue
        lg[i].colors[ixs[i]] = "orange"

    # make a raster plot using the pre-defined channel colors
    spikes, colors = make_raster(ixs, COLORS)
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

    buff = get_buffer(sub)
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
    if viz_queue.qsize() != 0 and i > 2:
        update()

figure.show()

figure.add_animations(update_figure)

if __name__ == "__main__":
    fpl.loop.run()