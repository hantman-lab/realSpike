"""File to turn the laser on 10 times. Run on the improv computer."""

import serial
import time


if __name__ == "__main__":
    ser = serial.Serial("/dev/ttyACM0", 115200, timeout=5)
    print("Opened serial port")

    for i in range(10):
        print(f"TURNING LASER ON, ATTEMPT {i}")
        ser.write(b"STIM 13 4 0 5000 10000 1\n")
        # sleep for 10 seconds and then try laser again
        time.sleep(10)
