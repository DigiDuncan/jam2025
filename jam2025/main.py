from arcade import View, Window

from jam2025.tests.webcam import WebcamTestView

SIZE = (1280, 720)
FPS = 240

class MainWindow(Window):
    def __init__(self) -> None:
        super().__init__(SIZE[0], SIZE[1], "Pass The Torch | Jam 2025B", update_rate = 1 / FPS)

        self.views: list[View] = [WebcamTestView()]

    def on_show(self):
        self.show_view(self.views[0])


def main() -> None:
    MainWindow().run()
