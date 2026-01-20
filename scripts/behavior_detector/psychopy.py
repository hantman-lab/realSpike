from psychopy import visual, core, event
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
import zmq
import zmq.utils.monitor as m
import threading

COLUMN_NAMES = ["trial number"]


class TimingLogger:
    def __init__(self, name: str, experiment_type: str = "holography"):
        """
        Parameters
        ----------
        name: str
            name of the logger, typically the name you want the timings saved under (e.g. rb50)
        """
        self.name = name

        if experiment_type not in ["holography", "fiber"]:
            raise ValueError(
                f"Experiment type must be one of 'holography', 'fiber', not {experiment_type}."
            )

        if experiment_type == "holography":
            COLUMN_NAMES.append("pattern")
        else:
            COLUMN_NAMES.append("position")

        self.df = pd.DataFrame(data=None, columns=COLUMN_NAMES)
        print(self.df)

    def log(
        self,
        trial_number: int,
        experiment_condition: np.ndarray,
    ):
        """Add a latency to the dataframe"""

        # save the recorded pattern/fiber position sent and the time sent
        self.df.loc[len(self.df.index)] = [
            int(trial_number),
            experiment_condition,
        ]

    def save(self):
        """Save the dataframe to disk."""
        parent_dir = Path(__file__).parents[0]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = parent_dir.joinpath(f"{self.name}_{timestamp}.pkl")
        self.df.to_pickle(path)


"----------------------------------------------------------------------------------------------------------------------"

# for now, just assuming that we are only stimming one pattern per trial
TRIAL_NUMBER = 0
SOCKET_OPEN = True

# TODO: Change path as needed
patterns = np.load("/home/clewis/repos/holo-nbs/experiment_data/preset_patterns.npy")

pattern_logger = TimingLogger("test-psychopy")


# TODO: update these values as needed
# mostly for stopping the process when "stop" is called in the TUI
def monitor_socket(monitor):
    """Monitors the socket sets global bool when socket has closed."""
    global SOCKET_OPEN
    print("Monitoring socket...")

    while True:
        try:
            event = m.recv_monitor_message(monitor)
            evt = event["event"]
            if evt == zmq.EVENT_ACCEPTED:
                SOCKET_OPEN = True
            elif evt == zmq.EVENT_DISCONNECTED:
                SOCKET_OPEN = False
                pattern_logger.save()
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
    win = visual.Window(
        size=[1280, 1280],
        screen=0,
        fullscr=False,  # TODO: will need to flip this to True during actual experiments
        color="black",
        units="pix",
        checkTiming=False,
    )

    # hide the cursor
    win.mouseVisible = False

    # initiate a black screen to start
    win.flip()

    # 320 pixels per 2mm
    px_per_cell = 160

    while SOCKET_OPEN:
        # try to get from zmq buffer
        buff = None
        try:
            buff = socket.recv(zmq.NOBLOCK)
        except zmq.Again:
            buff = None

        if buff is not None:
            print(f"CUE RECEIVED, TRIAL NUMBER: {TRIAL_NUMBER}")
            img = patterns[TRIAL_NUMBER].reshape(2, 2)
            img = 2 * img - 1
            stim = visual.ImageStim(
                win,
                image=img,
                size=(2 * px_per_cell, 2 * px_per_cell),
                units="pix",
                interpolate=False,  # VERY IMPORTANT
            )
            # need to put the stim in the top right corner for flip by DMD
            win_width, win_height = win.size
            stim.pos = (
                -win_width / 2 + stim.size[0] / 2,
                win_height / 2 - stim.size[1] / 2,
            )

            stim.draw()
            win.flip()

            print(patterns[TRIAL_NUMBER].reshape(2, 2))
            pattern_logger.log(TRIAL_NUMBER, patterns[TRIAL_NUMBER])
            TRIAL_NUMBER += 1
