from arcade import Sprite, Rect, SpriteList
from arcade.clock import GLOBAL_CLOCK
from jam2025.data.loading import load_texture
from jam2025.lib.anim import ease_linear, perc, EasingFunction

class Popup:
    def __init__(self, rect: Rect, icon_name: str = "missing", fade_in: float = 0.5, hold: float = 1.0, fade_out: float = 0.5,
                 easing_function: EasingFunction = ease_linear):
        self.rect = rect
        tex = load_texture(icon_name)
        self.sprite = Sprite(tex, center_x = rect.center_x, center_y = rect.center_y)
        self.sprite.width = rect.width
        self.sprite.height = rect.height

        self.sprite_list = SpriteList()
        self.sprite_list.append(self.sprite)

        self.fade_in = fade_in
        self.hold = hold
        self.fade_out = fade_out
        self.easing_function = easing_function

        self.last_popup_time = float("-inf")

    def popup(self, new_icon: str | None = None) -> None:
        if new_icon:
            self.sprite.texture = load_texture(new_icon)
        self.last_popup_time = GLOBAL_CLOCK.time

    def draw(self) -> None:
        time = GLOBAL_CLOCK.time
        fade_in_start = self.last_popup_time
        fade_in_finish = fade_in_start + self.fade_in
        hold_finish = fade_in_finish + self.hold
        fade_out_finish = hold_finish + self.fade_out

        alpha = 0
        # fading in
        if fade_in_start < time < fade_in_finish:
            alpha = self.easing_function(0, 255, perc(fade_in_start, fade_in_finish, time))
        elif fade_in_finish < time < hold_finish:
            alpha = 255
        elif hold_finish < time < fade_out_finish:
            alpha = self.easing_function(255, 0, perc(hold_finish, fade_out_finish, time))
        elif fade_out_finish < time:
            alpha = 0

        self.sprite.alpha = int(alpha)
        self.sprite_list.draw(pixelated = True)  # Hardcoding the pixelation here.
