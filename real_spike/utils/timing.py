import pandas as pd
import numpy as np
from datetime import datetime

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
        time: float,
        experiment_condition: np.ndarray,
    ):
        """Add a latency to the dataframe"""

        # save the recorded pattern/fiber position sent and the time sent
        self.df.loc[len(self.df.index)] = [
            int(trial_number),
            int(frame_number),
            time,
            experiment_condition,
        ]

    def save(self):
        """Save the dataframe to disk."""
        self.df.to_pickle(
            f"./timing/{self.name}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.pkl"
        )
