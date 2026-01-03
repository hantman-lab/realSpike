import pandas as pd

COLUMN_NAMES = ["trial number", "frame number", "latency"]


class LatencyLogger:
    def __init__(self, name: str, max_size: int | None = None):
        """
        Parameters
        ----------
        name: str
            name of the logger, typically the actor the latency is being calculated for
        max_size: int, default 1_000
            maximum number of frames to log
        """
        self.name = name

        self.df = pd.DataFrame(data=None, columns=COLUMN_NAMES)

        if max_size is not None:
            self.max_size = max_size
        else:
            self.max_size = 5_000

    def add(self, trial_number: int | None, frame_number: int, latency: float):
        """Add a latency to the dataframe"""
        # exceeded maximum number of frame entries
        if frame_number > self.max_size:
            return

        # save the recorded latency in ms
        self.df.loc[len(self.df.index)] = [
            trial_number,
            int(frame_number),
            latency / 1e6,
        ]

    def save(self):
        """Save the dataframe to disk."""
        self.df.to_pickle(f"./latency/{self.name}_latency.pkl")
