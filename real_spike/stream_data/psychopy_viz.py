from psychopy import visual, core
import numpy as np
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_spike.utils import connect, monitor_socket, get_buffer

SOCKET_OPEN = True



if __name__ == "__main__":
    # connect to port to listen on
    sub = connect()

    # Setup monitoring on the socket
    monitor = sub.get_monitor_socket()
    threading.Thread(target=monitor_socket, args=(monitor,), daemon=True).start()

    # open a blank screen
    win = visual.Window(size=[600, 600],
                        screen=0,
                        fullscr=False,
                        color='gray',
                        units='pix')

    # hide the cursor
    win.mouseVisible = False

    win.flip()

    while SOCKET_OPEN:
        buff = get_buffer(sub)

        if buff is not None:
            # Deserialize the buffer into a NumPy array
            data = np.frombuffer(buff, dtype=np.float64)

            data = data.reshape(13, 13).astype(np.float32)

            image_data = data * 2 - 1  # 0 becomes -1, 1 becomes +1

            # Convert to RGB by stacking the grayscale 3 times
            image_rgb = np.stack([image_data] * 3, axis=-1)

            # Create ImageStim
            stim = visual.ImageStim(win, image=image_rgb, size=(600, 600))

            stim.draw()
            win.flip()

            # only hold the pattern for small period
            core.wait(0.25)
            # Clear screen
            win.flip()

    win.close()
    core.quit()