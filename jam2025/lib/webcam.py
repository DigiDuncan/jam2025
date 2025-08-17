import arcade
import cv2
import queue
import threading
import numpy as np

from arcade import Vec2
from arcade.types import Point2
from PIL import Image

from jam2025.lib.procedural_animator import SecondOrderAnimatorKClamped
from jam2025.lib.utils import frame_data_to_image, rgb_to_l

class Webcam:
    def __init__(self, index: int = 0):
        self._index: int = index
        self._webcam: cv2.VideoCapture | None = None
        self._webcam_size: tuple[int, int] | None = None
        self._webcam_fps: int | None = None

        self._frames: queue.Queue[np.ndarray | None] = queue.Queue()
        self._thread: threading.Thread = threading.Thread(target=self._poll, daemon=True)
        self._data_lock: threading.Lock = threading.Lock()

    def connect(self) -> None:
        self._thread.start()

    def get_frame(self) -> None:
        try:
            frame = self._frames.get(False)
        except queue.Empty:
            frame = None
        finally:
            return frame

    @property
    def size(self) -> tuple[int, int]:
        with self._data_lock:
            if self._webcam_size is None:
                raise ValueError('Webcam is not connected')
            return self._webcam_size

    @property
    def fps(self) -> int:
        with self._data_lock:
            if self._webcam_fps is None:
                raise ValueError('Webcam is not connected')
            return self._webcam_fps

    @property
    def connected(self) -> bool:
        with self._data_lock:
            return self._webcam is not None

    def _poll(self) -> None:
        with self._data_lock:
            self._webcam = cv2.VideoCapture(self._index)
            retval, frame = self._webcam.read()
            while not retval:
                retval, frame = self._webcam.read()
            self._webcam_size = frame.shape[1], frame.shape[0]
            self._webcam_fps = self._webcam.get(cv2.CAP_PROP_FPS)
            self._webcam.set(cv2.CAP_PROP_EXPOSURE, -5)
            self._frames.put(frame)
        while True:
            retval, frame = self._webcam.read()
            if not retval:
                self._frames.put(None)
                print('Failed to read frame.')
            self._frames.put(frame)


class WebcamController:
    def __init__(self, index: int = 0, scaling: int = 1) -> None:
        self.webcam = Webcam(index)
        self.webcam.connect()

        self.name = "USB Video Device"
        self.scaling = scaling

        self.sprite = arcade.SpriteSolidColor(self.size[0], self.size[1], center_x = self.size[0]/2, center_y =  self.size[1]/2)
        self.crunchy_sprite = arcade.SpriteSolidColor(self.size[0], self.size[1], center_x = self.size[0]/2, center_y =  self.size[1]/2)

        self._fetched_frame: np.ndarray | None = self.webcam.get_frame()
        if self._fetched_frame is None:
            raise ValueError('No initial frame found')
        self._pixel_found = False
        self._raw_cursor: tuple[int, int] | None = None
        self._cursor: tuple[int, int] | None = None
        self._highest_l: int | None = None
        self._cloud = []
        self._no_pixel_time = 0.0

        self._threshold = 245
        self._downsample = 4
        self._top_pixels = 50
        self._frequency = 2.0
        self._dampening = 1.8
        self._response = -0.5

        self.timeout = 1.0

        self.flip = False
        self.show_lightness = False

        self.animator = SecondOrderAnimatorKClamped(self._frequency, self._dampening, self._response, Vec2(0, 0), Vec2(0, 0), 0)  # type: ignore -- Animatable

    @property
    def size(self) -> Vec2:
        return Vec2(*self.webcam.size) * self.scaling

    @property
    def raw_cursor(self) -> Point2 | None: return self._raw_cursor
    @property
    def cursor(self) -> Point2 | None: return self._cursor
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
        self._refresh_animator()

    @property
    def dampening(self) -> float: return self._dampening

    @dampening.setter
    def dampening(self, v: float) -> None:
        self._dampening = v
        self._refresh_animator()

    @property
    def response(self) -> float: return self._response

    @response.setter
    def response(self, v: float) -> None:
        self._response = v
        self._refresh_animator()

    def _refresh_animator(self) -> None:
        self.animator = SecondOrderAnimatorKClamped(self._frequency, self._dampening, self._response, Vec2(*self._raw_cursor) if self._raw_cursor else Vec2(0, 0), Vec2(*self._raw_cursor) if self._raw_cursor else Vec2(0, 0), 0)

    def _get_frame_data(self) -> np.ndarray | None:
        frame = self.webcam.get_frame()
        if frame is None:
            frame = self._fetched_frame
        else:
            self._fetched_frame = frame
        frame = frame[:, :, ::-1]  # The camera data is BGR for some reason
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
        # Get array of x and y indices
        bi = thresholded_values.nonzero()
        # Create bright pixel list (Could use numpy to make this cleaner but that doesn't really matter)
        brightest_pixels = [((x, frame.shape[0] - y), brightness[y, x]) for y, x in zip(bi[0], bi[1], strict = True)]
        brightest_pixels.sort(reverse=True, key = lambda x: x[1])
        self._cloud = brightest_pixels[:self._top_pixels]
        average_pos = np.mean(np.array([x[0] for x in self._cloud]), axis=0)

        try:
            if brightest_pixels:
                self._highest_l = brightest_pixels[0][1]
            self._pixel_found = True
            return (int(average_pos[0] * downsample * self.scaling), int(average_pos[1] * downsample * self.scaling))
        except Exception as _:  # noqa: BLE001
            self._pixel_found = False
            return None

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
            self.sprite.size = self.size

            crunchy_frame = crunchy_frame.convert("RGBA")
            if self.show_lightness:
                crunchy_frame = crunchy_frame.convert("L").convert("RGBA")
            crunchy_tex = arcade.Texture(crunchy_frame)
            self.crunchy_sprite.texture = crunchy_tex
            self.crunchy_sprite.size = self.size
        self._raw_cursor = self.get_brightest_pixel(self._threshold, self._downsample)
        if self._cursor is None and self._raw_cursor:
            self._refresh_animator()
        if self._raw_cursor:
            self._no_pixel_time = 0.0
            self._cursor = self.animator.update(delta_time, Vec2(*self._raw_cursor))
        else:
            self._no_pixel_time += delta_time
            if self._no_pixel_time >= self.timeout:
                self._cursor = None
