from collections.abc import Callable
from arcade import Rect, Sound, Vec2
import arcade
from arcade.types import Color

from jam2025.lib.anim import lerp, perc
from jam2025.lib.utils import clamp

class Slider[RT]:
    def __init__(self, rect: Rect, slider_min: float = 0, slider_max: float = 100,
                 inner_color: Color = arcade.color.BLACK, outer_color: Color = arcade.color.WHITE,
                 border_thickness: int = 3, handle_color: Color = arcade.color.WHITE,
                 handle_thickness: int = 25, sound: Sound | None = None, rounding_function: Callable[[float], RT] = float) -> None:
        self.rect = rect
        self.handle_rect = self.rect.clamp_width(handle_thickness, handle_thickness)
        self.handle_rect = self.handle_rect.align_left(self.rect.left)
        self.slider_min = slider_min
        self.slider_max = slider_max
        self.inner_color = inner_color
        self.outer_color = outer_color
        self.border_thickness = border_thickness
        self.handle_color = handle_color
        self.sound = sound
        self.rounding_function = rounding_function

        self._registered_functions: list[Callable[[RT], None]] = []

    @property
    def value(self) -> RT:
        val = lerp(self.slider_min, self.slider_max, perc(self.rect.left + self.handle_rect.width, self.rect.right, self.handle_rect.right))
        return self.rounding_function(val)

    def register(self, f: Callable[[RT], None]) -> None:
        if f not in self._registered_functions:
            self._registered_functions.append(f)

    def update(self, cursor_pos: Vec2) -> None:
        if cursor_pos in self.handle_rect:
            self.handle_rect = self.handle_rect.align_x(clamp(self.rect.left + self.handle_rect.width / 2, cursor_pos.x, self.rect.right - self.handle_rect.width / 2))
        for f in self._registered_functions:
            f(self.value)

    def draw(self) -> None:
        arcade.draw_rect_filled(self.rect, self.inner_color)
        arcade.draw_rect_outline(self.rect, self.outer_color, self.border_thickness)
        arcade.draw_rect_filled(self.handle_rect, self.handle_color)
