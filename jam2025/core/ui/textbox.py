import math
import sys
import arcade.color
from arcade import Text, Texture, Sound, draw_texture_rect, draw_rect_filled
from arcade.clock import GLOBAL_CLOCK
from arcade.types import RGBOrA255, Color, Rect
import pyglet
from pyglet.media import Player

from jam2025.lib import tobyscript
from jam2025.lib.logging import logger

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
        self._cps = cps
        self.beep = beep
        self.initial_text = initial_text

        self.text = Text(self.initial_text, self.rect.left + self.border, self.rect.top + self.border,
                         self.color, self.text_size, self.rect.width - (self.border * 2),  # type: ignore -- temped to upstream this issue
                         font_name = self.font, anchor_x = "left", anchor_y = "top", multiline = True)
        self.player = Player()

        self._last_queue_time = -sys.maxsize
        self._queued_message: str | None = None

    @property
    def spc(self) -> float:
        return 1 / self._cps if self._cps else 0

    @property
    def current_message(self) -> str:
        return self._queued_message if self._queued_message else ""

    def show(self, message: str) -> None:
        self._last_queue_time = GLOBAL_CLOCK.time
        self._queued_message = message

    def update(self, delta_time: float) -> None:
        chars_since = math.floor(GLOBAL_CLOCK.time_since(self._last_queue_time) * self._cps) if self._cps else sys.maxsize
        if self._queued_message is not None:
            self.text.text = self._queued_message[:chars_since]
        else:
            self.text.text = ""

    def draw(self) -> None:
        if self.background:
            if self._background_type == BackgroundType.TEXTURE:
                draw_texture_rect(self.background, self.rect)  # type: ignore -- static typing fail
            elif self._background_type == BackgroundType.COLOR:
                draw_rect_filled(self.rect, self.background)  # type: ignore -- static typing fail (double kill)
        self.text.draw()

class TobyScriptTextbox(Textbox):
    def __init__(self, rect: Rect, text_size: int, font: str, color: ColorLike = arcade.color.WHITE,
                 border: int | None = None, background: ColorLike | Texture | None = None,
                 cps: float | None = None, beep: Sound | None = None, initial_text: str = ""):
        super().__init__(rect, text_size, font, color, border, background, cps, beep, initial_text)

        # These are essentially unused right now.
        self.speaker = 0
        self.emotion = 0
        self.face = 0

        self.document = pyglet.text.document.FormattedDocument("")
        self.text = pyglet.text.DocumentLabel(document = self.document,
            x = int(self.rect.left) + self.border, y = int(self.rect.top) + self.border,
            width = int(self.rect.width - (self.border / 2)), height = int(self.rect.height - (self.border / 2)),
            anchor_x = "left", anchor_y = "baseline", multiline = True)

        self._current_string = ""
        self._current_wait = 0.0
        self._current_pause = 0.0
        self._queued_events = []
        self.hide = False
        self.paused = False

    def _push_char(self, c: str) -> None:
        self.document.insert_text(len(self.document.text), c, {
            "font_name": self.font,
            "font_size": self.text_size,
            "color": self.color})
        self.document.set_paragraph_style(0, len(self.document.text), {"margin_bottom": 4})
        if self.beep:
            if c not in [" "]:
                self.beep.play()

    def show(self, message: str) -> None:
        self.paused = True
        self.document.text = ""
        self._queued_message = message
        self._queued_events = tobyscript.parse(message)
        self.hide = False
        self._current_string = ""
        self._current_wait = 0.0
        self._current_pause = 0.0
        self.paused = False

    def update(self, delta_time: float) -> None:
        # !: We're using a very small subset of TobyScript here.
        # We can implement more as it's needed.

        if self.paused:
            return

        self._current_wait += delta_time

        if self._current_pause and self._current_pause < self._current_wait:
            self._current_pause = 0
        elif self._current_pause:
            return

        if not self._current_string:
            if self._queued_events:
                event = self._queued_events.pop(0)
                if isinstance(event, tobyscript.TextEvent):
                    if self.hide:
                        self.hide = False
                    self._current_string = event.data
                elif isinstance(event, tobyscript.PauseEvent):
                    self._current_pause = self.spc * event.data * 10
                elif isinstance(event, tobyscript.WaitEvent):
                    self.paused = True
                elif isinstance(event, tobyscript.ColorEvent):
                    self.color = event.rgba
                elif isinstance(event, tobyscript.TextSizeEvent):
                    pass
                elif isinstance(event, tobyscript.SkipEvent):
                    pass
                elif isinstance(event, tobyscript.EmotionEvent):
                    self.emotion = event.data
                elif isinstance(event, tobyscript.FaceEvent):
                    self.face = event.data
                elif isinstance(event, tobyscript.AnimationEvent):
                    pass
                elif isinstance(event, tobyscript.SpeakerEvent):
                    pass
                elif isinstance(event, tobyscript.SoundEvent):
                    pass
                elif isinstance(event, tobyscript.CloseEvent):
                    self.hide = True
                else:
                    logger.warning(f"Unknown event: {event}")
        else:
            if self._current_wait > self.spc:
                self._push_char(self._current_string[0])
                self._current_string = self._current_string[1:]
                self._current_wait = 0

