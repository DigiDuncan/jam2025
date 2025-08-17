import math
import os
import threading

import arcade
from PIL import Image
import numpy as np


def rgb_to_l(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_polar_angle(x: float, y: float, center: tuple[float, float] = (0, 0)) -> float:
    return math.atan2(y - center[1], x - center[0])

def text_to_rect(text: arcade.Text) -> arcade.types.Rect:
    """This will be unnecessary once my PR is merged.
    https://github.com/pythonarcade/arcade/pull/2759
    """
    return arcade.types.LRBT(text.left, text.right, text.bottom, text.top)

def _open_settings(name: str = "USB Video Device") -> None:
    """WOW THIS SUCKS"""
    os.system(f"ffmpeg -hide_banner -loglevel error -f dshow -show_video_device_dialog true -i video=\"{name}\"")

def open_settings(name: str = "USB Video Device") -> None:
    thread = threading.Thread(target = _open_settings, args = (name,))
    thread.start()

def frame_data_to_image(data: np.ndarray) -> Image.Image:
    return Image.fromarray(data, mode = "RGB")
