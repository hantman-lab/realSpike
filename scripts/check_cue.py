from threading import Event
import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType

# initially starts as False
cue_signal = Event()

CUE_NUM = 0

while True:
    with nidaqmx.Task() as task:
        # TODO: change this with the actual device and channel
        task.ai_channels.add_ai_voltage_chan("Dev1/ai0")

        # TODO: change this to a little more than what the actual duration of the cue signal is
        # 50 / 5_000 = 0.01 ms duration of samples
        task.timing.cfg_samp_clk_timing(
            rate=5000, sample_mode=AcquisitionType.FINITE, samps_per_chan=50
        )

        task.start()

        data = np.asarray(task.read(100))

        # TODO: change this to the actual voltage crossing
        if np.any(data > 1.0):
            CUE_NUM += 1
            print(f"RECEIVED CUE {CUE_NUM}, SETTING CUE SIGNAL")
            cue_signal.set()
            # clear cue signal
            cue_signal.clear()
        else:
            print("DID NOT DETECT CUE")
            if cue_signal.is_set():
                raise ValueError("CUE SIGNAL SHOULD NOT BE SET")
