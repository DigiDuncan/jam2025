# This is done the "bad" way.

import importlib.resources as pkg_resources
from arcade import Texture, Sound, load_texture as _load_texture, load_sound as _load_sound, load_font as _load_font
from jam2025 import data
from jam2025.lib.gif import GIF

def load_texture(name: str, ext: str = "png") -> Texture:
    with pkg_resources.path(data) as p:
        return _load_texture(p / "images" / f"{name}.{ext}")

def load_spritesheet(name: str, rows: int, cols: int, frames: int, fps: float, ext: str = "png") -> GIF:
    with pkg_resources.path(data) as p:
        return GIF(p / "images" / f"{name}.{ext}", rows, cols, frames, fps)

def load_music(name: str, ext: str = "wav") -> Sound:
    with pkg_resources.path(data) as p:
        return _load_sound(p / "music" / f"{name}.{ext}")

def load_sound(name: str, ext: str = "wav") -> Sound:
    with pkg_resources.path(data) as p:
        return _load_sound(p / "sound" / f"{name}.{ext}")

def load_font(name: str, ext: str = "ttf") -> None:
    with pkg_resources.path(data) as p:
        return _load_font(p / "fonts" / f"{name}.{ext}")

def load_shader(name: str, ext: str = "glsl") -> str:
    with pkg_resources.path(data) as p:
        return (p / "shaders" / f"{name}.{ext}").read_text()
