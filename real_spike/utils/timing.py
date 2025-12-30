import pandas as pd
import numpy as np
from datetime import datetime

COLUMN_NAMES = ["trial number", "frame number", "time", "pattern"]


class TimingLogger:
    def __init__(self, name: str):
        """
        Parameters
        ----------
        name: str
            name of the logger, typically the name you want the timings saved under (e.g. rb50)
        """
        self.name = name

        self.df = pd.DataFrame(data=None, columns=COLUMN_NAMES)

    def log(self, trial_number: int, frame_number: int, time: str, pattern: np.ndarray):
        """Add a latency to the dataframe"""

        # save the recorded pattern sent and the time sent
        self.df.loc[len(self.df.index)] = [
            int(trial_number),
            int(frame_number),
            time,
            pattern,
        ]

    def save(self):
        """Save the dataframe to disk."""
        self.df.to_pickle(
            f"./timing/{self.name}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.pkl"
        )
