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

type WebcamState = int
class Webcam:
    DISCONNECTED: WebcamState = 0 # thread has not started
    CONNECTING: WebcamState = 1 # has found camera but hasn't gotten first frame
    CONNECTED: WebcamState = 2 # has found camera and has properties
    ERROR: WebcamState = 3 # Something broke relating to the webcam

    # I'm unsure what cv2.CAP_DSHOW means, but it seems to speed up camera reading?
    def __init__(self, index: int = 0, dshow: bool = True):
        self._index: int = index
        self._dshow: bool = dshow
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

    def disconnect(self, block: bool = False):
        with self._data_lock:
            print('set disconnect')
            self._webcam_disconnect = True
        if block:
            print('started blocking')
            # Block the disconnect thread until the disconnect msg has been recieved.
            # This might be unsafe as there is no timeout, but it's only unsafe
            # If I have fucked up.
            self._thread.join()
            print('finished blocking')

    def _disconnect(self):
        # This is also run in the thread if we have to wait to disconnect
        # so this has to be a seperate call.
        print('disconnecting')
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
        print('finished disconnecting')
        

    def reconnect(self, start_reading: bool = False):
        # Disconnect the camera, and block until that is done, then reconnect.
        self.disconnect(block=True)
        with self._data_lock:
            force_disconnect = self._webcam_state != Webcam.DISCONNECTED
        if force_disconnect:
            self._disconnect()
            print('Problem disconnecting webcam, probably encountered an error')
        print('reconnecting')
        self.connect(start_reading)

    def set_read(self, read: bool):
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
        print('thread started')
        with self._data_lock:
            try:
                idx = self._index + cv2.CAP_DSHOW if self._dshow else self._index
                self._webcam = cv2.VideoCapture(idx)
                if not self._webcam.isOpened():
                    raise ValueError('Cannot connect to webcam')
            except Exception as e:
                self._webcam_state = Webcam.ERROR
                raise e
            print('connected to webcam')
    
        # We have to exit the data lock to disconnect because it locks internally
        # and if the thread is already holding the lock it will brick. 
        with self._data_lock:
            immediate_disconnect = self._webcam_disconnect
        if immediate_disconnect:
            print('connecting interupted')
            self._disconnect()
            return
        
        with self._data_lock:
            try:
                retval, frame = self._webcam.read()
                while not retval:
                    retval, frame = self._webcam.read()
                self._webcam_size = frame.shape[1], frame.shape[0]
                self._webcam_fps = self._webcam.get(cv2.CAP_PROP_FPS)
                if self._webcam_read:
                    self._frames.put(frame)
            except Exception as e:
                self._webcam_state = Webcam.ERROR
                raise e
            else:
                self._webcam_state = Webcam.CONNECTED
            print('finished connecting')
        
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
                print('disconnect found in loop')
                # If we wanted to be really safe we would disconnect even when the window close
                break

            try:
                retval, frame = self._webcam.read()
            except Exception as e:
                self._webcam_state = Webcam.ERROR
                raise e
            
            if not retval:
                # This should maybe set the Webcam state to Error.
                self._frames.put(None)
                print('Failed to read frame.')
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
