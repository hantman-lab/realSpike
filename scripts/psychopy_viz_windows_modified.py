from psychopy import visual, core, event
import datetime
import pandas as pd
import numpy as np
import os
import serial

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
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(parent_dir, f"{self.name}_{timestamp}.pkl")
        self.df.to_pickle(path)


"----------------------------------------------------------------------------------------------------------------------"

# for now, just assuming that we are only stimming one pattern per trial
TRIAL_NUMBER = 0

# TODO: Change path as needed
patterns = np.load("/home/clewis/repos/holo-nbs/experiment_data/preset_patterns.npy")

pattern_logger = TimingLogger("test-psychopy")

# TODO: update these values as needed
port_name = "/dev/ttyACM0"
baud_rate = 9600  # Check your device's documentation for the correct baud rate

ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=1)


if __name__ == "__main__":
    # open a blank screen
    win = visual.Window(
        size=[800, 800],
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

    # TODO: update with ratio
    px_per_cell = 8

    # constantly poll the serial port
    while True:
        bytes_available = ser.in_waiting

        if bytes_available > 0:
            line = ser.readline().decode(errors="ignore").strip()
            if line == "1":
                print(f"CUE DETECTED, TRIAL NUMBER: {TRIAL_NUMBER}")
                img = patterns[TRIAL_NUMBER].reshape(2, 2)
                img = 2 * img - 1
                # need to flip upside down
                img = np.flipud(img)
                stim = visual.ImageStim(
                    win,
                    image=img,
                    size=win.size,
                    # size=(2 * px_per_cell, 2 * px_per_cell),
                    units="pix",
                    interpolate=False,  # VERY IMPORTANT
                )

                stim.draw()
                win.flip()

                pattern_logger.log(TRIAL_NUMBER, patterns[TRIAL_NUMBER])
                TRIAL_NUMBER += 1
