# This is done the "bad" way.

import importlib.resources as pkg_resources
from arcade import Texture, load_texture as _load_texture
from jam2025 import data

def load_texture(name: str, ext: str = "png") -> Texture:
    with pkg_resources.path(data) as p:
        return _load_texture(p / f"{name}.{ext}")
