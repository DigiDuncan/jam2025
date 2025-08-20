from arcade import View, Window

from jam2025.lib import logging
from jam2025.tests.webcam import WebcamTestView
from jam2025.views.calibration_step1 import MouseCalibrationView

SIZE = (1280, 720)
FPS = 240

class MainWindow(Window):
    def __init__(self) -> None:
        super().__init__(SIZE[0], SIZE[1], "Pass The Torch | Jam 2025B", update_rate = 1 / FPS)

        self.views: list[View] = [MouseCalibrationView(), WebcamTestView()]

    def on_show(self) -> None:
        self.show_view(self.views[1])


def main() -> None:
    logging.setup()
    MainWindow().run()
