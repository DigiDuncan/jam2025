import math
import arcade
import cv2
from PIL import Image
import numpy as np
import os
import threading
from arcade import Vec2

from .webcam import WebCam
from .procedural_animator import SecondOrderAnimatorKClamped

def rgb_to_l(r: int, g: int, b: int) -> int:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_polar_angle(x: float, y: float, center: tuple[float, float] = (0, 0)) -> float:
    return math.atan2(y - center[1], x - center[0])

def text_to_rect(text: arcade.Text) -> arcade.types.Rect:
    """This will be unnecessary once my PR is merged.
    https://github.com/pythonarcade/arcade/pull/2759
    """
    return arcade.types.LRBT(text.left, text.right, text.bottom, text.top)

def open_settings(name: str = "USB Video Device") -> None:
    """WOW THIS SUCKS"""
    os.system(f"ffmpeg -hide_banner -loglevel error -f dshow -show_video_device_dialog true -i video=\"{name}\"")

class TestWindow(arcade.Window):
    DEFAULT_WIDTH = 1280
    DEFAULT_HEIGHT = 720

    def __init__(self) -> None:
        self.webcam = WebCam()
        self.webcam.connect()
        super().__init__(*self.webcam.size, "Pass The Torch!") # TestWindow.DEFAULT_WIDTH, TestWindow.DEFAULT_HEIGHT
        self.cam_name = "Logitech Webcam C930e"  # !: This is the name of my camera, replace it with yours! (Yes this sucks.)

        self.spritelist = arcade.SpriteList()
        self.webcam_sprite = arcade.SpriteSolidColor(self.webcam.size[0], self.webcam.size[1], center_x = self.webcam.size[0]/2, center_y =  self.webcam.size[1]/2)
        self.crunchy_webcam_sprite = arcade.SpriteSolidColor(self.webcam.size[0], self.webcam.size[1], center_x = self.webcam.size[0]/2, center_y =  self.webcam.size[1]/2)
        self.spritelist.append(self.webcam_sprite)
        self.spritelist.append(self.crunchy_webcam_sprite)

        self.fps_text = arcade.Text("000.0 FPS", 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.coordinate_text = arcade.Text("No bright spot found!", 5, self.fps_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.light_text = arcade.Text("000", 5, self.coordinate_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")

        self.display_camera = arcade.Camera2D(position=(self.webcam.size[0]/2,self.webcam.size[1]/2), projection=arcade.XYWH(0, 0, *self.webcam.size))
        self.display_camera.match_window(projection=False, aspect = self.webcam.size[0]/self.webcam.size[1])

        self.show_crunchy = False
        self.show_video = True
        self.show_raw_point = True
        self.show_smooth_point = True
        self.show_cloud = False
        self.show_shape = False
        self.show_lightness = False
        self.show_target = False
        self.show_ui = True
        self.do_flip = True

        self.fetched_frame: np.ndarray = self.webcam.get_frame()
        if self.fetched_frame is None:
            return ValueError('No initial frame found')
        self.pixel_found = False
        self.brightest_px: tuple[int, int] | None = None
        self.animated_px: tuple[int, int] | None = None
        self.highest_l: int | None = None
        self.cloud = []
        self.no_pixel_time = 0.0

        self.threshold = 245
        self.downsample = 8
        self.top_pixels = 10
        self.camera_alpha = 255
        self.timeout = 1.0
        self.frequency = 2.0
        self.dampening = 1.8
        self.response = -0.5

        self.threshold_text = arcade.Text(f"Threshold: {self.threshold}", self.width - 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.downsample_text = arcade.Text(f"Downsample: {self.downsample}x", self.width - 5, self.threshold_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.sampled_points_text = arcade.Text(f"Sampled Points: {self.top_pixels}", self.width - 5, self.downsample_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.alpha_text = arcade.Text(f"Camera Alpha: {self.camera_alpha}", self.width - 5, self.sampled_points_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.frequency_text = arcade.Text(f"Frequency: {self.frequency:.1f}", self.width - 5, self.alpha_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.dampening_text = arcade.Text(f"Dampening: {self.dampening:.1f}", self.width - 5, self.frequency_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")
        self.response_text = arcade.Text(f"Response: {self.response:.1f}", self.width - 5, self.dampening_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "right", align = "right")

        self.keybind_text = arcade.Text("[Z] Show Shape [X] Show Cloud [C] Show Crunchy [V] Show Video [B] Show Lightness [<] Show Point [>] Show Smooth Point [F] Flip [U] Close UI", 5, 5, font_size = 11, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "bottom", anchor_x = "left")

        self.animator = SecondOrderAnimatorKClamped(self.frequency, self.dampening, self.response, Vec2(0, 0), Vec2(0, 0), 0)

        self.target = self.rect.scale(0.25)

    def refresh_animator(self):
        self.animator = SecondOrderAnimatorKClamped(self.frequency, self.dampening, self.response, Vec2(*self.brightest_px) if self.brightest_px else Vec2(0, 0), Vec2(*self.brightest_px) if self.brightest_px else Vec2(0, 0), 0)

    def get_frame_data(self) -> np.ndarray | None:
        frame = self.webcam.get_frame()
        if frame is None:
            frame = self.fetched_frame
        else:
            self.fetched_frame = frame
        frame = frame[:, :, ::-1]  # The camera data is BGR for some reason
        if self.do_flip:
            frame = np.fliplr(frame)
        return frame

    def frame_data_to_image(self, data: np.ndarray) -> Image.Image:
        return Image.fromarray(data, mode = "RGB")

    def read_frame(self, downsample: int = 1) -> Image.Image | None:
        frame = self.get_frame_data()
        if frame is not None and downsample != 1:
            frame = frame[::downsample, ::downsample]
        if frame is not None:
            i = self.frame_data_to_image(frame)
            return i

    def get_brightest_pixel(self, threshold: int = 230, downsample: int = 8) -> tuple[int, int] | None:
        """You'd think this is the most expensive function, but it's not!"""
        frame = self.get_frame_data()
        if frame is not None and downsample != 1:
            frame = frame[::downsample, ::downsample]
        if frame is None:
            self.pixel_found = False
            return None
        
        # Use numpy to quickly get shaped array of brightness
        brightness = rgb_to_l(frame[:, :, 0], frame[:, :, 1], frame[:, :, 2])
        # Get a numpy conditional mask (shaped array of 0s and 1s)
        thresholded_values = brightness >= threshold
        # Get array of x and y indices
        bi = thresholded_values.nonzero()
        # Create bright pixel list (Could use numpy to make this cleaner but that doesn't really matter)
        brightest_pixels = [((x, frame.shape[0] - y), brightness[y, x]) for y, x in zip(bi[0], bi[1])]
        brightest_pixels.sort(reverse=True, key = lambda x: x[1])
        self.cloud = brightest_pixels[:self.top_pixels]
        average_pos = np.mean(np.array([x[0] for x in self.cloud]), axis=0)

        try:
            if brightest_pixels:
                self.highest_l = brightest_pixels[0][1]
            self.pixel_found = True
            return (int(average_pos[0] * downsample), int(average_pos[1] * downsample))  # I don't know why but you have to double the
        except Exception as _:                                                                   # coordinates from what you'd expect.
            self.pixel_found = False
            return None
    
    def on_resize(self, width, height):
        self.display_camera.match_window(projection=False, aspect = self.webcam.size[0]/self.webcam.size[1])

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.C:
            self.show_crunchy = not self.show_crunchy
        elif symbol == arcade.key.V:
            self.show_video = not self.show_video
        elif symbol == arcade.key.B:
            self.show_lightness = not self.show_lightness
        elif symbol == arcade.key.COMMA:
            self.show_raw_point = not self.show_raw_point
        elif symbol == arcade.key.PERIOD:
            self.show_smooth_point = not self.show_smooth_point
        elif symbol == arcade.key.X:
            self.show_cloud = not self.show_cloud
        elif symbol == arcade.key.Z:
            self.show_shape = not self.show_shape
        elif symbol == arcade.key.S:
            thread = threading.Thread(target = open_settings, args = (self.cam_name,))
            thread.start()
        elif symbol == arcade.key.U:
            self.show_ui = not self.show_ui
        elif symbol == arcade.key.F:
            self.do_flip = not self.do_flip
        elif symbol == arcade.key.T:
            self.show_target = not self.show_target

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        point = (x, y)
        threshold_rect = text_to_rect(self.threshold_text)
        downsample_rect = text_to_rect(self.downsample_text)
        sampled_points_rect = text_to_rect(self.sampled_points_text)
        alpha_rect = text_to_rect(self.alpha_text)
        frequency_rect = text_to_rect(self.frequency_text)
        dampening_rect = text_to_rect(self.dampening_text)
        response_rect = text_to_rect(self.response_text)

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
        elif point in frequency_rect:
            self.frequency += scroll_y * 0.1
            self.refresh_animator()
        elif point in dampening_rect:
            self.dampening += scroll_y * 0.1
            self.refresh_animator()
        elif point in response_rect:
            self.response += scroll_y * 0.1
            self.refresh_animator()

    def on_update(self, delta_time: float) -> None:
        frame_data = self.get_frame_data()
        frame = self.frame_data_to_image(frame_data) if frame_data is not None else None
        crunchy_frame = self.frame_data_to_image(frame_data[::self.downsample, ::self.downsample]) if frame_data is not None else None

        if frame is not None and crunchy_frame is not None:
            frame = frame.convert("RGBA")
            if self.show_lightness:
                frame = frame.convert("L").convert("RGBA")
            tex = arcade.Texture(frame)
            self.webcam_sprite.texture = tex
            self.webcam_sprite.size = self.size
            self.webcam_sprite.alpha = self.camera_alpha if self.show_video else 0

            crunchy_frame = crunchy_frame.convert("RGBA")
            if self.show_lightness:
                crunchy_frame = crunchy_frame.convert("L").convert("RGBA")
            crunchy_tex = arcade.Texture(crunchy_frame)
            self.crunchy_webcam_sprite.texture = crunchy_tex
            self.crunchy_webcam_sprite.size = self.size
            self.crunchy_webcam_sprite.alpha = 255 if self.show_crunchy else 0
        self.brightest_px = self.get_brightest_pixel(self.threshold, self.downsample)
        if self.animated_px is None and self.brightest_px:
            self.refresh_animator()
        if self.brightest_px:
            self.no_pixel_time = 0.0
            self.animated_px = self.animator.update(delta_time, Vec2(*self.brightest_px))
        else:
            self.no_pixel_time += delta_time
            if self.no_pixel_time >= self.timeout:
                self.animated_px = None
        self.update_ui(delta_time)

    def update_ui(self, delta_time: float) -> None:
        self.fps_text.text = f"{1/delta_time:.1f} FPS"
        if self.brightest_px:
            self.coordinate_text.text = f"({self.brightest_px[0]}, {self.brightest_px[1]})"
            self.light_text.text = str(self.highest_l)
        else:
            self.coordinate_text.text = "No bright point found!"
        self.threshold_text.text = f"Threshold: {self.threshold}"
        self.downsample_text.text = f"Downsample: {self.downsample}x"
        self.sampled_points_text.text = f"Sampled Points: {self.top_pixels}"
        self.alpha_text.text = f"Alpha: {self.camera_alpha}"
        self.frequency_text.text = f"Frequency: {self.frequency:.1f}"
        self.dampening_text.text = f"Dampening: {self.dampening:.1f}"
        self.response_text.text = f"Response: {self.response:.1f}"

    def on_draw(self) -> None:
        self.clear(arcade.color.BLACK)
        # with self.display_camera.activate():
        self.spritelist.draw()
        if self.brightest_px:
            if self.show_raw_point:
                rect = arcade.XYWH(self.brightest_px[0], self.brightest_px[1], 10, 10)
                arcade.draw_rect_filled(rect, arcade.color.RED)
            if self.show_cloud or self.show_shape:
                cloud = sorted([(x[0][0] * self.downsample, x[0][1] * self.downsample) for x in self.cloud], key = lambda x: get_polar_angle(x[0], x[1], self.brightest_px))
                if self.show_shape:
                    arcade.draw_polygon_filled(cloud, arcade.color.BLUE.replace(a = 128))
                if self.show_cloud:
                    arcade.draw_points(cloud, arcade.color.BLUE, 3)
        if self.animated_px and self.show_smooth_point:
            arect = arcade.XYWH(self.animated_px[0], self.animated_px[1], 10, 10)
            arcade.draw_rect_filled(arect, arcade.color.GREEN)
        if self.show_target:
            if self.animated_px in self.target:
                arcade.draw_rect_filled(self.target, arcade.color.GREEN.replace(a = 128))
            else:
                arcade.draw_rect_filled(self.target, arcade.color.RED.replace(a = 128))
        if self.show_ui:
            if self.brightest_px:
                self.light_text.draw()
            self.coordinate_text.draw()
            self.threshold_text.draw()
            self.downsample_text.draw()
            self.sampled_points_text.draw()
            self.alpha_text.draw()
            self.frequency_text.draw()
            self.dampening_text.draw()
            self.response_text.draw()
            self.keybind_text.draw()
        self.fps_text.draw()

def main() -> None:
    win = TestWindow()
    win.run()

if __name__ == '__main__':
    main()
