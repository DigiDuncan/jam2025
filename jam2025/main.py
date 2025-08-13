import arcade
import cv2
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter
import os
import threading

def rgb_to_l(r: int, g: int, b: int) -> int:
    return int(0.2126 * r + 0.7152 * g + 0.0722 * b)

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
        self.blur = False
        self.blur_kernel = (3, 3, 0)

        self.pixel_found = False
        self.brightest_px: tuple[int, int] | None = None
        self.highest_l: int | None = None

        self.threshold = 230
        self.downsample = 8
        self.top_pixels = 25

        self.info_text = arcade.Text(f"Threshold: {self.threshold}\nDownsample: {self.downsample}x\nAvg. Of: {self.top_pixels}px\nBlur: {self.blur}", self.width - 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right", width = self.width / 2, multiline = True)
        self.cloud = []

    def get_frame_data(self, downsample: int = 1, blur = False) -> np.ndarray | None:
        retval, frame = self.cam.read()
        if not retval:
            print("Can't read frame!")
        else:
            frame = frame[:, :, ::-1]  # The camera data is BGR for some reason
            frame = frame[::downsample, ::downsample]
            if blur:
                frame = gaussian_filter(frame, self.blur_kernel)
            return frame

    def read_frame(self, downsample: int = 1, blur: bool = False) -> Image.Image | None:
        frame = self.get_frame_data(downsample, blur)
        if frame is not None:
            i = Image.fromarray(frame, mode = "RGB")
            return i

    def get_brightest_pixel(self, threshold: int = 230, downsample: int = 8) -> tuple[int, int] | None:
        frame = self.get_frame_data(downsample, self.blur)
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
        elif symbol == arcade.key.S:
            thread = threading.Thread(target = open_settings, args = (self.cam_name, ))
            thread.start()
        elif symbol == arcade.key.B:
            self.blur = not self.blur

    def on_update(self, delta_time: float) -> bool | None:
        frame = self.read_frame()
        crunchy_frame = self.read_frame(self.downsample)
        if self.blur:
            ...
        if frame is not None and crunchy_frame is not None:
            frame = frame.convert("RGBA")
            tex = arcade.Texture(frame)
            self.webcam_sprite.texture = tex
            self.webcam_sprite.size = self.size
            # self.webcam_sprite.alpha = 128

            crunchy_frame = crunchy_frame.convert("RGBA")
            crunchy_tex = arcade.Texture(crunchy_frame)
            self.crunchy_webcam_sprite.texture = crunchy_tex
            self.crunchy_webcam_sprite.size = self.size
            self.crunchy_webcam_sprite.alpha = 255 if self.show_crunchy else 0
        self.brightest_px = self.get_brightest_pixel(self.threshold, self.downsample)
        if self.brightest_px:
            self.coordinate_text.text = f"({self.brightest_px[0]}, {self.brightest_px[1]})"
            self.light_text.text = str(self.highest_l)
        else:
            self.coordinate_text.text = "No bright point found!"
        self.info_text.text = f"Threshold: {self.threshold}\nDownsample: {self.downsample}x\nAvg. Of: {self.top_pixels}px\nBlur: {self.blur}"

    def on_draw(self) -> None:
        self.clear(arcade.color.BLACK)
        self.spritelist.draw()
        if self.brightest_px:
            rect = arcade.XYWH(self.brightest_px[0], self.brightest_px[1], 10, 10)
            arcade.draw_rect_filled(rect, arcade.color.RED)
            if self.show_cloud:
                arcade.draw_points([(x[0][0] * self.downsample * 2, x[0][1] * self.downsample * 2) for x in self.cloud], arcade.color.BLUE, 3)
            self.light_text.draw()
        self.coordinate_text.draw()
        self.info_text.draw()

def main() -> None:
    win = TestWindow()
    win.run()

if __name__ == '__main__':
    main()
