from collections.abc import Callable
from typing import Any
import arcade
from arcade.clock import GLOBAL_CLOCK
from arcade.math import get_distance
from arcade.types import Color, Point2

from jam2025.lib.anim import ease_linear, perc

def nothing(*args: Any) -> None:
    ...

def point_in_circle(center: Point2, radius: float, point: Point2) -> bool:
    d = get_distance(*center, *point)
    return d <= radius

class HoverButton:
    def __init__(self, x: float, y: float, size: int, thickness: int, hold_time: float = 1.5, cooldown_time: float = 1.0,
                 back_color: Color = arcade.color.GRAY, front_color: Color = arcade.color.RED, active_color: Color = arcade.color.GREEN,
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

        self.disabled = False

        self.current_hold_time = 0.0
        self.fired = False
        self.left = True
        self.cooldown = 0.0

    @property
    def hold_percentange(self) -> float:
        return self.current_hold_time / self.hold_time

    def update(self, delta_time: float, cursor: Point2) -> None:
        pic = point_in_circle((self.x, self.y), self.size / 2, cursor) if cursor else False
        if pic and not self.fired and self.left and not self.disabled:
            self.current_hold_time += delta_time
        if self.current_hold_time >= self.hold_time and not self.fired:
            self.callback(*self.callback_args)
            self.fired = True
            self.current_hold_time = 0.0
            self.left = False
        if pic and self.fired:
            self.cooldown += delta_time
        if self.cooldown >= self.cooldown_time:
            self.fired = False
            self.cooldown = 0.0
        if not pic:
            self.left = True
            self.current_hold_time -= delta_time * 2
            self.current_hold_time = max(0, self.current_hold_time)
        if not pic and self.fired:
            self.fired = False

    def draw(self) -> None:
        if not self.fired and not self.disabled:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.back_color, self.thickness)
            portion = self.hold_percentange * 360
            arcade.draw_arc_outline(self.x, self.y, self.size - self.thickness, self.size - self.thickness, self.front_color, 0, portion, self.thickness * 2, tilt_angle = -90 + portion)
        elif self.fired:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.back_color.replace(a = 128 if self.disabled else 255), self.thickness)
            alpha = int(ease_linear(255, 0, perc(self.cooldown_time / 2, self.cooldown_time, self.cooldown)))
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.active_color.replace(a = alpha), self.thickness)
        else:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.back_color.replace(a = 128), self.thickness)

class ClickButton:
    def __init__(self, x: float, y: float, size: int, thickness: int,
                 back_color: Color = arcade.color.GRAY, front_color: Color = arcade.color.RED, active_color: Color = arcade.color.GREEN,
                 callback: Callable = nothing, callback_args: tuple = ()) -> None:
        self.x = x
        self.y = y
        self.size = size
        self.thickness = thickness
        self.back_color = back_color
        self.front_color = front_color
        self.active_color = active_color
        self.callback = callback
        self.callback_args = callback_args

        self.disabled = False
        self.hovered = False
        self.clicked = False
        self.last_fire_time = -float("inf")
        self.cooldown = 1.0

    def update(self, cursor: arcade.Vec2, clicked: bool) -> None:
        last_click = self.clicked
        self.hovered = point_in_circle((self.x, self.y), self.size / 2, cursor)
        self.clicked = clicked

        if not last_click and self.clicked and self.hovered:
            self.callback(*self.callback_args)
            self.last_fire_time = GLOBAL_CLOCK.time


    def draw(self) -> None:
        if self.disabled:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.back_color.replace(a = 128), self.thickness)
        else:
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.back_color, self.thickness)
            if self.hovered:
                arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.front_color, self.thickness)
            alpha = int(ease_linear(255, 0, perc(self.last_fire_time, self.last_fire_time + self.cooldown, GLOBAL_CLOCK.time)))
            arcade.draw_circle_outline(self.x, self.y, self.size / 2, self.active_color.replace(a = alpha), self.thickness)
