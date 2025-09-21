from arcade import View as ArcadeView, Text
from pyglet.graphics import Batch

from jam2025.core.navigation import navigation

class ViewSelectView(ArcadeView):

    def __init__(self) -> None:
        super().__init__()
        self._batch = Batch()
        self._text = [Text(name.replace("_", " ").upper(), self.center_x, self.height - 80 * (idx + 1), font_size=44, anchor_x='center', anchor_y='center', batch=self._batch, font_name = "GohuFont 11 Nerd Font Mono") for idx, name in enumerate(navigation.available_views) if name != "v_select"]

    def setup(self) -> None:
        ...

    def on_draw(self) -> bool | None:
        self.clear()
        self._batch.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        closest = None
        dist = float('inf')
        for text in self._text:
            seperation = abs(y - text.y)
            if seperation < dist:
                closest = text
                dist = seperation

        if closest is not None:
            navigation.show_view(closest.text.lower().replace(" ", "_"), show_splash = closest.text.lower().replace(" ", "_") == "play")
