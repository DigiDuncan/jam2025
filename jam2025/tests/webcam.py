import arcade

from jam2025.core.ui.button import HoverButton
from jam2025.lib.utils import open_settings, text_to_rect
from jam2025.lib.logging import logger
from jam2025.lib.settings import SETTINGS
from jam2025.core.webcam import WebcamController

class WebcamTestView(arcade.View):
    def __init__(self) -> None:
        self.webcam = WebcamController(0, scaling = 2)

        super().__init__()

        self.spritelist = arcade.SpriteList()
        self.spritelist.append(self.webcam.sprite)
        self.button = HoverButton(self.center_x, self.height / 4, 40, 6)

        self.show_crunchy = False
        self.show_video = True
        self.show_raw_point = False
        self.show_smooth_point = True
        self.show_cloud = False
        self.show_target = False
        self.show_ui = True

        self.fps_text = arcade.Text("000.0 FPS", 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.coordinate_text = arcade.Text("No bright spot found!", 5, self.fps_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.light_text = arcade.Text("000", 5, self.coordinate_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.display_camera = arcade.Camera2D(position=(self.webcam.size[0]/2,self.webcam.size[1]/2), projection=arcade.XYWH(0, 0, *self.webcam.size))
        self.threshold_text = arcade.Text(f"Threshold: {self.webcam.threshold}", self.width - 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.downsample_text = arcade.Text(f"Downsample: {self.webcam.downsample}x", self.width - 5, self.threshold_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.sampled_points_text = arcade.Text(f"Sampled Points: {self.webcam.top_pixels}", self.width - 5, self.downsample_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.frequency_text = arcade.Text(f"Frequency: {self.webcam.frequency:.1f}", self.width - 5, self.sampled_points_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.dampening_text = arcade.Text(f"Dampening: {self.webcam.dampening:.1f}", self.width - 5, self.frequency_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.response_text = arcade.Text(f"Response: {self.webcam.response:.1f}", self.width - 5, self.dampening_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.keybind_text = arcade.Text("[C] Show Cloud [V] Show Video [B] Show Lightness [T] Show Target [<] Show Point [>] Show Smooth Point [F] Flip [U] Close UI", 5, 5, font_size = 11, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "bottom", anchor_x = "left")

    def on_close(self) -> None:
        self.webcam.webcam.disconnect(block=True)
        logger.debug('closing')

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.S:
            open_settings(self.webcam.name)
        elif symbol == arcade.key.V:
            self.show_video = not self.show_video
        elif symbol == arcade.key.C:
            self.show_cloud = not self.show_cloud
        elif symbol == arcade.key.B:
            self.webcam.show_lightness = not self.webcam.show_lightness
        elif symbol == arcade.key.COMMA:
            self.show_raw_point = not self.show_raw_point
        elif symbol == arcade.key.PERIOD:
            self.show_smooth_point = not self.show_smooth_point
        elif symbol == arcade.key.F:
            self.webcam.flip = not self.webcam.flip
        elif symbol == arcade.key.U:
            self.show_ui = not self.show_ui
        elif symbol == arcade.key.R:
            self.webcam.webcam.reconnect(True)
        elif symbol == arcade.key.T:
            self.show_target = not self.show_target

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        point = (x, y)
        threshold_rect = text_to_rect(self.threshold_text)
        downsample_rect = text_to_rect(self.downsample_text)
        sampled_points_rect = text_to_rect(self.sampled_points_text)
        frequency_rect = text_to_rect(self.frequency_text)
        dampening_rect = text_to_rect(self.dampening_text)
        response_rect = text_to_rect(self.response_text)

        if point in threshold_rect:
            SETTINGS.threshold += int(scroll_y)
            SETTINGS.threshold = max(0, self.webcam.threshold)
        elif point in downsample_rect:
            old_ds = self.webcam.downsample
            SETTINGS.downsample += int(scroll_y)
            SETTINGS.downsample = max(1, self.webcam.downsample)
            ratio = (old_ds / self.webcam.downsample)
            SETTINGS.polled_points *= ratio
            SETTINGS.polled_points = int(max(1, SETTINGS.polled_points))
        elif point in sampled_points_rect:
            SETTINGS.polled_points += int(scroll_y)
            SETTINGS.polled_points = max(1, SETTINGS.polled_points)
        elif point in frequency_rect:
            SETTINGS.frequency += scroll_y * 0.1
        elif point in dampening_rect:
            SETTINGS.dampening += scroll_y * 0.1
        elif point in response_rect:
            SETTINGS.response += scroll_y * 0.1

    def on_update(self, delta_time: float) -> None:
        self.webcam.update(delta_time)
        self.button.update(delta_time, self.webcam.cursor)
        self.update_ui(delta_time)

    def update_ui(self, delta_time: float) -> None:
        self.fps_text.text = f"{1/delta_time:.1f} FPS"
        if self.webcam.raw_cursor:
            self.coordinate_text.text = f"({self.webcam.raw_cursor[0]}, {self.webcam.raw_cursor[1]})"
            self.light_text.text = f"{self.webcam._highest_l:.3f}"
        else:
            self.coordinate_text.text = "No bright point found!"
        self.threshold_text.text = f"Threshold: {self.webcam.threshold}"
        self.downsample_text.text = f"Downsample: {self.webcam.downsample}x"
        self.sampled_points_text.text = f"Sampled Points: {self.webcam.top_pixels}"
        self.frequency_text.text = f"Frequency: {self.webcam.frequency:.1f}"
        self.dampening_text.text = f"Dampening: {self.webcam.dampening:.1f}"
        self.response_text.text = f"Response: {self.webcam.response:.1f}"

    def on_draw(self) -> None:
        self.clear(arcade.color.BLACK)
        if self.show_video:
            self.spritelist.draw()
        if self.webcam.raw_cursor:
            if self.show_raw_point:
                rect = arcade.XYWH(self.webcam.raw_cursor[0], self.webcam.raw_cursor[1], 10, 10)
                arcade.draw_rect_filled(rect, arcade.color.RED)
            if self.show_cloud:
                cloud = [(x[0][0] * self.webcam.downsample * self.webcam.scaling, x[0][1] * self.webcam.downsample * self.webcam.scaling) for x in self.webcam.cloud]
                arcade.draw_points(cloud, arcade.color.BLUE, 3)
        if self.webcam.cursor and self.show_smooth_point:
            arect = arcade.XYWH(self.webcam.cursor[0], self.webcam.cursor[1], 10, 10)
            arcade.draw_rect_filled(arect, arcade.color.GREEN)
        if self.show_target:
            self.button.draw()
        if self.show_ui:
            if self.webcam.raw_cursor:
                self.light_text.draw()
            self.coordinate_text.draw()
            self.threshold_text.draw()
            self.downsample_text.draw()
            self.sampled_points_text.draw()
            self.frequency_text.draw()
            self.dampening_text.draw()
            self.response_text.draw()
            self.keybind_text.draw()
        self.fps_text.draw()
