from __future__ import annotations
from collections.abc import Callable, Sequence
from weakref import WeakMethod
from typing import Any
from pathlib import Path
from sys import platform
from tomllib import load
from tomli_w import dump

from jam2025.lib.logging import logger
from jam2025.lib.webcam import Webcam


__all__ = (
    "settings",
)

type RefreshFunc = Callable[[], Any] # No args, any return value (generally None)
type WeakRefreshFunc = WeakMethod[RefreshFunc]

class _Settings:

    def __init__(self, values: dict[str, Any]) -> None:
        self._refresh_functions: dict[WeakRefreshFunc, set[str] | None] = {}

        # Context values (change during run time and are none-able)
        # ! I didn't want to add even more global state in another singleton
        self.connected_webcam: Webcam | None = None
        self.skipped_capture_consent: bool = True

        # Config (change during development)
        self.window_width: int
        self.window_height: int
        self.window_name: str
        self.window_fullscreen: bool
        self.window_fps: int
        self.window_tps: int
        
        self.initial_view: str
        self._platform: str = platform

        self.motion_frequency: float
        self.motion_dampening: float
        self.motion_response: float

        # Calibration (unique to each webcam / device)
        self.webcam_name: str
        self.webcam_id: int
        self.webcam_width: int
        self.webcam_height: int
        self.webcam_exposure: float
        self.webcam_flip: bool
        self.webcam_bounds: tuple[float, float, float, float]
        self.webcam_dshow: bool
        
        self.capture_threshold: int
        self.capture_downsample: int
        self.capture_count: int

        # Settings (set by player)
        self.master_volume: float
        self.sfx_volume: float
        self.music_volume: float
        self.ui_volume: float

        self.update_values(**values)

    # -- SETTINGS OBSERVER CODE --

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)
        if name.startswith('_'):
            return
        
        for func, mask in self._refresh_functions.items():
            if mask is None or name in mask:
                func()() # type: ignore -- because it's a weakref we have to deref it first

    def update_values(self, **kwds: Any):
        for name, value in kwds.items():
            object.__setattr__(self, name, value)
        updated = set(kwds)
        for func, mask in self._refresh_functions.items():
            if mask is None or updated.intersection(updated):
                func()() # type: ignore -- because it's a weakref we have to deref it first

    def register_refresh_func(self, f: RefreshFunc, mask: Sequence[str] | None):
        m = None if mask is None else set(mask)
        w = WeakMethod(f, self._clear_function)
        self._refresh_functions[w] = m

    def _clear_function(self, w: WeakRefreshFunc):
        self._refresh_functions.pop(w)
        logger.info(f'refresh function {w} automatically deregistered')

    def deregister_refresh_func(self, f: RefreshFunc):
        w = WeakMethod(f)
        if w not in self._refresh_functions:
            return
        self._refresh_functions.pop(w)

    # -- UTILITY PROPERTIES AND METHODS --

    @property
    def platform(self):
        return self._platform
    
    @property
    def is_windows(self):
        return self._platform == 'win32'
    
    @property
    def has_webcam(self):
        return self.connected_webcam is not None
    
    @property
    def webcam_connected(self):
        return self.connected_webcam is not None and self.connected_webcam.connected
        

type settingMapping = tuple[str, Any]
_MAPPING: dict[str, dict[str, settingMapping]] = {
    "window": {
        "width": ("window_width", 1280),
        "height": ("window_height", 720),
        "fullscreen": ("window_fullscreen", False),
        "name": ("window_name", "GDG jam 2 2025 - Lux: pass the torch"),
        "fps": ("window_fps", 240),
        "tps": ("window_tps", 20),
        "initial_view": ("initial_view", "m_calibration")
    },
    "control": {
        "frequency": ("motion_frequency", 2.0),
        "damping": ("motion_dampening", 1.0),
        "response": ("motion_response", -0.5)
    },
    "volume": {
        "master": ("master_volume", 1.0),
        "sfx": ("sfx_volume", 1.0),
        "music": ("music_volume", 1.0),
        "ui": ("ui_volume", 1.0),
    },
    "webcam": {
        "width": ("webcam_width", 1280),
        "height": ("webcam_height", 720),
        "exposure": ("webcam_exposure", -5.0),
        "use_dshow": ("webcam_dshow", False),
    },
    "calibration": {
        "name": ("webcam_name", "NO DEVICE NAME SET"),
        "id": ("webcam_id", 0),
        "flip": ("webcam_flip", False),
        "bounds": ("webcam_bounds", (0.0, 1.0, 0.0, 1.0)),
        "threshold": ("capture_threshold", 245),
        "downsample": ("capture_downsample", 4),
        "count": ("capture_count", 30),
    },
}

def load_settings() -> _Settings:
    _cfg_path = Path('.cfg')
    if not _cfg_path.exists():
        return create_settings()
    
    with open(_cfg_path, 'rb') as fp:
        toml = load(fp)
    
    values: dict[str, Any] = {}
    for group, data in _MAPPING.items():
        for name, (attr, default) in data.items():
            values[attr] = toml.get(group, {}).get(name, default)

    return _Settings(values)


def create_settings() -> _Settings:
    values: dict[str, Any] = {}
    for data in _MAPPING.values():
        for (attr, default) in data.values():
            values[attr] = default
    return _Settings(values)


def write_settings(settings: _Settings, dump_toml: bool = True):
    toml: dict[str, Any] = {}
    for group, data in _MAPPING.items():
        toml[group] = {}
        for name, (attr, _) in data.items():
            toml[group][name] = settings.__getattribute__(attr)

    if not dump_toml:
        return toml

    _cfg_path = Path('.cfg')
    with open(_cfg_path, 'wb+') as fp:
        dump(toml, fp)
    return toml

settings = load_settings()