from psychopy import visual, core
import threading
import zmq.utils.monitor as m
import nidaqmx
import time
import datetime
import pandas as pd

from real_spike.utils import *
from real_spike.utils.latency import COLUMN_NAMES

SOCKET_OPEN = True
STIM_LENGTH_TIME = 0.005
# for now, just assuming that we are only stimming one pattern per trial
TRIAL_NUMBER = 0

# TODO: need to create a dataframe to save out pattern/trial information to columns = ["trial_number", "stim_time (datetime.now())", "pattern",
# TODO: think about how to incorporate trial number, global number of patterns seen? increment every time you get







































































































































# TODO: fail safe for laser, power limits

COLUMN_NAMES = ["trial number", "stim time", "pattern"]
df = pd.DataFrame(
            data=None,
            columns=COLUMN_NAMES
        )

# mostly for stopping the process when "stop" is called in the TUI
def monitor_socket(monitor):
    """Monitors the socket sets global bool when socket has closed."""
    global SOCKET_OPEN
    global df
    print("Monitoring socket...")

    while True:
        try:
            event = m.recv_monitor_message(monitor)
            evt = event['event']
            if evt == zmq.EVENT_ACCEPTED:
                SOCKET_OPEN = True
            elif evt == zmq.EVENT_DISCONNECTED:
                SOCKET_OPEN = False
                # save the df
                df.to_pickle(f"./stim_data/experiment_{datetime.datetime.now()}.pkl")
                print("Exiting process")
        except zmq.error.ZMQError:
            break


if __name__ == "__main__":
    # connect to port to listen on
    address = "10.172.17.107"
    port = 5559
    context = zmq.Context()
    sub = context.socket(zmq.PULL)
    sub.connect(f"tcp://{address}:{port}")
    print(f"Connected socket to address {address} on port {port}")

    # Setup monitoring on the socket
    monitor = sub.get_monitor_socket()
    threading.Thread(target=monitor_socket, args=(monitor,), daemon=True).start()

    # open a blank screen
    win = visual.Window(size=[1_000, 1_000],
                        screen=0,
                        fullscr=False, # will need to flip this to True during actual experiments
                        color='gray',
                        units='pix')

    # hide the cursor
    win.mouseVisible = False

    win.flip()

    while SOCKET_OPEN:
        buff = get_buffer(sub)

        if buff is not None:
            # Deserialize the buffer into a NumPy array
            data = np.frombuffer(buff, dtype=np.float64)

            # TODO: will need to update with the actual pattern size we are using
            data = data.reshape(13, 13).astype(np.float32)

            # increment trial number
            TRIAL_NUMBER += 1

            image_data = data * 2 - 1  # 0 becomes -1, 1 becomes +1

            # Convert to RGB by stacking the grayscale 3 times
            image_rgb = np.stack([image_data] * 3, axis=-1)

            # Create ImageStim
            stim = visual.ImageStim(win, image=image_rgb, size=win.size)

            stim.draw()
            win.flip()

            # TODO: send analog voltage via NIDAQ to trigger laser
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan("Dev1/ao1")

                stim_time = datetime.datetime.now()
                task.write(5.0)

                # hold pattern for stim length time
                time.sleep(STIM_LENGTH_TIME)

                task.write(0.0)

            # only hold the pattern for small period
            core.wait(0.25)
            # Clear screen
            win.flip()

            # save out all the things
            df.loc[len(df.index)] = [TRIAL_NUMBER, stim_time, data]

    win.close()
    core.quit()