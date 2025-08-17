import math
import sys
import arcade.color
from arcade import Text, Texture, Sound, draw_texture_rect, draw_rect_filled
from arcade.clock import GLOBAL_CLOCK
from arcade.types import RGBOrA255, Color, Rect
from pyglet.media import Player

type ColorLike = RGBOrA255 | Color

class BackgroundType:
    TEXTURE = "texture"
    COLOR = "color"
    NONE = "none"

class Textbox:
    def __init__(self, rect: Rect, text_size: int, font: str, color: ColorLike = arcade.color.WHITE, border: int | None = None,
                 background: ColorLike | Texture | None = None, cps: float | None = None, beep: Sound | None = None, initial_text: str = ""):
        self.rect = rect
        self.text_size = text_size
        self.font = font
        self.color = color
        self.border = border if border else 0
        self.background = background
        self._background_type = None
        if isinstance(self.background, Texture):
            self._background_type = BackgroundType.TEXTURE
        elif self.background is None:
            self._background_type = BackgroundType.NONE
        else:
            self._background_type = BackgroundType.COLOR
        self.cps = cps
        self.beep = beep
        self.initial_text = initial_text

        self.text = Text(self.initial_text, self.rect.left + self.border, self.rect.top + self.border,
                         self.color, self.text_size, self.rect.width - (self.border * 2),
                         font_name = self.font, anchor_x = "left", anchor_y = "top", multiline = True)
        self.player = Player()

        self._last_queue_time = -sys.maxsize
        self._queued_message: str | None = None

    def queue(self, message: str) -> None:
        self._last_queue_time = GLOBAL_CLOCK.time
        self._queued_message = message

    def update(self, delta_time: float) -> None:
        chars_since = math.floor(GLOBAL_CLOCK.time_since(self._last_queue_time) * self.cps) if self.cps else sys.maxsize
        if self._queued_message is not None:
            self.text.text = self._queued_message[:chars_since]
        else:
            self.text.text = ""

    def draw(self) -> None:
        if self.background:
            if self._background_type == BackgroundType.TEXTURE:
                draw_texture_rect(self.background, self.rect)
            elif self._background_type == BackgroundType.COLOR:
                draw_rect_filled(self.rect, self.background)
        self.text.draw()
