"""Fastplotlib gui that will request frame 615 from disk on bias computer."""

from fastplotlib.ui import EdgeWindow
import fastplotlib as fpl
import zmq
import numpy as np
from imgui_bundle import imgui


DEFAULT_CROP = [136, 155, 207, 220]
RESHAPE_SIZE = (290, 448)

# TODO: update with netgear ip_address
ip_address = "localhost"
port = 5555

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f"tcp://{ip_address}:{port}")
print(f"Connected to ZMQ server at {ip_address} on port {port}")

socket.send_string("fetch()")
data = socket.recv()  # Receive one full frame
data = np.frombuffer(data, dtype=np.uint8)
data = data.reshape(*RESHAPE_SIZE)

print(data.shape)

socket.close()


class ImguiWindow(EdgeWindow):
    def __init__(self, figure, size, location, title):
        super().__init__(figure=figure, size=size, location=location, title=title)

        self.current_crop = DEFAULT_CROP

        self.rect_selector = self._figure[0, 0].selectors[0]

    def update(self):
        # reset button
        if imgui.button("Set Crop"):
            print("new crop")
            self.current_crop = [int(_) for _ in self.rect_selector.selection]
            print(self.current_crop)

        if imgui.button("Reset Crop"):
            print("resetting crop to default")
            self.rect_selector.selection = DEFAULT_CROP
            self.current_crop = DEFAULT_CROP


figure = fpl.Figure(size=(800, 500))

ig = figure[0, 0].add_image(data, cmap="gray")

rs = ig.add_rectangle_selector(selection=DEFAULT_CROP, resizable=False)

figure[0, 0].axes.visible = False

gui = ImguiWindow(figure, 100, "right", "Check Crop")
figure.add_gui(gui)

figure.show()


if __name__ == "__main__":
    fpl.loop.run()
