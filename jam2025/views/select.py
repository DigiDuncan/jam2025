from arcade import View as ArcadeView, Text
from pyglet.graphics import Batch

from jam2025.core.navigation import navigation

class ViewSelectView(ArcadeView):

    def __init__(self) -> None:
        super().__init__()
        self._batch = Batch()
        self._text = [Text(name, self.center_x, self.height - 36 * (idx + 1), font_size=20, anchor_x='center', anchor_y='center', batch=self._batch) for idx, name in enumerate(navigation.available_views)]

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
            navigation.show_view(closest.text)
