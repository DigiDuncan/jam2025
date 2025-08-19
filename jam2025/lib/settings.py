from collections.abc import Callable, Sequence
from typing import Any


class _Settings:
    def __init__(self) -> None:
        self._registered_refresh_funcs: dict[Callable, Sequence[str] | None] = {}

        self.device_id: int = 0
        self.device_name: str = "USB Video Device"

        self.threshold: int = 245
        self.downsample: int = 8
        self.polled_points: int = 50
        self.exposure: int = -5

        self.frequency: float = 2.0
        self.dampening: float = 1.8
        self.response: float = -0.5

        self.x_min: int = 0
        self.x_max: int = 1280
        self.y_min: int = 0
        self.y_max: int = 720

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if not name.startswith("_"):
            for f, mask in self._registered_refresh_funcs.items():
                if not mask or name in mask:
                    f()

    def register_refresh_func(self, f: Callable, mask: Sequence[str] = ()) -> None:
        if f not in self._registered_refresh_funcs:
            self._registered_refresh_funcs[f] = mask

SETTINGS = _Settings()
