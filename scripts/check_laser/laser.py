"""File to turn the laser on 10 times. Run on the improv computer."""

import serial
import time


if __name__ == "__main__":
    from serial.tools import list_ports

    # print the ports
    # ports = list_ports.comports()
    #
    # for p in ports:
    #     print(f"Port: {p.device}")
    #     print(f"  Description: {p.description}")
    #     print(f"  HWID: {p.hwid}")
    #     print(f"  VID:PID = {p.vid}:{p.pid}")
    #     print(f"  Manufacturer: {p.manufacturer}")
    #     print(f"  Product: {p.product}")
    #     print(f"  Serial Number: {p.serial_number}")
    #     print()

    ser = serial.Serial("/dev/ttyACM0", 115200, timeout=5)
    print("Opened serial port")
    time.sleep(2)

    for i in range(5):
        print(f"TURNING LASER ON, ATTEMPT {i}")
        ser.write(b"STIM 13 4 0 5000 10000 1\n")
        ser.flush()
        # sleep for 10 seconds and then try laser again
        time.sleep(2)

    print("Closing serial port")
    ser.close()
