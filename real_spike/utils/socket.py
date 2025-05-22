import zmq
import zmq.utils.monitor as m

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

    print(f"Made connection on port {port_number}")

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
