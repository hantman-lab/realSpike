import pandas as pd
import numpy as np
from datetime import datetime

COLUMN_NAMES = ["trial number", "frame number", "time"]
BEHAVIOR_COLUMNS = ["trial number", "frame number"]


class TimingLogger:
    def __init__(self, name: str, experiment_type: str = "holography"):
        """
        Parameters
        ----------
        name: str
            name of the logger, typically the name you want the timings saved under (e.g. rb50)
        experiment_type: str, default 'holography'
            type of experiment, either 'holography' or 'fiber'
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
        time: float | str,
        experiment_condition: np.ndarray,
    ):
        """Add a pattern send to the dataframe"""

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
            f"./timing/{self.name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
        )


class BehaviorLogger:
    def __init__(self, name: str, behavior: str = "lift"):
        """
        Parameters
        ----------
        name: str
            name of the logger, typically the name you want the timings saved under (e.g. rb50)
        behavior: str, default 'lift'
            behavior being detected, one of 'lift' or 'grab'
        """
        self.name = name

        if behavior not in ["lift", "grab"]:
            raise ValueError(f"Behavior must be one of 'lift', 'grab', not {behavior}.")

        self.behavior = behavior

        self.df = pd.DataFrame(data=None, columns=BEHAVIOR_COLUMNS)

    def log(
        self,
        trial_number: int,
        frame_number: int | str,
    ):
        """Add a behavior detection to the dataframe"""

        # save the recorded pattern/fiber position sent and the time sent
        self.df.loc[len(self.df.index)] = [
            int(trial_number),
            frame_number,
        ]

    def save(self):
        """Save the dataframe to disk."""
        self.df.to_pickle(
            f"./behavior/{self.behavior}_{self.name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
        )
