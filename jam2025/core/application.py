from arcade import Window as ArcadeWindow

from .config import CONFIG

class Window(ArcadeWindow):
    def __init__(self) -> None:
        super().__init__(CONFIG.window_width, CONFIG.window_height, "Pass The Torch | Jam 2025", update_rate = 1 / CONFIG.window_fps, fixed_rate = 1 / CONFIG.window_tps)


