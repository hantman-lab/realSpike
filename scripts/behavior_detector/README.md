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
1. `cue.py`
2. `psychopy.py`
3. `align_laser.py`
4. `check_crop.py`
5. `send_frame.py` 

IP_ADDRESS & PORT NUMBERS
-------------------------

[//]: # (insert a table src [machine and file], dst [machine and file], ip_address, port_number) 


LOGGING
-------

[//]: # (what things are being saved and where should they be looked for)
[//]: # (changing the names of the loggers to match the animal-id experiments)