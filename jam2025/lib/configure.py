from pathlib import Path
from typing import Self

class Config:

    def __init__(self) -> None:
        self._webcam_idx: int = 0
        self._webcam_fps: int = 30
        self._webcam_width: int = 0
        self._webcam_height: int = 0

        self._processing_downscale: int = 4
        self._processing_threshold: int = 245

    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        pass

    def to_file(self, file_path: Path):
        pass