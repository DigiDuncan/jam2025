import arcade
import cv2
import queue
import threading
import numpy as np

from arcade import Vec2
from arcade.types import Point2
from PIL import Image

from jam2025.lib.logging import logger
from jam2025.lib.procedural_animator import SecondOrderAnimatorKClamped
from jam2025.lib.settings import SETTINGS
from jam2025.lib.utils import frame_data_to_image, rgb_to_l

from pygrabber.dshow_graph import FilterGraph

def get_available_cameras() -> dict[int, str]:
    """https://stackoverflow.com/questions/70886225/get-camera-device-name-and-port-for-opencv-videostream-python"""
    devices = FilterGraph().get_input_devices()
    available_cameras = {}
    for device_index, device_name in enumerate(devices):
        available_cameras[device_index] = device_name
    return available_cameras


type WebcamState = int
class Webcam:
    DISCONNECTED: WebcamState = 0 # thread has not started
    CONNECTING: WebcamState = 1 # has found camera but hasn't gotten first frame
    CONNECTED: WebcamState = 2 # has found camera and has properties
    ERROR: WebcamState = 3 # Something broke relating to the webcam

    def __init__(self, index: int = 0):
        self._index: int = index
        self._webcam: cv2.VideoCapture | None = None

        # Webcam properties that must be read through the data lock
        self._webcam_size: tuple[int, int] | None = None
        self._webcam_fps: int | None = None
        self._webcam_state: WebcamState = Webcam.DISCONNECTED
        self._webcam_read: bool = False
        self._webcam_disconnect: bool = False

        self._frames: queue.Queue[np.ndarray | None] = queue.Queue()
        self._thread: threading.Thread = threading.Thread(target=self._poll, daemon=True)

        # The data lock prevents race conditions by blocking until the thread
        # releases it.
        self._data_lock: threading.Lock = threading.Lock()

    def connect(self, start_reading: bool = False) -> None:
        with self._data_lock:
            invalid_connection = self._webcam_state != self.DISCONNECTED
        if invalid_connection:
            raise ValueError('Webcam has already been connected, call disconnect first.')
        self._webcam_read = start_reading
        self._thread.start()

    def disconnect(self, block: bool = False) -> None:
        with self._data_lock:
            if self._webcam is None:
                return
            logger.debug('set disconnect')
            self._webcam_disconnect = True
        if block:
            logger.debug('started blocking')
            # Block the disconnect thread until the disconnect msg has been recieved.
            # This might be unsafe as there is no timeout, but it's only unsafe
            # If I have fucked up.
            self._thread.join()
            logger.debug('finished blocking')

    def _disconnect(self) -> None:
        # This is also run in the thread if we have to wait to disconnect
        # so this has to be a seperate call.
        logger.debug('disconnecting')
        with self._data_lock:
            if self._webcam is not None:
                self._webcam.release()
            self._webcam = None

            self._webcam_size = None
            self._webcam_fps = None
            self._webcam_read = False
            self._webcam_disconnect = False

            # Reset the queue and make sure no thread is trying to get from it
            # when it shouldn't.
            self._frames.shutdown(True)
            self._frames = queue.Queue()

            # Dereference the thread and make a new one. I think this is memory safe?
            # This has to be done like this because there is not 'thread ended' callback.
            self._thread = threading.Thread(target=self._poll, daemon=True)

            # This happens last as a safety check. We can't start a thread that
            # has already been started, even if it's dead.
            self._webcam_state: WebcamState = Webcam.DISCONNECTED
        logger.debug('finished disconnecting')


    def reconnect(self, start_reading: bool = False) -> None:
        # Disconnect the camera, and block until that is done, then reconnect.
        self.disconnect(block=True)
        with self._data_lock:
            force_disconnect = self._webcam_state != Webcam.DISCONNECTED
        if force_disconnect:
            logger.debug('Problem disconnecting webcam, probably encountered an error')
            self._disconnect()
        logger.debug('reconnecting')
        self.connect(start_reading)

    def set_read(self, read: bool) -> None:
        with self._data_lock:
            self._webcam_read = True

    def get_frame(self) -> None:
        try:
            frame = self._frames.get(False)
        except queue.Empty:
            frame = None
        finally:
            return frame

    @property
    def state(self) -> WebcamState:
        with self._data_lock:
            return self._webcam_state

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
            return self._webcam_state == Webcam.CONNECTED

    def _poll(self) -> None:
        logger.debug('thread started')
        with self._data_lock:
            try:
                self._webcam = cv2.VideoCapture(self._index)
                if not self._webcam.isOpened():
                    raise ValueError('Cannot connect to webcam')
            except Exception as e:
                self._webcam_state = Webcam.ERROR
                raise e
            logger.debug('connected to webcam')

        # We have to exit the data lock to disconnect because it locks internally
        # and if the thread is already holding the lock it will brick.
        with self._data_lock:
            immediate_disconnect = self._webcam_disconnect
        if immediate_disconnect:
            logger.debug('connecting interupted')
            self._disconnect()
            return

        with self._data_lock:
            self._webcam_size = int(self._webcam.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self._webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._webcam_fps = int(self._webcam.get(cv2.CAP_PROP_FPS))
            self._webcam_state = Webcam.CONNECTED

            # print("cv2.CAP_PROP_FRAME_WIDTH))", self._webcam.get(cv2.CAP_PROP_FRAME_WIDTH)) # Static (for my camera)
            # print("cv2.CAP_PROP_FRAME_HEIGHT))", self._webcam.get(cv2.CAP_PROP_FRAME_HEIGHT)) # Static (for my camera)
            # print("cv2.CAP_PROP_FPS))", self._webcam.get(cv2.CAP_PROP_FPS)) # Controlable (for my camera)
            # print("cv2.CAP_PROP_FOURCC))", self._webcam.get(cv2.CAP_PROP_FOURCC)) # Static (for my camera, do we care about it.)
            # print("cv2.CAP_PROP_BRIGHTNESS))", self._webcam.get(cv2.CAP_PROP_BRIGHTNESS))
            # print("cv2.CAP_PROP_CONTRAST))", self._webcam.get(cv2.CAP_PROP_CONTRAST))
            # print("cv2.CAP_PROP_SATURATION))", self._webcam.get(cv2.CAP_PROP_SATURATION))
            # print("cv2.CAP_PROP_HUE))", self._webcam.get(cv2.CAP_PROP_HUE))
            # print("cv2.CAP_PROP_GAIN))", self._webcam.get(cv2.CAP_PROP_GAIN))
            # print("cv2.CAP_PROP_EXPOSURE))", self._webcam.get(cv2.CAP_PROP_EXPOSURE))
            # print("cv2.CAP_PROP_CONVERT_RGB))", self._webcam.get(cv2.CAP_PROP_CONVERT_RGB))
            # print("cv2.CAP_PROP_WHITE_BALANCE_BLUE_U))", self._webcam.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U))
            # print("cv2.CAP_PROP_RECTIFICATION))", self._webcam.get(cv2.CAP_PROP_RECTIFICATION))
            # print("cv2.CAP_PROP_MONOCHROME))", self._webcam.get(cv2.CAP_PROP_MONOCHROME))
            # print("cv2.CAP_PROP_SHARPNESS))", self._webcam.get(cv2.CAP_PROP_SHARPNESS))
            # print("cv2.CAP_PROP_AUTO_EXPOSURE))", self._webcam.get(cv2.CAP_PROP_AUTO_EXPOSURE))
            # print("cv2.CAP_PROP_GAMMA))", self._webcam.get(cv2.CAP_PROP_GAMMA))
            # print("cv2.CAP_PROP_TEMPERATURE))", self._webcam.get(cv2.CAP_PROP_TEMPERATURE))
            # print("cv2.CAP_PROP_TRIGGER))", self._webcam.get(cv2.CAP_PROP_TRIGGER))
            # print("cv2.CAP_PROP_TRIGGER_DELAY))", self._webcam.get(cv2.CAP_PROP_TRIGGER_DELAY))
            # print("cv2.CAP_PROP_WHITE_BALANCE_RED_V))", self._webcam.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V))
            # print("cv2.CAP_PROP_ZOOM))", self._webcam.get(cv2.CAP_PROP_ZOOM))
            # print("cv2.CAP_PROP_FOCUS))", self._webcam.get(cv2.CAP_PROP_FOCUS))
            # print("cv2.CAP_PROP_GUID))", self._webcam.get(cv2.CAP_PROP_GUID))
            # print("cv2.CAP_PROP_ISO_SPEED))", self._webcam.get(cv2.CAP_PROP_ISO_SPEED))
            # print("cv2.CAP_PROP_BACKLIGHT))", self._webcam.get(cv2.CAP_PROP_BACKLIGHT))
            # print("cv2.CAP_PROP_PAN))", self._webcam.get(cv2.CAP_PROP_PAN))
            # print("cv2.CAP_PROP_TILT))", self._webcam.get(cv2.CAP_PROP_TILT))
            # print("cv2.CAP_PROP_ROLL))", self._webcam.get(cv2.CAP_PROP_ROLL))
            # print("cv2.CAP_PROP_IRIS))", self._webcam.get(cv2.CAP_PROP_IRIS))
            # print("cv2.CAP_PROP_SETTINGS))", self._webcam.get(cv2.CAP_PROP_SETTINGS))
            # print("cv2.CAP_PROP_BUFFERSIZE))", self._webcam.get(cv2.CAP_PROP_BUFFERSIZE))
            # print("cv2.CAP_PROP_AUTOFOCUS))", self._webcam.get(cv2.CAP_PROP_AUTOFOCUS))
            # print("cv2.CAP_PROP_CHANNEL))", self._webcam.get(cv2.CAP_PROP_CHANNEL))
            # print("cv2.CAP_PROP_AUTO_WB))", self._webcam.get(cv2.CAP_PROP_AUTO_WB))
            # print("cv2.CAP_PROP_WB_TEMPERATURE))", self._webcam.get(cv2.CAP_PROP_WB_TEMPERATURE))
            logger.debug('finished connecting')

        if self._webcam_state == Webcam.ERROR:
            # This shouldn't really be possible.
            return

        while True:
            # Could maybe be done with a threading.event but this is fine for now
            with self._data_lock:
                read = self._webcam_read
                disconnect = self._webcam_disconnect

            if not read:
                continue # This will give faster responses than reading and not sending.
            if disconnect:
                logger.debug('disconnect found in loop')
                # If we wanted to be really safe we would disconnect even when the window closed
                # through an error
                break

            try:
                retval, frame = self._webcam.read()
            except Exception as e:
                with self._data_lock:
                    self._webcam_state = Webcam.ERROR
                raise e

            if not retval:
                # This should maybe set the Webcam state to Error.
                with self._data_lock:
                    self._webcam_state = Webcam.ERROR
                raise ValueError('Failed to Read Frame (camera most likely disconnected).')
            else:
                self._frames.put(frame)

        self._disconnect()


class WebcamController:
    def __init__(self, index: int = 0, scaling: int = 1) -> None:
        self.webcam = Webcam(index)
        self.webcam.connect(start_reading=True)

        # Cludge to block until the webcam is active. I will remove later
        while True:
            if self.webcam.connected:
                break

        self.name = "USB Video Device"
        self.scaling = scaling

        size = self.size
        center = size / 2.0
        self.sprite = arcade.SpriteSolidColor(*size, *center)
        self.crunchy_sprite = arcade.SpriteSolidColor(*size, *center)

        self._fetched_frame: np.ndarray | None = np.zeros((self.webcam.size[0], self.webcam.size[1], 3), np.int64)
        self._pixel_found = False
        self._raw_cursor: tuple[int, int] | None = None
        self._cursor: tuple[int, int] | None = None
        self._highest_l: int | None = None
        self._cloud = []
        self._no_pixel_time = 0.0

        self._threshold = SETTINGS.threshold
        self._downsample = SETTINGS.downsample
        self._top_pixels = SETTINGS.polled_points
        self._frequency = SETTINGS.frequency
        self._dampening = SETTINGS.dampening
        self._response = SETTINGS.response

        self.timeout = 1.0

        self.flip = False
        self.show_lightness = False

        self.animator = SecondOrderAnimatorKClamped(self._frequency, self._dampening, self._response, Vec2(0, 0), Vec2(0, 0), 0)  # type: ignore -- Animatable

        SETTINGS.register_refresh_func(self._refresh_nonanimator_settings, ("threshold", "downsample", "polled_points"))
        SETTINGS.register_refresh_func(self._refresh_animator_settings, ("frequency", "dampening", "response"))

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
            bp = (int(average_pos[0] * downsample * self.scaling), int(average_pos[1] * downsample * self.scaling))
            return bp
        except Exception as _:  # noqa: BLE001
            self._pixel_found = False
            return None

    def _refresh_nonanimator_settings(self) -> None:
        self.threshold = SETTINGS.threshold
        self.downsample = SETTINGS.downsample
        self.top_pixels = SETTINGS.polled_points

    def _refresh_animator_settings(self) -> None:
        self.frequency = SETTINGS.frequency
        self.dampening = SETTINGS.dampening
        self.response = SETTINGS.response

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
