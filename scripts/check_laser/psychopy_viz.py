"""File to just hold one pattern on. Put file on the Pattern Display Monitor."""

from psychopy import visual, event
import numpy as np

condition = np.array([[1, 0], [0, 1]])

if __name__ == "__main__":
    # open a blank screen
    win = visual.Window(
        size=[800, 800],
        screen=0,
        fullscr=False,  # TODO: will need to flip this to True during actual experiments
        color="black",
        units="pix",
        checkTiming=False,
    )

    # hide the cursor
    win.mouseVisible = False

    # initiate a black screen to start
    win.flip()

    img = condition.reshape(2, 2)
    img = 2 * img - 1
    # need to flip upside down
    img = np.flipud(img)
    stim = visual.ImageStim(
        win,
        image=img,
        size=win.size,
        units="pix",
        interpolate=False,  # VERY IMPORTANT
    )

    stim.draw()
    win.flip()

    event.waitKeys()
    win.close()
