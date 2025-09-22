from typing import Any
from arcade import get_window, View

from jam2025.core.ui.splashscreen import SplashView

__all__ = (
    "Transition",
)

class Transition:

    def __init__(self, views: dict[str, tuple[type[View], bool]] | None = None):
        views = views or {}
        self._views: dict[str, type] = {}
        self._persistent: dict[str, View | None] = {}

        self.add_views(views)

    @property
    def available_views(self) -> tuple[str, ...]:
        return tuple(self._views.keys())

    def add_view(self, name: str, typ: type[View], persistent: bool = False, view: View | None = None) -> None:
        if name in self._views:
            raise KeyError(f"{name} is already a registered view")

        self._views[name] = typ
        if persistent or view:
            self._persistent[name] = view

    def add_views(self, views: dict[str, tuple[type[View], bool]]) -> None:
        for name, (view, persistent) in views.items():
            self.add_view(name, view, persistent)

    def show_view(self, name: str, *args: Any, show_splash: bool = False, **kwds: Any) -> None:
        if name not in self._views:
            raise KeyError(f"{name} is not a registered view")

        typ = self._views[name]
        if show_splash:
            splash_view = SplashView(typ, args, kwds)
            get_window().show_view(splash_view)
            return

        if name not in self._persistent:
            view = typ(*args, **kwds)
        else:
            view = self._persistent[name]
            if view is None:
                view = typ()
                self._persistent[name] = view
        get_window().show_view(view)

