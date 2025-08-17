from collections.abc import Callable
from typing import Any
import arcade
from arcade.math import get_distance
from arcade.types import Color, Point2

def nothing(*args: Any) -> None:
    ...

def point_in_circle(center: Point2, radius: float, point: Point2) -> bool:
    d = get_distance(*center, *point)
    return d <= radius

class Button:
    def __init__(self, x: int, y: int, size: int, thickness: int, hold_time: float = 1.5, cooldown_time: float = 1.0,
                 back_color: Color = arcade.color.GRAY, front_color: Color = arcade.color.WHITE, active_color: Color = arcade.color.GREEN,
                 callback: Callable = nothing, callback_args: tuple = ()) -> None:
        self.x = x
        self.y = y
        self.size = size
        self.thickness = thickness
        self.hold_time = hold_time
        self.cooldown_time = cooldown_time
        self.back_color = back_color
        self.front_color = front_color
        self.active_color = active_color
        self.callback = callback
        self.callback_args = callback_args

        self.current_hold_time = 0.0
        self.fired = False
        self.left = True
        self.cooldown = 0.0

    @property
    def hold_percentange(self) -> float:
        return self.current_hold_time / self.hold_time

    def update(self, delta_time: float, cursor: Point2) -> None:
        pic = point_in_circle((self.x, self.y), self.size / 2, cursor)
        if pic and not self.fired and self.left:
            self.current_hold_time += delta_time
        if self.current_hold_time >= self.hold_time and not self.fired:
            self.callback(*self.callback_args)
            self.fired = True
            self.left = False
        if pic and self.fired:
            self.cooldown += delta_time
        if self.cooldown >= self.cooldown_time:
            self.fired = False
            self.current_hold_time = 0.0
            self.cooldown = 0.0
        if not pic:
            self.left = True
            self.current_hold_time = 0.0
        if not pic and self.fired:
            self.fired = False

    def draw(self) -> None:
        if not self.fired:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.back_color, self.thickness)
            arcade.draw_arc_outline(self.x, self.y, self.size, self.size, self.front_color, 0, self.hold_percentange * 360, self.thickness)
        if self.fired:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.active_color, self.thickness)
