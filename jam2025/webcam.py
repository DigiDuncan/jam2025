import cv2
import queue
import threading
import numpy as np

class WebCam:
    
    def __init__(self):
        self._webcam: cv2.VideoCapture | None = None
        self._webcam_size: tuple[int, int] | None = None
        self._webcam_fps: int | None = None

        self._frames: queue.Queue[np.ndarray | None] = queue.Queue()
        self._thread: threading.Thread = threading.Thread(target=self._poll, daemon=True)
        self._data_lock: threading.Lock = threading.Lock()

    def connect(self):
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

    def _poll(self):
        with self._data_lock:
            self._webcam = cv2.VideoCapture(0)
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
