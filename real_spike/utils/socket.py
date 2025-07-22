def connect(address: str = "127.0.0.1", port_number: int = 5558):
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
    sub.connect(f"tcp://{address}:{port_number}")

    print(f"Made connection on port {port_number} at address {address}")

    return sub