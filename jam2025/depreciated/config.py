from tomllib import load
from typing import Self
from sys import platform
from pathlib import Path

from jam2025.lib.view_control import Transition

class WindowConfig:

    def __init__(self, webcam_name: str = "USB Video Device", initial_view: str = "m_calibration", window_width: int = 1280, window_height: int = 720, window_fps: int = 240, window_tps: int = 60):
        self.webcam_name = webcam_name

        self.initial_view = initial_view

        self.window_width = window_width
        self.window_height = window_height
        self.window_fps = window_fps
        self.window_tps = window_tps

        self.platform = platform


    @classmethod
    def from_file(cls, path: Path | str) -> Self:
        with open(path, 'rb') as fp:
            data = load(fp)
        web = data['webcam']
        win = data['window']
        return cls(
            web['name'],
            win['initial_view'],
            win['width'],
            win['height'],
            win['fps'],
            win['tps']
        )

    def write(self) -> None:
        _cfg_path = Path('.cfg')
        _data_str = (
            f"[webcam]\n"
            f"name=\"{self.webcam_name}\"\n"
            f"[window]\n"
            f"initial_view=\"{self.initial_view}\"\n"
            f"width={self.window_width}\n"
            f"height={self.window_height}\n"
            f"fps={self.window_fps}\n"
            f"tps={self.window_tps}"
        )
        with open(_cfg_path, "w+") as fp:
            fp.write(_data_str)

    @property
    def is_windows(self) -> bool:
        """The pname property."""
        return self.platform == "win32"

    @property
    def is_linux(self) -> bool:
        """The is_linux property."""
        return self.platform == "linux"


_cfg_path = Path('.cfg')
if _cfg_path.exists():
    CONFIG = WindowConfig.from_file(_cfg_path)
else:
    CONFIG = WindowConfig()
    CONFIG.write()

VIEWS = Transition()

__all__ = (
    "CONFIG",
    "VIEWS"
)
