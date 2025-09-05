from __future__ import annotations

from math import tau
import arcade
from arcade.types import Point2, RGBOrA255
from pyglet.graphics import Batch
from pyglet.shapes import Triangle, Circle
from jam2025.lib.procedural_animator import ProceduralAnimator, SecondOrderAnimator
from pyglet.math import Vec2
from typing import TYPE_CHECKING
from logging import getLogger

if TYPE_CHECKING:
    from jam2025.core.game.character import Character

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

import numpy as np

class LuxSimplified:
    """
    Because of how ProceduralAnimator is implimented we can use numpy arrays
    to animate all of lux's points at once.
    """

    def __init__(self, position: tuple[float, float]):
        self._directions = np.asarray([[np.cos(r), np.sin(r)] for r in np.linspace(0, 2 * np.pi, BUBBLE_COUNT, False)])
        self._relative_positions = RADIUS * self._directions
        self._batch = Batch()
        self._triangle_indices = tuple((0, i, (i+1)) for i in range(1, BUBBLE_COUNT-1))
        self._triangles = tuple(Triangle(0.0, 0.0, 1.0, 1.0, 2.0, 0.0, batch=self._batch) for _ in range(BUBBLE_COUNT-2))
        _positions = np.asarray([position]) + self._relative_positions
        self._animator = SecondOrderAnimator(
            LOCUS_POS_FREQ, LOCUS_POS_DAMP, LOCUS_POS_RESP,
            _positions.reshape(2*BUBBLE_COUNT), _positions.reshape(2*BUBBLE_COUNT), np.zeros(2*BUBBLE_COUNT) # type: ignore -- I need to fix the typing of the animatable protocol
        )
        self.update_triangles()

    def update(self, dt: float, nx: tuple[float, float], dx: tuple[float, float]):
        dot = dx[0]*self._directions[:, 0] + dx[1]*self._directions[:, 1]
        freq = 3.0*(0.5*dot + 0.5) + 3.0
        self._animator.update_frequency(new_frequency=np.repeat(freq, 2))
        self._animator.update_response(new_response=np.repeat(dot, 2))

        _positions = np.asarray([nx]) + self._relative_positions
        self._animator.update(dt, _positions.reshape(2*BUBBLE_COUNT))

    def update_triangles(self):
        points = (self._animator.y).reshape(BUBBLE_COUNT, -1)
        for idx, triangle in enumerate(self._triangles):
            a, b, c = self._triangle_indices[idx]
            triangle.x, triangle.y = points[a]
            triangle.x2, triangle.y2 = points[b]
            triangle.x3, triangle.y3 = points[c]

    def draw(self):
        self.update_triangles()
        # TODO: backface culling
        self._batch.draw()
        

class BubblePoint:
    def __init__(self, angle: float, locus: Point2):
        self.original_dir = Vec2.from_polar(angle, 1.0)
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
        self.bubble_points = tuple(BubblePoint(float(angle), locus) for angle in np.linspace(0, 2 * np.pi, BUBBLE_COUNT, False))
        self.points: tuple[Vec2, ...] = tuple(p.pos for p in self.bubble_points)
        self._batch = Batch()
        self._triangle_indices = tuple((0, i, (i+1)) for i in range(1, BUBBLE_COUNT-1))
        self._triangles = tuple(Triangle(*self.points[a], *self.points[b], *self.points[c], batch=self._batch) for a,b,c in self._triangle_indices)

    def update(self, dt: float, locus: Point2, direction: Vec2) -> None:
        self.points = tuple(p.update(dt, locus, direction) for p in self.bubble_points)

    def draw(self, color: RGBOrA255) -> None:
        for idx, triangle in enumerate(self._triangles):
            if triangle.color != color:
                triangle.color = color

            a, b, c = self._triangle_indices[idx]
            triangle.x, triangle.y = self.points[a]
            triangle.x2, triangle.y2 = self.points[b]
            triangle.x3, triangle.y3 = self.points[c]

        self._batch.draw()


class PlayerRenderer:
    def __init__(self):
        self.locus_a: Vec2 = Vec2()
        self.locus_da: Vec2 = Vec2()
        self.locus_b: Vec2 = Vec2()
        self.locus_animator = ProceduralAnimator(
            LOCUS_POS_FREQ, LOCUS_POS_DAMP, LOCUS_POS_RESP,
            self.locus_a, self.locus_b, Vec2()  # type: ignore -- Animators are poorly typed
        )
        self.bubble = Bubble(self.locus_a)

    def update(self, dt: float, new_a: Vec2) -> None:
        self.locus_da = (new_a - self.locus_a) / dt
        self.locus_a = Vec2(*new_a)
        self.locus_b = self.locus_animator.update(dt, self.locus_a, self.locus_da)
        self.bubble.update(dt, self.locus_a, self.locus_da.normalize())

    def draw(self) -> None:
        self.bubble.draw(arcade.color.WHITE)

