from random import random

import numpy as np
from arcade import View as ArcadeView, get_window
from arcade.types import Point2
import arcade.gl as gl

class Lux:
    TRANSFORM: str = """ #version 330

uniform vec4 state; // dt, g, reserved * 2

in vec4 in_dynamic; // xy: position zw: velocity
in vec4 in_properties; // xy: target z: radius w: decay

out vec4 out_dynamic;
out vec4 out_properties;

void main(){
    vec2 diff = in_properties.xy - in_dynamic.xy;
    float distance = length(diff);
    vec2 decceleration = -in_dynamic.zw*in_properties.w;
    vec2 acceleration;
    if (distance < 5){
        acceleration = vec2(0.0);
    }
    else{
        acceleration = diff / pow(distance, 2) * state.y;
    }

    out_dynamic.zw = in_dynamic.zw + (acceleration + decceleration) * state.x;
    out_dynamic.xy = in_dynamic.xy + out_dynamic.zw * state.x;

    out_properties = in_properties;
}
"""

    DEBUG_VERTEX: str = """#version 330

uniform WindowBlock {
    mat4 projection;
    mat4 view;
} window;

in vec4 in_dynamic;
in vec4 in_colour;

out vec4 vs_colour;

void main(){
    gl_Position = window.projection * window.view * vec4(in_dynamic.xy, 0.0, 1.0);
    vs_colour = in_colour;
}
"""

    DEBUG_FRAGMENT="""#version 330
in vec4 vs_colour;
out vec4 fs_colour;
void main() { fs_colour = vs_colour; }
"""

    def __init__(self, x: float, y: float) -> None:
        self.blob_colours = np.asarray(
            [
                (1.0, 1.0, 1.0, 1.0)
                for _ in range(20)
            ],
            dtype=np.float32
        )
        self.blob_positions = np.asarray(
            [
                # x, y, vx, vy, tx, ty, r, d,  
                (x*random(), random()*y, (random() - 0.5) * 50.0, (random() - 0.5) * 50.0, x*0.5, y*0.5, 10.0, 0.1)
                for _ in range(20)
            ],
            dtype=np.float32
        )

        self._stale: bool = False

        self.gravity: float = 10000.0
        
        self.ctx = ctx = get_window().ctx

        self.transform_shader = ctx.program(vertex_shader=Lux.TRANSFORM)
        self.debug_shader = ctx.program(
            vertex_shader=Lux.DEBUG_VERTEX,
            fragment_shader=Lux.DEBUG_FRAGMENT,
        )

        byte_data = self.blob_positions.tobytes()
        self.blob_buffer_1 = ctx.buffer(data=byte_data, usage='dynamic')
        self.blob_buffer_2 = ctx.buffer(data=byte_data, usage='dynamic')
        self.colour_buffer = ctx.buffer(data=self.blob_colours.tobytes(), usage='dynamic')

        self.blob_debug_1 = ctx.geometry(
            [
                gl.BufferDescription(self.blob_buffer_1, '4f 4f', ['in_dynamic', 'in_properties']),
                gl.BufferDescription(self.colour_buffer, '4f', ['in_colour'])
            ]
        )
        self.blob_debug_2 = ctx.geometry(
            [
                gl.BufferDescription(self.blob_buffer_2, '4f 4f', ['in_dynamic', 'in_properties']),
                gl.BufferDescription(self.colour_buffer, '4f', ['in_colour'])
            ]
        )

        self.transform_1 = ctx.geometry(
            [gl.BufferDescription(self.blob_buffer_1, '4f 4f', ['in_dynamic', 'in_properties']),]
        )
        self.transform_2 = ctx.geometry(
            [gl.BufferDescription(self.blob_buffer_2, '4f 4f', ['in_dynamic', 'in_properties']),]
        )

    def get_velocity(self, blob: int):
        return self.blob_positions[blob, 2], self.blob_positions[blob, 3]

    def apply_impulse(self, impulse: Point2, blob: int = -1):
        self._stale = True
        if blob < 0:
            self.blob_positions[:, 2] = impulse[0]
            self.blob_positions[:, 3] = impulse[1]
            return
        self.blob_positions[blob, 2] += impulse[0]
        self.blob_positions[blob, 3] += impulse[1]

    def move_target(self, position: Point2, blob: int = -1):
        self._stale = True
        if blob < 0:
            self.blob_positions[:, 4] = position[0]
            self.blob_positions[:, 5] = position[1]
            return
        self.blob_positions[blob, 4] = position[0]
        self.blob_positions[blob, 5] = position[1]

    def move_blob(self, position: Point2, blob: int = -1):
        self._stale = True
        if blob < 0:
            self.blob_positions[:, 0] = position[0]
            self.blob_positions[:, 1] = position[1]
            return
        self.blob_positions[blob, 0] = position[0]
        self.blob_positions[blob, 1] = position[1]

    def shift_blob(self, shift: Point2, blob: int = -1):
        self._stale = True
        if blob < 0:
            self.blob_positions[:, 0] += shift[0]
            self.blob_positions[:, 1] += shift[1]
            return
        self.blob_positions[blob, 0] += shift[0]
        self.blob_positions[blob, 1] += shift[1]

    def update(self, delta_time: float):
        if self._stale:
            self._stale = False
            self._write()
    
        self.transform_shader['state'] = delta_time, self.gravity, 0.0, 0.0
        self.transform_1.transform(self.transform_shader, self.blob_buffer_2)
        self._swap()

    def _write(self):
        self.blob_buffer_1.write(data=self.blob_positions.tobytes())

    def _swap(self, read: bool = True):
        self.transform_1, self.transform_2 = self.transform_2, self.transform_1
        self.blob_buffer_1, self.blob_buffer_2 = self.blob_buffer_2, self.blob_buffer_1
        self.blob_debug_1, self.blob_debug_2 = self.blob_debug_2, self.blob_debug_1

        if read:
            self._read()

    def _read(self):
        byte_data = self.blob_buffer_2.read()
        self.blob_positions = np.frombuffer(byte_data, np.float32).reshape(-1, 8).copy()

    def debug_draw(self):
        self.blob_debug_1.render(self.debug_shader, mode=gl.POINTS)


class LuxBlobTest(ArcadeView):
    
    def __init__(self) -> None:
        super().__init__()
        self.lux = Lux(self.width, self.height)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.lux.move_target((x, y))
        # self.lux.shift_blob((dx, dy))
        self.lux.update(self.window.delta_time)

    def on_update(self, delta_time: float) -> bool | None:
        self.lux.update(delta_time)

    def on_fixed_update(self, delta_time: float) -> None:
        print(1/delta_time, self.window.time)

    def on_draw(self) -> bool | None:
        self.clear()
        self.window.ctx.point_size = 20
        self.lux.debug_draw()