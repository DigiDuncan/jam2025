from arcade import SpriteList, View
from jam2025.core.game.bullet import bullet_sprite
from jam2025.core.void import Void
from jam2025.data.loading import load_music


class AnimationTestView(View):
    def __init__(self) -> None:
        super().__init__()
        self.void = Void(self.window.rect)
        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.0, loop = True)

        self.spritelist = SpriteList()

        self.sprite = bullet_sprite
        self.sprite.position = self.window.center

        self.spritelist.append(self.sprite)

    def on_update(self, delta_time: float) -> None:
        self.spritelist.update_animation(delta_time)

    def on_draw(self) -> bool | None:
        self.clear()
        self.void.draw()
        self.spritelist.draw()
