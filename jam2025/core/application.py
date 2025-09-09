from arcade import Window as ArcadeWindow

from .settings import settings

class Window(ArcadeWindow):
    def __init__(self) -> None:
        super().__init__(settings.window_width, settings.window_height, "Pass The Torch | Jam 2025", update_rate = 1 / settings.window_fps, fixed_rate = 1 / settings.window_tps)


