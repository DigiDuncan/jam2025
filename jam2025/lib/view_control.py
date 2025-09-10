from typing import Any
from arcade import get_window, View

__all__ = (
    "Transition",
)

class Transition:

    def __init__(self, views: dict[str, tuple[type[View], bool]] = None):
        views = views or {}
        self._views: dict[str, type] = {}
        self._persistent: dict[str, View | None] = {}

        self.add_views(views)

    @property
    def available_views(self) -> tuple[str, ...]:
        return tuple(self._views.keys())

    def add_view[T: View](self, name: str, typ: type[T], persistent: bool = False, view: T | None = None) -> None:
        if name in self._views:
            raise KeyError(f"{name} is already a registered view")

        self._views[name] = typ
        if persistent or view:
            self._persistent[name] = view

    def add_views(self, views: dict[str, tuple[type[View], bool]]) -> None:
        for name, (view, persistent) in views.items():
            self.add_view(name, view, persistent)

    def show_view(self, name: str, *args: Any, **kwds: Any) -> None:
        if name not in self._views:
            raise KeyError(f"{name} is not a registered view")

        typ = self._views[name]
        if name not in self._persistent:
            view = typ(*args, **kwds)
        else:
            view = self._persistent[name]
            if view is None:
                view = typ()
                self._persistent[name] = view
        get_window().show_view(view)

