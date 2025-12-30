from psychopy import visual, core, event
import threading
import nidaqmx
import time
import datetime
import pandas as pd
import os 
import zmq
import zmq.utils.monitor as m
import numpy as np


SOCKET_OPEN = True
STIM_LENGTH_TIME = 0.005
# for now, just assuming that we are only stimming one pattern per trial
TRIAL_NUMBER = 0

LAST_STIM = time.time()

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
                df.to_pickle(f"./experiment_{datetime.datetime.now()}.pkl")
                print("Exiting process")
        except zmq.error.ZMQError:
            break


if __name__ == "__main__":
    # connect to port to listen on
    address = "localhost"
    port = 5559
    
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    socket.connect(f"tcp://{address}:{port}")
    
    print(f"Connected socket to address {address} on port {port}")

    # Setup monitoring on the socket
    monitor = socket.get_monitor_socket()
    threading.Thread(target=monitor_socket, args=(monitor,), daemon=True).start()

    # open a blank screen
    win = visual.Window(size=[800, 800],
                        screen=0,
                        fullscr=False, # will need to flip this to True during actual experiments
                        color='black',
                        units='pix',
                        checkTiming=False)

    # hide the cursor
    win.mouseVisible = False

    while SOCKET_OPEN:
        # laser safety check
        t = time.time()
        if LAST_STIM - t <= 1: 
            print("Previous stim occurred less than 1 second ago.")
            LAST_STIM = t
            time.sleep(1)
             
        # try to get from zmq buffer 
        buff = None 
        try: 
            buff = socket.recv(zmq.NOBLOCK)
        except zmq.Again:
            buff = None 

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
            # with nidaqmx.Task() as task:
            #     task.ao_channels.add_ao_voltage_chan("Dev1/ao1")

            #     stim_time = datetime.datetime.now()
            #     task.write(5.0)

            #     # hold pattern for stim length time
            #     time.sleep(STIM_LENGTH_TIME)

            #     task.write(0.0)

            # only hold the pattern for small period
            core.wait(0.25)
            # Clear screen
            win.flip()

            # save out all the things
            # df.loc[len(df.index)] = [TRIAL_NUMBER, stim_time, data]

    win.close()
    core.quit()