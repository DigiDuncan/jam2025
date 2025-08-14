import math
import arcade
import cv2
from PIL import Image
import numpy as np
import os
import threading
from arcade import Vec2

from jam2025.procedural_animator import SecondOrderAnimatorKClamped

def rgb_to_l(r: int, g: int, b: int) -> int:
    return int(0.2126 * r + 0.7152 * g + 0.0722 * b)

def get_polar_angle(x: float, y: float, center: tuple[float, float] = (0, 0)) -> float:
    return math.atan2(y - center[1], x - center[0])

def text_to_rect(text: arcade.Text) -> arcade.types.Rect:
    """This will be unnecessary once my PR is merged.
    https://github.com/pythonarcade/arcade/pull/2759
    """
    return arcade.types.LRBT(text.left, text.right, text.bottom, text.top)

def open_settings(name: str = "USB Video Device") -> None:
    os.system(f"ffmpeg -hide_banner -loglevel error -f dshow -show_video_device_dialog true -i video=\"{name}\"")

class TestWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__()
        self.cam = cv2.VideoCapture(0)
        self.cam_name = "USB Video Device"

        self.spritelist = arcade.SpriteList()
        self.webcam_sprite = arcade.SpriteSolidColor(self.width, self.height, center_x = self.center_x, center_y = self.center_y)
        self.crunchy_webcam_sprite = arcade.SpriteSolidColor(self.width, self.height, center_x = self.center_x, center_y = self.center_y)
        self.spritelist.append(self.webcam_sprite)
        self.spritelist.append(self.crunchy_webcam_sprite)

        self.coordinate_text = arcade.Text("No bright spot found!", 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.light_text = arcade.Text("000", 5, self.coordinate_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")

        self.show_crunchy = False
        self.show_cloud = False
        self.show_shape = False

        self.pixel_found = False
        self.brightest_px: tuple[int, int] | None = None
        self.animated_px: tuple[int, int] | None = None
        self.highest_l: int | None = None
        self.cloud = []

        self.threshold = 245
        self.downsample = 8
        self.top_pixels = 10
        self.camera_alpha = 255

        self.threshold_text = arcade.Text(f"Threshold: {self.threshold}", self.width - 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.downsample_text = arcade.Text(f"Downsample: {self.downsample}x", self.width - 5, self.threshold_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.sampled_points_text = arcade.Text(f"Sampled Points: {self.top_pixels}", self.width - 5, self.downsample_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.alpha_text = arcade.Text(f"Camera Alpha: {self.camera_alpha}", self.width - 5, self.sampled_points_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")

        self.animator = SecondOrderAnimatorKClamped(1, 1, 0, Vec2(0, 0), Vec2(0, 0), 0)

    def get_frame_data(self, downsample: int = 1,) -> np.ndarray | None:
        retval, frame = self.cam.read()
        if not retval:
            print("Can't read frame!")
        else:
            frame = frame[:, :, ::-1]  # The camera data is BGR for some reason
            frame = frame[::downsample, ::downsample]
            return frame

    def read_frame(self, downsample: int = 1) -> Image.Image | None:
        frame = self.get_frame_data(downsample)
        if frame is not None:
            i = Image.fromarray(frame, mode = "RGB")
            return i

    def get_brightest_pixel(self, threshold: int = 230, downsample: int = 8) -> tuple[int, int] | None:
        frame = self.get_frame_data(downsample)
        if frame is None:
            self.pixel_found = False
            return None
        brightest_pixels = []
        if frame is not None:
            for y_coord, y in enumerate(frame):
                for x_coord, rgb in enumerate(y):
                    l = rgb_to_l(*rgb)
                    if l >= threshold:
                        brightest_pixels.append(((x_coord, frame.shape[0] - y_coord), l))
        brightest_pixels.sort(key = lambda x: x[1], reverse = True)
        self.cloud = brightest_pixels[:self.top_pixels]
        average_pos = np.mean(np.array([x[0] for x in self.cloud]), axis=0)
        try:
            if brightest_pixels:
                self.highest_l = brightest_pixels[0][1]
            self.pixel_found = True
            return (int(average_pos[0] * downsample * 2), int(average_pos[1] * downsample * 2))  # I don't know why but you have to double the
        except Exception as _:                                                                   # coordinates from what you'd expect.
            self.pixel_found = False
            return None

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.C:
            self.show_crunchy = not self.show_crunchy
        elif symbol == arcade.key.X:
            self.show_cloud = not self.show_cloud
        elif symbol == arcade.key.Z:
            self.show_shape = not self.show_shape
        elif symbol == arcade.key.S:
            thread = threading.Thread(target = open_settings, args = (self.cam_name,))
            thread.start()

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        point = (x, y)
        threshold_rect = text_to_rect(self.threshold_text)
        downsample_rect = text_to_rect(self.downsample_text)
        sampled_points_rect = text_to_rect(self.sampled_points_text)
        alpha_rect = text_to_rect(self.alpha_text)

        if point in threshold_rect:
            self.threshold += int(scroll_y)
            self.threshold = max(0, self.threshold)
        elif point in downsample_rect:
            self.downsample += int(scroll_y)
            self.downsample = max(1, self.downsample)
        elif point in sampled_points_rect:
            self.top_pixels += int(scroll_y)
            self.top_pixels = max(1, self.top_pixels)
        elif point in alpha_rect:
            self.camera_alpha += int(scroll_y) * 16
            self.camera_alpha = min(255, max(0, self.camera_alpha))

    def on_update(self, delta_time: float) -> bool | None:
        frame = self.read_frame()
        crunchy_frame = self.read_frame(self.downsample)
        if frame is not None and crunchy_frame is not None:
            frame = frame.convert("RGBA")
            tex = arcade.Texture(frame)
            self.webcam_sprite.texture = tex
            self.webcam_sprite.size = self.size
            self.webcam_sprite.alpha = self.camera_alpha

            crunchy_frame = crunchy_frame.convert("RGBA")
            crunchy_tex = arcade.Texture(crunchy_frame)
            self.crunchy_webcam_sprite.texture = crunchy_tex
            self.crunchy_webcam_sprite.size = self.size
            self.crunchy_webcam_sprite.alpha = 255 if self.show_crunchy else 0
        self.brightest_px = self.get_brightest_pixel(self.threshold, self.downsample)
        if self.brightest_px:
            self.animated_px = self.animator.update(delta_time, Vec2(*self.brightest_px))
        self.update_ui()

    def update_ui(self):
        if self.brightest_px:
            self.coordinate_text.text = f"({self.brightest_px[0]}, {self.brightest_px[1]})"
            self.light_text.text = str(self.highest_l)
        else:
            self.coordinate_text.text = "No bright point found!"
        self.threshold_text.text = f"Threshold: {self.threshold}"
        self.downsample_text.text = f"Downsample: {self.downsample}x"
        self.sampled_points_text.text = f"Sampled Points: {self.top_pixels}"
        self.alpha_text.text = f"Alpha: {self.camera_alpha}"

    def on_draw(self) -> None:
        self.clear(arcade.color.BLACK)
        self.spritelist.draw()
        if self.brightest_px:
            rect = arcade.XYWH(self.brightest_px[0], self.brightest_px[1], 10, 10)
            arcade.draw_rect_filled(rect, arcade.color.RED)

            arect = arcade.XYWH(self.animated_px[0], self.animated_px[1], 10, 10)
            arcade.draw_rect_filled(arect, arcade.color.GREEN)

            if self.show_cloud or self.show_shape:
                cloud = sorted([(x[0][0] * self.downsample * 2, x[0][1] * self.downsample * 2) for x in self.cloud], key = lambda x: get_polar_angle(x[0], x[1], self.brightest_px))
                if self.show_shape:
                    arcade.draw_polygon_filled(cloud, arcade.color.BLUE.replace(a = 128))
                if self.show_cloud:
                    arcade.draw_points(cloud, arcade.color.BLUE, 3)
            self.light_text.draw()
        self.coordinate_text.draw()
        self.threshold_text.draw()
        self.downsample_text.draw()
        self.sampled_points_text.draw()
        self.alpha_text.draw()

def main() -> None:
    win = TestWindow()
    win.run()

if __name__ == '__main__':
    main()
