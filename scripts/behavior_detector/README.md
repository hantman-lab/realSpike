Notes and instructions
======================


1. Detail what each file does and what system it should live on
2. How to run each thing 



PRE-EXPERIMENT TODOs
--------------------
1. Check crop 
    - First a "test" video needs to recorded (the animal does not have to be in the rig)
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
    - Instructions for aligning the laser can be found [here](https://docs.google.com/document/d/1BRN5fjz8DTYgcB3r8oJ438RY_BqFJK8Sj2__ErfupG4/edit?usp=sharing)

FILES & WHERE THEY LIVE
-----------------------
1. `improv` computer
    - `cue.py`
    - `check_crop.py`
2. PDM computer
    - `psychopy_viz.py`
    - `align_laser.py`
3. `bias` computer
    - `send_frame.py` (checking crop)
    - `generate_frames.py` (detection)

IP_ADDRESS & PORT NUMBERS
-------------------------

| MACHINE1 | SRC                    | MACHINE2 | DST                     | IP ADDRESS      | PORT NUMBER | DESCRIPTION                    |
|----------|------------------------|----------|-------------------------|-----------------|-------------|--------------------------------|
| improv   | cue.py                 | improv   | actors/cue_detector.py  | "localhost"     | 5552        | cue signal from usb to improv  |
| improv   | actors/cue_detector.py | PDM      | psychopy.py             | "192.168.0.100" | 4146        | cue signal from improv to PDM  |
| bias     | generate_frames.py     | improv   | actors/frame_grabber.py | "192.168.0.102" | 4147        | send frame from bias to improv |

LOGGING
-------

[//]: # (what things are being saved and where should they be looked for)
[//]: # (changing the names of the loggers to match the animal-id experiments)