from psychopy import visual, core, event
import numpy as np

control = np.zeros((2, 2))
full = np.ones((2, 2))

quad_ul = np.array([[1, 0], [0, 0]])

quad_ur = np.array([[0, 1], [0, 0]])

quad_ll = np.array([[0, 0], [1, 0]])

quad_lr = np.array([[0, 0], [0, 1]])

conditions = [control, full, quad_ul, quad_ur, quad_ll, quad_lr]


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

    # TODO: update with ratio
    px_per_cell = 80

    for c in conditions:
        print(c)
        img = c.reshape(2, 2)
        img = 2 * img - 1
        # need to flip upside down
        img = np.flipud(img)
        stim = visual.ImageStim(
            win,
            image=img,
            size=win.size,
            # size=(2 * px_per_cell, 2 * px_per_cell),
            units="pix",
            interpolate=False,  # VERY IMPORTANT
        )

        stim.draw()
        win.flip()

        core.wait(2.5)

    win.close()
    core.quit()
