import arcade

from jam2025.core.button import Button
from jam2025.core.textbox import Textbox


class TextboxTestWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__()
        self.text_box = Textbox(arcade.XYWH(self.center_x, self.center_y, self.width * 0.75, self.height * 0.33), 48, "8bitoperator JVE",
                                border = 5, cps = 30, background = arcade.color.DARK_SLATE_GRAY, color = arcade.color.WHITE)

        self.messages = ["This is a textbox.", "We can use it to make text happen, and this is a much longer message.", "We're going to see if this works!", None]

        self.button = Button(self.center_x, self.height / 4, 40, 6)
        self.button.callback = self.queue_message

        self.cursor = None

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.cursor = (x, y)

    def queue_message(self):
        if self.messages:
            msg = self.messages.pop(0)
            self.text_box.queue(msg)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.Q and self.messages:
            self.queue_message()
        if symbol == arcade.key.R:
            self.messages = ["This is a textbox.", "We can use it to make text happen, and this is a much longer message.", "We're going to see if this works!", None]

    def on_update(self, delta_time: float) -> None:
        self.text_box.update(delta_time)
        if self.cursor:
            self.button.update(delta_time, self.cursor)
        self.button.disabled = not self.messages

    def on_draw(self) -> None:
        self.clear()
        self.text_box.draw()
        self.button.draw()

def main() -> None:
    win = TextboxTestWindow()
    win.run()

if __name__ == '__main__':
    main()
