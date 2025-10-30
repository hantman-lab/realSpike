# Automated "lift" detection to prompt stimulation delivery


## Actors

1. Generator
- Will communicate with the camera and grab frames 
  - Might need to think of a way to get the "cue" signal after trial starts (only really need to be fetching frames during the 5ms after cue)
- For now, can just read video(s) from disk and stream at the proper sampling rate (500Hz)
- Optionally crop frame in this step around where the paw will start to make detection easier
- Pass frame to detector
2. Detector 
- Responsible for doing the OpenCV calls for detection or deep learning related things depending on model used 
- Process a frame one at a time, detect paw (either via bright pixel marker on paw or bounding box around object)
- If paw has crossed threshold for lift, trigger stim 
  - Only need to trigger stim on first detection of threshold crossing (keep a boolean flag per trial of whether stim has been delivered or not)
- Need to track in a given trial if stim has been triggered or not, only want the first threshold crossing 
3. Pattern 
- Hold the logic for communicating with `psychopy` on the pattern display computer 
  - Likely will still be a pre-fixed list of patterns 
- Basically just instantiate the pattern and send it on via `zmq` 
- Need to put in some constraints for how to make sure stim only gets triggered once per trial
4. Visual (Optional) 
- Could have `fastplotlib` running in real-time and showing the detection as it happens 
  - Might be useful in these initial stages 

## TODO 
- [ ] Stream a video at 500Hz, do the cropping
- [ ] Implement detection schema after some more playing around in notebook setting 
    - [ ] Start with just using very good trials that are single reach
      - Hopefully with just identifying lift, that should be pretty consistent even in the multi-reach trials (should probably investigate some after initial model working) 
- [ ] Timing profiling 
    - [ ] Should get a baseline sense of how fast lift normally happens on average and also how fast between lift and grab is on average
      - We need to detect lift as early on as possible so that hopefully we can deliver stim as close to still during/right after lift 
    - [ ] Running the video, doing detection, sending out pattern 
      - No Netgear switch to get accurate pattern timing, but could run the `psychopy` locally or send patterns over Duke network (would just be really inflated network costs)
    - [ ] Get both total costs for the entire pipeline and individual components 
      - Obviously the latency for communicating with the camera will be artificially lower because I will be streaming from disk
- [ ] Model comparison
    - Even if I end up in practice only using OpenCV with no deep learning model, still need to implement/use one for ECE 661 class
    - Can do some timing profiling of just doing the detection for comparison 
- [ ] Making nice figures to go into the final report and also into my prelim exam next Spring 