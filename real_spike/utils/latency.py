from typing import List
import pandas as pd
import time

COLUMN_NAMES = ["frame number", "latency"]

class LatencyLogger:
    def __init__(self,
                 name: str,
                 max_size: int | None = None,
                 columns: List[str] = None):
        """
        Parameters
        ----------
        name: str
            name of the logger, typically the actor the latency is being calculated for
        max_size: int, default 1_000
            maximum number of frames to log
        columns: list[str], default ['frame number', 'latency']
            names of columns to log, typically only calculated one latency for entire actor
        """
        self.name = name

        if columns is None:
            columns = COLUMN_NAMES
        else:
            # check to make sure frame number as first element
            if "frame number" not in columns:
                columns.insert(0, "frame number")

        self.df = pd.DataFrame(
            data=None,
            columns=columns
        )

        if max_size is not None:
            self.max_size = max_size
        else:
            self.max_size = 1000

    def add(self, frame_number: int, latency: float | List[float]):
        """Add a latency to the dataframe"""
        # exceeded maximum number of frame entries
        if frame_number > self.max_size:
            return

        if type(latency) == float:
            self.df.loc[len(self.df.index)] = [int(frame_number), latency]
        else:
            self.df.loc[len(self.df.index)] = [int(frame_number),  *latency]

    def save(self):
        """Save the dataframe."""
        # when stop is called in the actors, safe the df to disk
        self.df.to_pickle(f"./latency/{self.name}_latency_{time.strftime("%Y%m%d-%H%M%S")}.pkl")

