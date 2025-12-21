import fastplotlib as fpl
import queue
import numpy as np 
import zmq 
import scipy 

"----------------------------------------------------------------------------------------------------------------------"
# define utility functions 
def get_spike_events(data: np.ndarray, median: np.ndarray, num_dev: int = 5):
    """
    Use the MAD to calculate spike times num_dev above and below the provided median.

    Parameters
    ----------
    data: np.ndarray 
        Array representing channels x time 
    median: np.ndarray 
        1D array representing the median value for each channel 
    num_dev: int, default 5
        Number of MAD deviations to threshold spikes above and below the median 
    """
    # validate data
    if data.ndim != 2:
        raise ValueError(f"Data passed in must be (channels, time). You have paased in an array of dim {data.ndim}.")
    # validate median 
    if data.shape[0] != median.shape[0]:
        raise ValueError(f"Number of channels in data array must match number of median values provided. Data shape: {data.shape[0]} != Median shape: {median.shape[0]}")

    # calculate mad
    mad = scipy.stats.median_abs_deviation(data, axis=1)

    # Calculate threshold
    thresh = (num_dev * mad) + median

    # Vectorized computation of absolute data
    abs_data = np.abs(data)

    # Find indices where threshold is crossed for each channel
    spike_indices = [np.where(abs_data[i] > thresh[i])[0] for i in range(data.shape[0])]

    spike_counts = [np.count_nonzero(arr) for arr in spike_indices]

    return spike_indices, spike_counts


def make_raster(ixs, COLORS):
    """
    Takes a list of threshold crossings and returns a list of points (channel number, spike time) and colors.
    Used to make a raster plot.
    """
    spikes = list()

    for i, ix in enumerate(ixs):
        ys = np.full(ix.shape, i * 35)
        sp = np.vstack([ix, ys]).T
        spikes.append(sp)

    colors = list()

    for j, i in enumerate(spikes):
        # randomly select a color
        c = [COLORS[j]] * len(i)
        colors += c

    return spikes, np.array(colors)


"----------------------------------------------------------------------------------------------------------------------"
# data configurations: fetching 1ms of data at a time for 150 channels
NUM_CHANNELS = 150
NUM_SAMPLES = 30

# init colors 
COLORS = np.random.rand(NUM_CHANNELS, 4) # [n_colors, rgba] array
COLORS[:, -1] = 1 # set alpha = 1

# queue for the viz 
viz_queue = queue.Queue(5_000)

"----------------------------------------------------------------------------------------------------------------------"
# load in a saved median from disk 
median = np.load("/home/clewis/repos/realSpike/real_spike/stream_data/median.npy")

"----------------------------------------------------------------------------------------------------------------------"
# make zmq connection 
address = "localhost" 
port = 5557

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.SUBSCRIBE, b"")
socket.connect(f"tcp://{address}:{port}")

print(f"Made connection at {address} on port {port}")

"----------------------------------------------------------------------------------------------------------------------"
# make the figure
figure = fpl.Figure(shape=(1, 2),
                    size=(1000, 900),
                    names=["filtered spikes", "raster"],
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
        # need to have 30 ms before stream continue
        if viz_queue.qsize() != 30:
            return 
        print("init graphic") 
        # first data, fetch 30 ms of data
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

        # get the current data, most recent ms of data
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
    figure["raster"].add_scatter(spikes, sizes=5, colors=colors)



def update_figure(p):
    """Fetch the data from the socket, deserialize it, and put it in the queue for visualization."""
    global viz_queue, update

    # try to get from zmq buffer 
    buff = None 
    try: 
        buff = socket.recv(zmq.NOBLOCK)
    except zmq.Again:
        buff = None 

    if buff is not None:
        # Deserialize the buffer into a NumPy array
        data = np.frombuffer(buff, dtype=np.float64)

        data = data.reshape(NUM_CHANNELS, NUM_SAMPLES)

        # put the data in the queue
        viz_queue.put(data)

    # as long as there is something in the queue, update the viz
    if viz_queue.qsize() != 0:
        update()

figure.show()

figure.add_animations(update_figure)

if __name__ == "__main__":
    fpl.loop.run()