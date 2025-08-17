import arcade

from jam2025.lib.textbox import Textbox


class TextboxTestWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__()
        self.text_box = Textbox(arcade.XYWH(self.center_x, self.center_y, self.width * 0.75, self.height * 0.33), 48, "8bitoperator JVE",
                                border = 5, cps = 30, background = arcade.color.DARK_SLATE_GRAY)

        self.messages = ["This is a textbox.", "We can use it to make text happen, and this is a much longer message.", "We're going to see if this works!"]


    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.Q and self.messages:
            msg = self.messages.pop(0)
            self.text_box.queue(msg)

    def on_update(self, delta_time: float) -> None:
        self.text_box.update(delta_time)

    def on_draw(self) -> None:
        self.clear()
        self.text_box.draw()

def main() -> None:
    win = TextboxTestWindow()
    win.run()

if __name__ == '__main__':
    main()
