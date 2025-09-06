from __future__ import annotations

import arcade
import arcade.gl as gl
from arcade.types import Point2, RGBOrA255
from pyglet.graphics import Batch
from pyglet.shapes import Triangle
from jam2025.lib.procedural_animator import ProceduralAnimator, SecondOrderAnimator
from pyglet.math import Vec2
from logging import getLogger

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

class BubblePoint:
    def __init__(self, angle: float, locus: Vec2):
        self.original_dir = Vec2.from_polar(angle, 1.0)
        self.original_offset = self.original_dir * RADIUS
        pos = locus + self.original_offset

        self.animator = ProceduralAnimator(
            LOCUS_POS_FREQ, LOCUS_POS_DAMP, LOCUS_POS_RESP,
            pos, pos, Vec2()
        )

    def update(self, dt: float, new_locus: Vec2, new_dir: Vec2):
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
        self.locus_animator: SecondOrderAnimator[Vec2, float] = SecondOrderAnimator(
            LOCUS_POS_FREQ, LOCUS_POS_DAMP, LOCUS_POS_RESP,
            self.locus_a, self.locus_b, Vec2()
        )
        self.bubble = Bubble(self.locus_a)

    @property
    def position(self):
        return self.locus_a
    
    @position.setter
    def position(self, pos: Vec2):
        self.locus_a = pos

    @property
    def velocity(self):
        return self.locus_da
    
    @velocity.setter
    def velocity(self, vel: Vec2):
        self.locus_da = vel

    def update(self, dt: float) -> None:
        self.locus_b = self.locus_animator.update(dt, self.locus_a, self.locus_da)
        self.bubble.update(dt, self.locus_a, self.locus_da.normalize())

    def draw(self) -> None:
        self.bubble.draw(arcade.color.WHITE)

class LuxRenderer:
    FRAGMENT_SHADER = r"""#version 330
uniform vec4 in_colour;

out vec4 fs_colour;

void main(){
    fs_colour = in_colour;
}
"""
    VERTEX_SHADER = r"""#version 330
uniform WindowBlock {
    mat4 projection;
    mat4 view;
} window;

in vec2 in_position;

void main(){
    gl_Position = window.projection * window.view * vec4(in_position, 0.0, 1.0);
}
"""

    def __init__(self) -> None:
        self.position: Vec2 = Vec2()
        self.velocity: Vec2 = Vec2()

        self._directions: np.typing.NDArray[np.float64] = np.asarray([(np.cos(a), np.sin(a)) for a in np.linspace(0, 2*np.pi, BUBBLE_COUNT, endpoint=False)])
        self._offsets = RADIUS * self._directions
        
        vertices = [self.position] + self._offsets
        self._animator: SecondOrderAnimator[np.typing.NDArray[np.float64], np.typing.NDArray[np.float64]] = (
            SecondOrderAnimator(
                np.ones((BUBBLE_COUNT, 1)) * LOCUS_POS_FREQ,
                np.ones((BUBBLE_COUNT, 1)) * LOCUS_POS_DAMP,
                np.ones((BUBBLE_COUNT, 1)) * LOCUS_POS_RESP,
                vertices, vertices, np.zeros((BUBBLE_COUNT, 2))
            )
        )

        ctx = arcade.get_window().ctx
        self._vertices: gl.Buffer = ctx.buffer(data=np.asarray(vertices, np.float32).tobytes())
        self._geometry: gl.Geometry = ctx.geometry(
            [gl.BufferDescription(self._vertices, '2f', ['in_position'])],
            index_buffer=ctx.buffer(data=np.asarray([(0, (i+1), i) for i in range(1, BUBBLE_COUNT-1)], dtype=np.int32).tobytes()),
            mode=ctx.TRIANGLES
        )
        self._program: gl.Program = ctx.program(
            vertex_shader=LuxRenderer.VERTEX_SHADER,
            fragment_shader=LuxRenderer.FRAGMENT_SHADER,
        )
        self._program['in_colour'] = (1.0, 1.0, 1.0, 1.0)
    
    def reset(self):
        self.position: Vec2 = Vec2()
        self.velocity: Vec2 = Vec2()
        vertices = [self.position] + self._offsets
        self._animator = (
            SecondOrderAnimator(
                np.ones((BUBBLE_COUNT, 1)) * LOCUS_POS_FREQ,
                np.ones((BUBBLE_COUNT, 1)) * LOCUS_POS_DAMP,
                np.ones((BUBBLE_COUNT, 1)) * LOCUS_POS_RESP,
                vertices, vertices, np.zeros((BUBBLE_COUNT, 2))
            )
        )

        self._vertices.write(vertices.tobytes())

    def update(self, dt: float) -> None:
        dir = self.velocity.normalize()
        dot = dir.x * self._directions[:, None, 0] + dir.y * self._directions[:, None, 1]
        self._animator.update_values(new_frequency=3.0*(0.5*dot + 0.5) + 3.0, new_response=dot)

        targets = [self.position] + self._offsets
        vertices = self._animator.update(dt, targets)
        self._vertices.write(np.asarray(vertices, np.float32).tobytes())

    def draw(self) -> None:
        self._geometry.render(self._program)

