# separate script for the pyschopy commands, I think this would be run on the other monitor
# but want to port the matlab script here

# also will be good to make the zmq connection for sending the data
# hopefully we can just send the pattern data to psychopy and it display the pattern
from psychopy import visual, event, core
import numpy as np



if __name__ == "__main__":
    # open a blank screen

    # make a local zmq connection

    # get buffer similar to whats in notebook

    # when get buffer, make into image that can displayed
    # if buffer is not empty, display pattern

    # go back to blank screen after

    # Create a window


    win = visual.Window([600, 600], color='gray', units='pix')

    # Create a 2D array of 0s and 1s
    array = np.random.randint(0, 2, (100, 100))  # 100x100 binary image

    # Convert to grayscale values between 0 and 1
    image_data = array.astype(np.float32)

    # Scale to -1 to 1 (PsychoPy texture range)
    image_data = image_data * 2 - 1  # 0 becomes -1, 1 becomes +1

    # Convert to RGB by stacking the grayscale 3 times
    image_rgb = np.stack([image_data] * 3, axis=-1)  # shape: (100, 100, 3)

    # Create ImageStim
    stim = visual.ImageStim(win, image=image_rgb, size=(300, 300))

    # Draw and show the image
    stim.draw()
    win.flip()

    # Wait for a keypress or 3 seconds
    event.waitKeys(maxWait=3)
    win.close()
    core.quit()