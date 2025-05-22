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


# mostly for stopping the process when "stop" is called in the TUI
def monitor_socket(monitor):
    """Monitors the socket sets global bool when socket has closed."""
    global SOCKET_OPEN

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