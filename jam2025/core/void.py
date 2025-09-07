import arcade
from arcade.clock import GLOBAL_CLOCK
from arcade.experimental.shadertoy import Shadertoy
from arcade.types import RGBA255

class Void:
    SHADER = """void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;
    vec3 r = vec3(uv, 1.0);
    vec4 o = vec4(0.3);
    float t = iTime;
    vec3 p;

    for (float i = 0.0, z = 0.0, d; i < 100.0; i++) {
        // Ray direction, modulated by time and camera
        p = z * normalize(vec3(uv, 0.5));
        p.z += t;

        // Rotating plane using a cos matrix
        vec4 angle = vec4(12.0, 33.0, 11.0, 0.0);
        vec4 a = z - 0.2 + t * 0.1 - angle;
        p.xy *= mat2(cos(a.x), -sin(a.x), tan(a.x), cos(a.x));

        // Distance estimator
        z += d = length(sin(p + cos(p.yzx + p.z - t * 0.2)).xy) / 6.0;

        // Color accumulation using sin palette
        o += (cos(p.x + t + vec4(10.0, 22.0, 3.0, 0.0)) + 2.0) / d;
    }

    o = tanh(o / 5000.0);
    fragColor = vec4(o.rgb, 1.0);
}
"""

    def __init__(self, region: arcade.Rect) -> None:
        """https://www.shadertoy.com/view/3XG3WK"""
        self.region = region
        self.shadertoy = Shadertoy((region.width, region.height), Void.SHADER)
        self.overlay_color: RGBA255 = (0, 0, 0, 255 - 32)

    def draw(self) -> None:
        self.shadertoy.render(time = GLOBAL_CLOCK.time)
        arcade.draw_rect_filled(arcade.get_window().rect, self.overlay_color)
