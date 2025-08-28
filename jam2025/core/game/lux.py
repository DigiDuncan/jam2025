from math import tau
import arcade
from arcade.types import Point2, RGBOrA255
from pyglet.graphics import Batch
from pyglet.shapes import Triangle
from jam2025.lib.procedural_animator import ProceduralAnimator
from pyglet.math import Vec2

from logging import getLogger

from jam2025.lib.typing import Character

logger = getLogger("jam2025")

OFFSET = 6.0
RADIUS = 16.0

LOCUS_COUNT = 2
LOCUS_POS_FREQ = 3.0
LOCUS_POS_DAMP = 0.5
LOCUS_POS_RESP = 2.0

BUBBLE_COUNT = 16
BUBBLE_WIDTH = 6

NORMAL_TEST = 0.0001


class BubblePoint:
    def __init__(self, angle: float, locus: Point2):
        self.original_dir = Vec2.from_polar(1.0, angle)
        self.original_offset = self.original_dir * RADIUS
        pos = locus + self.original_offset

        self.animator = ProceduralAnimator(
            LOCUS_POS_FREQ, LOCUS_POS_DAMP, LOCUS_POS_RESP,
            pos, pos, Vec2()
        )

    def update(self, dt: float, new_locus: Point2, new_dir: Vec2):
        target = new_locus + self.original_offset
        dot = new_dir.dot(self.original_dir)
        self.animator.update_values(new_frequency=3.0*(0.5*dot + 0.5) + 3.0, new_response=dot)

        return self.animator.update(dt, target)

    @property
    def pos(self):
        return self.animator.y


class Bubble:
    def __init__(self, locus: Point2):
        self.bubble_points = tuple(BubblePoint(tau * idx/BUBBLE_COUNT, locus) for idx in range(BUBBLE_COUNT))
        self.points = tuple(p.pos for p in self.bubble_points)
        self._batch = Batch()
        self._triangle_indices = tuple((0, i, (i+1)%BUBBLE_COUNT) for i in range(1, BUBBLE_COUNT))
        self._triangles = tuple(Triangle(*self.points[a], *self.points[b], *self.points[c], batch=self._batch) for a,b,c in self._triangle_indices)

    def update(self, dt: float, locus: Point2, direction: Point2) -> None:
        self.points = tuple(p.update(dt, locus, Vec2(*direction)) for p in self.bubble_points)

    def draw(self, color: RGBOrA255) -> None:
        for idx in range(len(self._triangle_indices)):
            triangle = self._triangles[idx]
            if triangle.color != color:
                triangle.color = color

            a, b, c = self._triangle_indices[idx]
            triangle.x, triangle.y = self.points[a]
            triangle.x2, triangle.y2 = self.points[b]
            triangle.x3, triangle.y3 = self.points[c]
        self._batch.draw()


class PlayerRenderer:
    def __init__(self, character: Character):
        self.character = character

        self.locus_a: Vec2 = Vec2()
        self.locus_da: Vec2 = Vec2()
        self.locus_b: Vec2 = Vec2()
        self.locus_animator = ProceduralAnimator(
            LOCUS_POS_FREQ, LOCUS_POS_DAMP, LOCUS_POS_RESP,
            self.locus_a, self.locus_b, Vec2()  # type: ignore -- Animators are poorly typed
        )
        self.bubble = Bubble(self.locus_a)

    def update(self, dt: float) -> None:
        new_a = self.character.position
        self.locus_da = (new_a - self.locus_a)
        self.locus_a = Vec2(*new_a)
        self.locus_b = self.locus_animator.update(dt, self.locus_a, self.locus_da)
        self.bubble.update(dt, self.locus_a, Vec2(*self.character.velocity).normalize())

    def draw(self) -> None:
        self.bubble.draw(arcade.color.WHITE)
