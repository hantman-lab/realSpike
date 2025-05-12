import pandas as pd
import time

COLUMN_NAMES = ["frame number", "latency"]

class Latency:
    def __init__(self, actor_name: str, max_frames: int | None = None):
        self.df = pd.DataFrame(
            data=None,
            columns=COLUMN_NAMES,
        )
        self.actor = actor_name
        if max_frames is not None:
            self.size = max_frames
        else:
            self.size = 1000

    def add(self, frame_number: int, latency: float):
        # exceeded maximum number of frame entries
        if frame_number > self.size:
            return

        self.df.loc[len(self.df.index)] = [int(frame_number), latency]

    def save(self):
        # when stop is called in the actors, safe the df to disk
        self.df.to_pickle(f"./latency/{self.actor}_latency_{time.strftime("%Y%m%d-%H%M%S")}.pkl")

