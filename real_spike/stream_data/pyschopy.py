# separate script for the pyschopy commands, I think this would be run on the other monitor
# but want to port the matlab script here

# also will be good to make the zmq connection for sending the data
# hopefully we can just send the pattern data to psychopy and it display the pattern
from psychopy import visual, event, core
import numpy as np
import zmq
import threading
import zmq.utils.monitor as m

SOCKET_OPEN = True


def connect(port_number: int = 5558):
    """
    Connect to the pattern generator actor via zmq. Make sure that ports match and are different from visual
    actor ports.
    """
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, b"")

    # keep only the most recent message
    sub.setsockopt(zmq.CONFLATE, 1)

    # TODO: add in check to make sure specified port number is valid

    # address must match publisher in actor
    sub.connect(f"tcp://127.0.0.1:{port_number}")

    print("Made connection")

    return sub

# TODO: implement this function to monitor whether the socket has been closed since
#  this file will not receive the stop signal from improv
def monitor_socket(monitor):
    global SOCKET_OPEN
    """Returns a bool indicating if a given socket has closed or not."""
    while True:
        try:
            event = m.recv_monitor_message(monitor)
            evt = event['event']
            if evt == zmq.EVENT_ACCEPTED:
                SOCKET_OPEN = True
            elif evt == zmq.EVENT_DISCONNECTED:
                SOCKET_OPEN = False
                print("Exiting process")
        except zmq.error.ZMQError:
            break


def get_buffer(sub):
    """Gets the buffer from the publisher."""
    try:
        b = sub.recv(zmq.NOBLOCK)
    except zmq.Again:
        pass
    else:
        return b

    return None

if __name__ == "__main__":
    sub = connect()

    # Setup monitoring on the socket
    monitor = sub.get_monitor_socket()
    threading.Thread(target=monitor_socket, args=(monitor,), daemon=True).start()

    while SOCKET_OPEN:
        buff = get_buffer(sub)

        if buff is not None:
            # Deserialize the buffer into a NumPy array
            data = np.frombuffer(buff, dtype=np.float64)

            data = data.reshape(13, 13)
            print(data)

            # break

    # open a blank screen

    # when get buffer, make into image that can displayed
    # if buffer is not empty, display pattern

    # go back to blank screen after

    # Create a window


    # win = visual.Window([600, 600], color='gray', units='pix')
    #
    # # Create a 2D array of 0s and 1s
    # array = np.random.randint(0, 2, (100, 100))  # 100x100 binary image
    #
    # # Convert to grayscale values between 0 and 1
    # image_data = array.astype(np.float32)
    #
    # # Scale to -1 to 1 (PsychoPy texture range)
    # image_data = image_data * 2 - 1  # 0 becomes -1, 1 becomes +1
    #
    # # Convert to RGB by stacking the grayscale 3 times
    # image_rgb = np.stack([image_data] * 3, axis=-1)  # shape: (100, 100, 3)
    #
    # # Create ImageStim
    # stim = visual.ImageStim(win, image=image_rgb, size=(300, 300))
    #
    # # Draw and show the image
    # stim.draw()
    # win.flip()
    #
    # # Wait for a keypress or 3 seconds
    # event.waitKeys(maxWait=30)
    # win.close()
    # core.quit()