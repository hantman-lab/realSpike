import time

from pyflycap2.interface import CameraContext, Camera


import pyflycap2.interface as fc2

import numpy as np

# USB / Flea3: use IIDC context
n = fc2.CameraContext("IIDC").get_num_cameras()
print("num cams:", n)

for i in range(n):
    cam = fc2.Camera(index=i, context_type="IIDC")
    print(
        "index", i, "serial", cam.serial, "guid", cam.guid, "iface", cam.interface_type
    )
    serial = cam.serial

cc = CameraContext()

# guid = cc.get_device_guid_from_index(0)
# print("GUID:", guid)

cam = Camera(serial=serial, context_type="IIDC")
cam.connect()

for attr in dir(cam):
    if attr.startswith("_"):
        continue
    val = getattr(cam, attr)
    if callable(val):
        continue
    print(f"{attr}: {val}")

cam.set_cam_setting_option_values("frame_rate", abs=True, auto=False)
cam.set_cam_abs_setting_value("frame_rate", 500.0)

print("FPS now:", cam.get_cam_abs_setting_value("frame_rate"))


# Start streaming
cam.start_capture()

try:
    t = time.perf_counter_ns()
    for _ in range(500):
        cam.read_next_image()
        img = cam.get_current_image()
        #   print(img.keys())
        r = img["rows"]
        c = img["cols"]
        frame = np.frombuffer(img["buffer"], dtype=np.uint8).reshape(r, c)
    # print(f"frame {k}: ", frame)
    t2 = (time.perf_counter_ns() - t) / 1e6
    print(t2)
finally:
    cam.stop_capture()
    cam.disconnect()
