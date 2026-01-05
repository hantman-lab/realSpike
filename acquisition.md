# Acquisition 

## Things to update before running real-time experiment

1. Check `acquisition.yaml` and make sure that the generator actor is set to `generator_netgear`
2. Within the generator file, fix the `address` that `SpikeGLX` is broadcasting to (should be the same every time for the netgear switch)
3. In `psychopy_viz_windows.py`
    - change the `address` and `port` that is being used to match netgear 
    - make sure the pattern reshape size is correct
4. In the pattern actor, change the `address` and `port` that is being used to match netgear 
5. Make sure the path for saving the timing on the Windows pattern display monitor is valid 
6. In each actor, make sure the name for the loggers/latency registers are correct


## Setting up the Windows pattern display monitor 

1. Install `python==3.11` 
2. Create a virtual environment 
3. Run the following:
```bash 
pip install psychopy, pandas, nidaqmx, zmq, numpy 
```
4. Download the script from GitHub 
5. Change the window option to `fullscreen=True`
6. Create a `timing` folder to have the pattern timing save out correctly 