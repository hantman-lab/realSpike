"""File for Reagan to align the laser. Will make a psychopy window with full field pattern and turn the laser on."""

from psychopy import visual, core, event
import numpy as np

# open a blank screen
win = visual.Window(
    size=[1280, 1280],
    screen=0,
    fullscr=True,
    color="black",
    units="pix",
    checkTiming=False,
)

# hide the cursor
win.mouseVisible = False

# initiate a black screen to start
win.flip()

# 320 pixels per 2mm
px_per_cell = 160


img = np.array([[1, 1], [1, 1]]).reshape(2, 2)
img = 2 * img - 1
stim = visual.ImageStim(
    win,
    image=img,
    size=(2 * px_per_cell, 2 * px_per_cell),
    units="pix",
    interpolate=False,  # VERY IMPORTANT
)
# need to put the stim in the top right corner for flip by DMD
win_width, win_height = win.size
stim.pos = (
    -win_width / 2 + stim.size[0] / 2,
    win_height / 2 - stim.size[1] / 2,
)

print("showing full field pattern")
stim.draw()
win.flip()

event.waitKeys()
win.close()
