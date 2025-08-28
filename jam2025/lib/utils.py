import math
import os
import threading

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    # !!! This is genuinely unhinged. What even is this module? Why is it private???
    from _typeshed import SupportsRichComparison

import arcade
from arcade.math import get_distance
from arcade.types import HasAddSubMul, Point2
from PIL import Image
import numpy as np

def nothing(*args: Any) -> None:
    ...

def point_in_circle(center: Point2, radius: float, point: Point2) -> bool:
    d = get_distance(*center, *point)
    return d <= radius

def clamp[T: SupportsRichComparison](min_val: T, val: T, mav_val: T) -> T:
    """Clamp a `val` to be no lower than `minVal`, and no higher than `maxVal`."""
    return max(min_val, min(mav_val, val))

def snap(n: float, increments: int) -> float:
    return round(increments * n) / increments

def map_range[L: HasAddSubMul](x: L, n1: L, m1: L, n2: L = -1, m2: L = 1) -> L:
    """Scale a value `x` that is currently somewhere between `n1` and `m1` to now be in an
    equivalent position between `n2` and `m2`."""
    # Make the range start at 0.
    old_max = m1 - n1
    old_x = x - n1
    percentage = old_x / old_max

    # Shmoove it over.
    new_max = m2 - n2
    new_pos = new_max * percentage
    ans = new_pos + n2
    return ans

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
