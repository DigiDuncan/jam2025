import arcade
import numpy as np

from arcade import Vec2, Sprite, Texture
from arcade.types import Point2
from arcade.math import smerp_2d
from PIL import Image

from .settings import settings

from jam2025.lib.webcam import Webcam
from jam2025.lib.logging import logger
from jam2025.lib.procedural_animator import SecondOrderAnimatorKClamped
from jam2025.lib.utils import frame_data_to_image, rgb_to_l

class SimpleAnimatedWebcamDisplay:
    # !! This assumes the webcam is connected and reading
    # !! only one display works per webcam since reading the frame is destructive
    ANIMATION_SPEED = 0.1

    def __init__(self, webcam: Webcam) -> None:
        self.webcam: Webcam = webcam
        self.webcam_size: Point2 = webcam.size

        self.target_position: Point2 = (0.0, 0.0)
        self.target_size: Point2 = self.webcam_size
        self.max_size: Point2 = self.webcam_size

        self.frame = None

        self.sprite: Sprite = Sprite()

    def _update_texture(self):
        frame = self.webcam.get_frame()
        if frame is None:
            return
        self.frame = frame
        img = frame_data_to_image(frame).convert("RGBA")
        tex = Texture(img)
        size = self.sprite.size
        self.sprite.texture = tex
        self.sprite.size = size # type: ignore -- should be Point2 not Point
        
    def contains_point(self, point: Point2):
        return (
            self.sprite.left <= point[0] <= self.sprite.right and
            self.sprite.bottom <= point[1] <= self.sprite.top
        )

    def update_max_size(self, max_size: Point2):
        w, h = max_size
        if self.webcam_size[0] < w:
            w = self.webcam_size[0]

        if self.webcam_size[1] < h:
            h = self.webcam_size[1]

        ratio = self.webcam_size[0] / self.webcam_size[1]
        self.max_size = w, h
        if h * ratio < w: # on ratio width fits within max_width
            self.target_size = h * ratio, h
        else:
            self.target_size = w, w / ratio

    def update(self, delta_time: float):
        x, y = self.sprite.position
        tx, ty = self.target_position
        if abs(x - tx) > 1.0 or abs(y - ty) > 1.0:
            self.sprite.position = smerp_2d(
                self.sprite.position,
                self.target_position,
                delta_time,
                SimpleAnimatedWebcamDisplay.ANIMATION_SPEED
            )

        w, h = self.sprite.size # type: ignore -- should be Point2 not Point
        tw, th = self.target_size
        if abs(w - tw) > 1.0 or abs(h - th) > 1.0:
            self.sprite.size = smerp_2d(
                self.sprite.size, # type: ignore -- should be Point2 not Point
                self.target_size,
                delta_time,
                SimpleAnimatedWebcamDisplay.ANIMATION_SPEED
            )

        self._update_texture()


class WebcamController:
    def __init__(self, index: int, name: str, scaling: int = 1, region: arcade.Rect | None = None, bounds: arcade.Rect | None = None) -> None:
        self.webcam = Webcam(index)
        self.webcam.connect(start_reading=True)

        self.name = name
        self.scaling = scaling

        size = self.size
        center = size / 2.0
        self.sprite = arcade.Sprite(None, 1.0, *center)
        self.sprite.size = size
        self.crunchy_sprite = arcade.Sprite(None, 1.0, *center)
        self.crunchy_sprite.size = size

        self.region: arcade.Rect = region or arcade.XYWH(*center, *size)
        self.bounds: arcade.Rect = bounds or arcade.LRBT(0.0, 1.0, 0.0, 1.0)
        self.capture: arcade.Rect = arcade.LBWH(0, 0, size[0], size[1])

        self.spritelist: arcade.SpriteList[arcade.Sprite] = arcade.SpriteList()
        self.spritelist.append(self.sprite)

        self._fetched_frame: np.ndarray | None = np.zeros((1, 1, 3), np.int64)
        self._pixel_found = False
        self._raw_cursor: tuple[int, int] | None = None
        self._cursor: tuple[int, int] | None = None
        self._mapped_cursor: tuple[int, int] | None = None
        self._highest_l: int | None = None
        self._cloud = []
        self._no_pixel_time = 0.0

        self._threshold = settings.capture_threshold
        self._downsample = settings.capture_downsample
        self._top_pixels = settings.capture_count

        self._frequency = settings.motion_frequency
        self._dampening = settings.motion_dampening
        self._response = settings.motion_response

        self.timeout = 1.0

        self.flip = False
        self.show_lightness = False
        self.force_debug = False

        self.animator = SecondOrderAnimatorKClamped(self._frequency, self._dampening, self._response, Vec2(0, 0), Vec2(0, 0), 0)  # type: ignore -- Animatable

        settings.register_refresh_func(self._refresh_nonanimator_settings, ("capture_threshold", "capture_downsample", "capture_count"))
        settings.register_refresh_func(self._refresh_animator_settings, ("motion_frequency", "motion_dampening", "motion_response"))

    @property
    def size(self) -> Vec2:
        if not self.webcam.connected:
            return Vec2(1, 1)
        return Vec2(*self.webcam.size) * self.scaling

    @property
    def raw_cursor(self) -> Point2 | None: return self._raw_cursor
    @property
    def cursor(self) -> Point2 | None: return self._cursor
    @property
    def mapped_cursor(self) -> Point2 | None: return self._mapped_cursor
    @property
    def cloud(self): return self._cloud

    @property
    def threshold(self) -> int: return self._threshold
    @threshold.setter
    def threshold(self, v: int) -> None: self._threshold = v

    @property
    def downsample(self) -> int: return self._downsample
    @downsample.setter
    def downsample(self, v: int) -> None: self._downsample = v

    @property
    def top_pixels(self) -> int: return self._top_pixels
    @top_pixels.setter
    def top_pixels(self, v: int) -> None: self._top_pixels = v

    @property
    def frequency(self) -> float: return self._frequency

    @frequency.setter
    def frequency(self, v: float) -> None:
        self._frequency = v
        self.animator.update_values(self._frequency, self._dampening, self._response)

    @property
    def dampening(self) -> float: return self._dampening

    @dampening.setter
    def dampening(self, v: float) -> None:
        self._dampening = v
        self.animator.update_values(self._frequency, self._dampening, self._response)

    @property
    def response(self) -> float: return self._response

    @response.setter
    def response(self, v: float) -> None:
        self._response = v
        self.animator.update_values(self._frequency, self._dampening, self._response)

    def _refresh_animator(self) -> None:
        self.animator = SecondOrderAnimatorKClamped(self._frequency, self._dampening, self._response, Vec2(*self._raw_cursor) if self._raw_cursor else Vec2(0, 0), Vec2(*self._raw_cursor) if self._raw_cursor else Vec2(0, 0), 0)

    def map_position(self, position: Point2) -> Vec2:
        x, y = position

        rl, rb = self.region.bottom_left
        rw, rh = self.region.size

        bl, bb = self.bounds.bottom_left
        bw, bh = self.bounds.size

        cw, ch = self.capture.size

        xf = rl + rw / bw * (x / cw - bl)
        yf = rb + rh / bh * (y / ch - bb)
        return Vec2(xf, yf)

    def unmap_position(self, position: Point2) -> Vec2:
        x, y = position

        rl, rb = self.region.bottom_left
        rw, rh = self.region.size

        bl, bb = self.bounds.bottom_left
        bw, bh = self.bounds.size

        cw, ch = self.capture.size

        xf = (bw/rw * (x - rl) + bl) * cw
        yf = (bh/rh * (y - rb) + bb) * ch
        return Vec2(xf, yf)

    def _get_frame_data(self) -> np.ndarray | None:
        frame = self.webcam.get_frame()
        if frame is None:
            frame = self._fetched_frame
        else:
            self._fetched_frame = frame
            self.capture = arcade.LBWH(0, 0, frame.shape[1], frame.shape[0])
            l, b = self.map_position((0.0, 0.0))
            r, t = self.map_position(self.capture.size)
            rect = arcade.LRBT(l, r, b, t)
            self.sprite.position = self.crunchy_sprite.position = rect.center
            self.sprite.size = self.crunchy_sprite.size = rect.size
        if self.flip:
            frame = np.fliplr(frame)
        return frame

    def _read_frame(self, downsample: int = 1) -> Image.Image | None:
        frame = self._get_frame_data()
        if frame is not None and downsample != 1:
            frame = frame[::downsample, ::downsample]
        if frame is not None:
            i = frame_data_to_image(frame)
            return i

    def get_brightest_pixel(self, threshold: int = 230, downsample: int = 8) -> tuple[int, int] | None:
        """You'd think this is the most expensive function, but it's not!"""
        frame = self._get_frame_data()
        if frame is not None and downsample != 1:
            frame = frame[::downsample, ::downsample]
        if frame is None:
            self._pixel_found = False
            return None

        # Use numpy to quickly get shaped array of brightness
        brightness: np.ndarray = rgb_to_l(frame[:, :, 0], frame[:, :, 1], frame[:, :, 2])
        # Get a numpy conditional mask (shaped array of 0s and 1s)
        thresholded_values = brightness >= threshold
        # Get the y idx and x idx of every pixel above the threshold
        bi = thresholded_values.nonzero()

        # Get the brightness values for each pixel position
        brightest = brightness[bi]

        # Turn the pixel indices into their positions by stiching and flipping the y coord
        positions = np.c_[bi[::-1]]
        positions[:, 1] = frame.shape[0] - positions[:, 1]

        # sort by the brightest pixels, but get the indices needed so the brightness and positions can be sorted
        sorting = np.argsort(brightest)[::-1]

        # get the top n brightest pixels
        top = sorting[:self._top_pixels]
        positions = positions[top]
        brightest = brightest[top]

        if positions.size > 0:
            average_position = np.mean(positions, axis=0)
            self._cloud = tuple(zip(positions, brightest))
        else:
            average_position = (0.0, 0.0)
            self._cloud = ()

        try:
            if self._cloud:
                self._highest_l = brightest[0]
            self._pixel_found = True
            bp = (int(average_position[0] * downsample * self.scaling), int(average_position[1] * downsample * self.scaling))
            return bp
        except Exception as exception:  # noqa: BLE001
            logger.exception(exception)
            self._pixel_found = False
            return None

    def _refresh_nonanimator_settings(self) -> None:
        self.threshold = settings.capture_threshold
        self.downsample = settings.capture_downsample
        self.top_pixels = settings.capture_count
        print(f"updating webcam controller {self.threshold}, {self.downsample}, {self.top_pixels}")

    def _refresh_animator_settings(self) -> None:
        self.frequency = settings.motion_frequency
        self.dampening = settings.motion_dampening
        self.response = settings.motion_response

    def update(self, delta_time: float) -> None:
        frame_data = self._get_frame_data()
        frame = frame_data_to_image(frame_data) if frame_data is not None else None
        crunchy_frame = frame_data_to_image(frame_data[::self._downsample, ::self._downsample]) if frame_data is not None else None

        if frame is not None and crunchy_frame is not None:
            frame = frame.convert("RGBA")
            if self.show_lightness:
                frame = frame.convert("L").convert("RGBA")
            tex = arcade.Texture(frame)
            self.sprite.texture = tex

            crunchy_frame = crunchy_frame.convert("RGBA")
            if self.show_lightness:
                crunchy_frame = crunchy_frame.convert("L").convert("RGBA")
            crunchy_tex = arcade.Texture(crunchy_frame)
            self.crunchy_sprite.texture = crunchy_tex
        self._raw_cursor = self.get_brightest_pixel(self._threshold, self._downsample)
        if self._cursor is None and self._raw_cursor:
            self._refresh_animator()
        if self._raw_cursor:
            self._no_pixel_time = 0.0
            self._cursor = self.animator.update(delta_time, Vec2(*self._raw_cursor))
            self._mapped_cursor = self.map_position(self._cursor)
        else:
            self._no_pixel_time += delta_time
            if self._no_pixel_time >= self.timeout:
                self._cursor = None

    def debug_draw(self) -> None:
        if self.raw_cursor:
            pos = self.map_position(self.raw_cursor)
            arcade.draw_point(*pos, (255, 0, 0), 10)
            cloud = [self.map_position((x[0][0] * self.downsample, x[0][1] * self.downsample)) for x in self.cloud]
            arcade.draw_points(cloud, arcade.color.BLUE, 3)
        if self.cursor:
            pos = self.map_position(self.cursor)
            arcade.draw_point(*pos, (0, 255, 0), 10)

        arcade.draw_rect_outline(self.region, (255, 255, 255), 15)
        l, b = self.map_position((0.0, 0.0))
        r, t = self.map_position(self.capture.size)
        arcade.draw_rect_outline(arcade.LRBT(l, r, b, t), (255, 0, 0), 10)

    def draw(self) -> None:
        self.spritelist.draw()
        if settings.debug or self.force_debug:
            self.debug_draw()
