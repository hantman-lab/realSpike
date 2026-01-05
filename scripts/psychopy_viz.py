from psychopy import visual, core, event
import threading
import nidaqmx
import time
import datetime
import pandas as pd
import zmq
import zmq.utils.monitor as m
import numpy as np


COLUMN_NAMES = ["trial number", "frame number", "time"]


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

    def log(
        self,
        trial_number: int,
        frame_number: int | None,
        log_time: float,
        experiment_condition: np.ndarray,
    ):
        """Add a latency to the dataframe"""

        # save the recorded pattern/fiber position sent and the time sent
        self.df.loc[len(self.df.index)] = [
            int(trial_number),
            frame_number,
            log_time,
            experiment_condition,
        ]

    def save(self):
        """Save the dataframe to disk."""
        self.df.to_pickle(
            f"./timing/{self.name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
        )


"----------------------------------------------------------------------------------------------------------------------"

SOCKET_OPEN = True
STIM_LENGTH_TIME = 0.005
# for now, just assuming that we are only stimming one pattern per trial
TRIAL_NUMBER = 0

LAST_STIM = time.time()

pattern_logger = TimingLogger("test-psychopy")


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
        size=[800, 800],
        screen=0,
        fullscr=False,  # will need to flip this to True during actual experiments
        color="black",
        units="pix",
        checkTiming=False,
    )

    # hide the cursor
    win.mouseVisible = False

    while SOCKET_OPEN:
        # try to get from zmq buffer
        buff = None
        try:
            buff = socket.recv(zmq.NOBLOCK)
        except zmq.Again:
            buff = None

        if buff is not None:
            # laser safety check
            t = time.time()
            if t - LAST_STIM <= 0.0025:
                print("Previous stim occurred less than 2.5ms second ago.")
            else:
                # Deserialize the buffer into a NumPy array
                data = np.frombuffer(buff, dtype=np.float64)
                print("Received stim data")

                # TODO: will need to update with the actual pattern size we are using
                # TODO: for behavior using a 2x2, for others might be a 4x4
                data = data.reshape(2, 2).astype(np.float32)

                image_data = data * 2 - 1  # 0 becomes -1, 1 becomes +1

                # Convert to RGB by stacking the grayscale 3 times
                image_rgb = np.stack([image_data] * 3, axis=-1)

                # Create ImageStim
                stim = visual.ImageStim(win, image=image_rgb, size=win.size)

                stim.draw()
                win.flip()
                t = time.perf_counter_ns()
                LAST_STIM = time.time()

                # TODO: get the time during when the laser is put to on so it is most accurate
                # for now, right after showing the pattern, log the pattern
                pattern_logger.log(TRIAL_NUMBER, None, t, data)

                # TODO: send analog voltage via NIDAQ to trigger laser
                # with nidaqmx.Task() as task:
                #     task.ao_channels.add_ao_voltage_chan("Dev1/ao1")

                #     stim_time = time.time()
                #     task.write(5.0)

                #     # hold pattern for stim length time
                #     time.sleep(STIM_LENGTH_TIME)

                #     task.write(0.0)

                # pattern_logger.log(TRIAL_NUMBER, None, stim_time, data)
                TRIAL_NUMBER += 1  # assuming one stim per trial

                # only hold the pattern for small period
                core.wait(0.25)  # remove this when doing the actual laser
                # Clear screen
                win.flip()

    win.close()
    core.quit()
