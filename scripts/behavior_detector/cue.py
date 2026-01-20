import serial
import time
import zmq

address = "localhost"
port_number = 5552

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(f"tcp://{address}:{port_number}")
print(f"Connected to {address}:{port_number}")

CUE_NUM = 0

port_name = "/dev/ttyACM0"
baud_rate = 9600  # Check your device's documentation for the correct baud rate

ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=1)
print("opened port")
ser.reset_input_buffer()


while True:
    bytes_available = ser.in_waiting

    if bytes_available > 0:
        line = ser.readline().decode(errors="ignore").strip()
        # print(line)
        if line == "1":
            # send detection signal to improv CueDetector
            socket.send_string("1")
            CUE_NUM += 1
            # Trigger received
            print(f"RECEIVED CUE {CUE_NUM}")
            # put to sleep so that it doesn't accidentally read the same cue signal more than once
            time.sleep(1.5)
            ser.flush()
            ser.reset_input_buffer()
