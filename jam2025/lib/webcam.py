import cv2
import queue
import threading

import numpy as np 

from .logging import logger

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
            if self._webcam_state == Webcam.ERROR:
                self._disconnect()

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

    def get_frame(self) -> np.ndarray | None:
        try:
            frame = self._frames.get(False)
            return frame
        except queue.Empty:
            return None

    # -- WEBCAM ATTRIBUTE PROPERTIES --

    @property
    def index(self) -> int:
        return self._index

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
    
    # -- STATE PROPERTIES --

    @property
    def state(self) -> WebcamState:
        with self._data_lock:
            return self._webcam_state

    @property
    def disconnected(self) -> bool:
        with self._data_lock:
            return self._webcam_state == Webcam.DISCONNECTED

    @property
    def connecting(self) -> bool:
        with self._data_lock:
            return self._webcam_state == Webcam.CONNECTING

    @property
    def connected(self) -> bool:
        with self._data_lock:
            return self._webcam_state == Webcam.CONNECTED

    @property
    def failed(self) -> bool:
        with self._data_lock:
            return self._webcam_state == Webcam.ERROR

    # -- THREAD METHOD --

    def _poll(self) -> None:
        logger.debug('thread started')
        try:
            webcam = cv2.VideoCapture(self._index)
            if not webcam.isOpened():
                raise ValueError('Cannot connect to webcam')
        except Exception as e:
            with self._data_lock:
                self._webcam_state = Webcam.ERROR
            raise e
        logger.debug('connected to webcam')

        with self._data_lock:
            self._webcam = webcam

        # We have to exit the data lock to disconnect because it locks internally
        # and if the thread is already holding the lock it will brick.
        with self._data_lock:
            immediate_disconnect = self._webcam_disconnect
        if immediate_disconnect:
            logger.debug('connecting interupted')
            self._disconnect()
            return

        # self._webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self._webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        try:
            size = int(self._webcam.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self._webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps =  int(self._webcam.get(cv2.CAP_PROP_FPS))
        except Exception as e:
            with self._data_lock:
                self._webcam_state = Webcam.ERROR
            raise e

        with self._data_lock:
            self._webcam_size = size
            self._webcam_fps = fps
            self._webcam_state = Webcam.CONNECTED

            # print("cv2.CAP_PROP_FRAME_WIDTH))", self._webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
            # print("cv2.CAP_PROP_FRAME_HEIGHT))", self._webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # print("cv2.CAP_PROP_FPS))", self._webcam.get(cv2.CAP_PROP_FPS))
            # print("cv2.CAP_PROP_FOURCC))", self._webcam.get(cv2.CAP_PROP_FOURCC))
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
                with self._data_lock:
                    self._webcam_state = Webcam.ERROR
                raise ValueError('Failed to Read Frame (camera most likely disconnected).')
            frame = frame[:, :, ::-1]
            self._frames.put(frame) # Flip the BGR to RGB on thread

        self._disconnect()
