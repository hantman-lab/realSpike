Notes & Instructions
====================


Details for running real-time lift detection and stimulation two-photon holography :D



PRE-EXPERIMENT TODOs
--------------------
1. Check crop 
    - First a "test" video needs to be recorded (the animal does not have to be in the rig)
    - **Both the bias computer and improv computer need to be on the netgear switch**
        - Make sure to update the `ip_address` field in both scripts and check that they have matching port numbers 
    - `send_frame.py` should be placed on the same computer as bias
    - `check_crop.py` should stay on the improv computer 
    - **Run the `send_frame.py` script first and then the `check_crop.py` script**
2. Align laser 
    - `align_laser.py` should be placed on the PDM (Reagan's computer)
    - The script will display a full field pattern and turn the laser on for 30s
    - To turn the laser on, the usb for the laser will need to be plugged into the PDM
    - **NOTE:** The PDM does not need to be on the netgear switch to run this test
    - Instructions for running the script for aligning the laser can be found [here](https://docs.google.com/document/d/1BRN5fjz8DTYgcB3r8oJ438RY_BqFJK8Sj2__ErfupG4/edit?usp=sharing)

FILES & WHERE THEY LIVE
-----------------------
1. `improv` computer
    - `cue.py`
    - `check_crop.py`
2. PDM computer
    - `psychopy_viz.py`
    - `align_laser.py`
    - `preset_patterns.npy` (change path to this file in `psychoviz_viz.py`)
3. `bias` computer
    - `send_frame.py` (checking crop)
    - `generate_frames.py` (detection)
    - `make_avi.py` (for post-experiment)

IP_ADDRESS & PORT NUMBERS
-------------------------

| MACHINE1 | SRC                     | MACHINE2 | DST                     | IP ADDRESS      | PORT NUMBER | DESCRIPTION                           |
|----------|-------------------------|----------|-------------------------|-----------------|-------------|---------------------------------------|
| improv   | cue.py                  | improv   | actors/cue_detector.py  | "localhost"     | 5552        | cue signal from usb to improv         |
| improv   | actors/cue_detector.py  | PDM      | psychopy.py             | "192.168.0.100" | 4146        | cue signal from improv to PDM         |
| bias     | generate_frames.py      | improv   | actors/frame_grabber.py | "192.168.0.103" | 4148        | send frame from bias to improv        |
| improv   | actors/lift_detector.py | improv   | actors/frame_grabber.py | "localhost"     | 4143        | stop signal from detect to frame grab |
 

LOGGING
-------

**MAKE SURE TO CHANGE THE NAMES OF THE LOGGERS IN EACH ACTOR TO BE THE `ANIMAL_ID` AND `DATE` PREFIX (i.e., `rb50_20260127`)**

1. Behavior Detection 
    - Will output a dataframe with (trial number, frame number | NOT DETECTED, frame | None) 
    - Saved to `/behavior/`
2. Timing 
    - Each actor will log the amount of time it takes to send/receive frames  
    - Saved to `/latency/`
3. Pattern Logger
    - Saves the trial number and pattern 
        - There is an existing file with the pattern order already saved, but just want to have this to double-check post-experiment
