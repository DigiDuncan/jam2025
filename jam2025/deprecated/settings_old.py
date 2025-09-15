from __future__ import annotations
from collections.abc import Callable, Sequence
from weakref import WeakMethod
from logging import getLogger
from pathlib import Path
from typing import Any, Self

logger = getLogger("jam2025")

class _Setting[V]:

    def __init__(self, default: V):
        self._name: str = "*"
        self._value: V = default

    def __set_name__(self, owner: type[_Settings], name: str):
        # Geting the setting name for the listeners to get updated
        # We also use this opertunity to register ourselves for reading/writing
        self._name = name

    def __get__(self, obj: _Settings, objtype: type[_Settings] | None = None) -> V:
        return self._value

    def __set__(self, obj: _Settings, value: V) -> None:
        if value == self._value:
            pass # Should we ignore when the value doesn't change?
        self._value = value
        obj.refresh(self._name)

type RefreshFunc = Callable[[], Any] # No args, any return value (generally None)
type WeakRefreshFunc = WeakMethod[RefreshFunc]


class _Settings:
    screen_width: _Setting[int] = _Setting(1280)
    screen_height: _Setting[int] = _Setting(720)
    screen_fps: _Setting[int] = _Setting(240)

    device_id: _Setting[int] = _Setting(0)
    device_name: _Setting[str] = _Setting("USB Video Device")

    threshold: _Setting[int] = _Setting(245)
    downsample: _Setting[int] = _Setting(8)
    polled_points: _Setting[int] = _Setting(50)

    frequency: _Setting[float] = _Setting(2.0)
    dampening: _Setting[float] = _Setting(1.8)
    response: _Setting[float] = _Setting(-0.5)

    webcam_width: _Setting[int] = _Setting(1280)
    webcam_height: _Setting[int] = _Setting(720)
    webcam_fps: _Setting[int] = _Setting(30)
    webcam_exposure: _Setting[float] = _Setting(-5.0)

    def __init__(self) -> None:
        self._registered_refresh_funcs: dict[WeakRefreshFunc, Sequence[str] | None] = {}
        self._refresh_func_mapping: dict[str, list[WeakRefreshFunc]] = {} # Could this be a default dict? yes. I don't care.

    def refresh(self, name: str) -> None:
        functions = self._refresh_func_mapping.get(name, []) + self._refresh_func_mapping.get("*", [])

        for function in functions:
            function()() # dereference weakrefs and call function

    def register_refresh_func(self, f: RefreshFunc, mask: Sequence[str] = ()) -> None:
        w = WeakMethod(f, self._cleanup_refresh_func) # Make a weakref to protect against ugly reference nightmares
        if w in self._registered_refresh_funcs:
            # function already been registered so we need to update masks
            old_mask = self._registered_refresh_funcs[w]
            if mask == old_mask:
                return # No need to continue updating mask
            self._remove_mask(w, old_mask)

        self._registered_refresh_funcs[w] = mask
        self._add_mask(w, mask)

    def _cleanup_refresh_func(self, w: WeakRefreshFunc) -> None:
        # We need to use a special private cleanup method because:
        # a) logging when weakref cleanup happens
        # b) the original the weakmethod is passed in not the function
        mask = self._registered_refresh_funcs[w]
        logger.info(f"cleaning up refresh func {w} with mask {mask}")
        self._remove_mask(w, mask)

    def _remove_mask(self, w: WeakRefreshFunc, mask: Sequence[str] | None) -> None:
        if mask is None:
            self._refresh_func_mapping["*"].remove(w)
            return
        for name in mask:
            self._refresh_func_mapping[name].remove(w)

    def _add_mask(self, w: WeakRefreshFunc, mask: Sequence[str] | None) -> None:
        # Yeah I know about default dict but idk something about it feels stinky
        if mask is None:
            l = self._refresh_func_mapping.get("*", [])
            l.append(w)
            self._refresh_func_mapping["*"] = l
            return
        for name in mask:
            l = self._refresh_func_mapping.get(name, [])
            l.append(w)
            self._refresh_func_mapping[name] = l

    def deregister_refresh_func(self, f: RefreshFunc) -> None: 
        w = WeakMethod(f)
        if w not in self._registered_refresh_funcs:
            return
        mask = self._registered_refresh_funcs.pop(w)
        self._remove_mask(mask)

    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        raise NotImplementedError

    def to_file(self, file_path: Path) -> None:
        raise NotImplementedError

SETTINGS = _Settings()
