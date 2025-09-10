from arcade import View as ArcadeView, Sprite, SpriteList, Rect, LRBT

from jam2025.core.settings import settings
from jam2025.core.webcam import SimpleAnimatedWebcamDisplay

from jam2025.lib.webcam import Webcam


class SelectWebcamView(ArcadeView):
    """
    The goal of this view is to let the player select which webcam to use.

    It defaults to loading the webcam found in the .cfg file. Which defaults to zero.
    It then keeps trying to connect to webcams until one fails to connect. 

    every connected webcam is displayed in an enumeration the player can select from.
    The default (the one found in the .cfg) is highlighted as the default. If the
    player selects a different view it will update the settings, and then write it
    to disk saving it for next time.
    """
    WEBCAM_FAIL_CAP = 5
    PADDING = 30.0
    MAX_COLUMNS = 3
    

    def __init__(self) -> None:
        super().__init__()

        self.query_index: int
        self.failed_queries: int

        self.webcams: list[Webcam]
        self.displays: list[SimpleAnimatedWebcamDisplay | None]
        self.spritelist: SpriteList[Sprite]

        self.display_area: Rect

    def on_show_view(self) -> None:
        self.spritelist = SpriteList()

        initial_id = settings.webcam_id
        webcam = Webcam(initial_id)
        webcam.connect(True)

        self.webcams = [webcam]
        self.displays = [None]
        self.query_index = 0
        self.failed_queries = 0

        padding = SelectWebcamView.PADDING
        self.display_area = LRBT(
            padding,
            self.width - padding,
            padding,
            self.height - padding
        )

    def on_hide_view(self) -> None:
        # This is a safety check by this point all the webcams should be cleared
        self.spritelist.clear()
        for webcam in self.webcams:
            webcam.disconnect()
        self.webcams = []

    def select_webcam(self, id: int):
        # TODO: select webcam
        pass

    def on_draw(self) -> bool | None:
        self.clear()
        self.spritelist.draw()

    def on_update(self, delta_time: float) -> bool | None:
        # TODO: handle failing to connect to even one webcam
        # TODO: connect new webcams and move em to the right spot
        self._validate_webcams()

        for display in self.displays:
            if display is not None:
                display.update(delta_time)

    def _validate_webcams(self):
        for idx, webcam in enumerate(self.webcams):
            if webcam.failed:
                webcam.disconnect()
                self.failed_queries += 1
                if idx == self.query_index:
                    self.query_index += 1
                continue

            if not webcam.connected:
                continue

            # the query index is a connected webcam so move on
            if idx == self.query_index:
                self.query_index += 1
            
            # check to see if the display for the connected webcam exists.
            display = self.displays[idx]
            if display is None:
                display = SimpleAnimatedWebcamDisplay(webcam)
                self.displays[idx] = display
                display.target_position = display.sprite.position = self.center
                self.spritelist.append(display.sprite)
                self._layout_displays()

        if self.failed_queries >= SelectWebcamView.WEBCAM_FAIL_CAP:
            return

        if self.query_index >= len(self.webcams):
            webcam = Webcam(self.query_index)
            webcam.connect(True)
            self.webcams.append(webcam)
            self.displays.append(None)

    def _layout_displays(self):
        active_displays = tuple(display for display in self.displays if display is not None)
        max_columns = SelectWebcamView.MAX_COLUMNS
        padding = SelectWebcamView.PADDING

        count = len(active_displays)
        remainder = count % max_columns

        columns = min(max_columns, count)
        rows = count // max_columns + 1
        
        max_width = self.display_area.width - (columns - 1) * padding
        max_height = self.display_area.height - (rows - 1) * padding
        max_size = (max_width, max_height)
        dx, dy = max_width + padding, max_height + padding
        hx, hy = max_width * 0.5, max_height * 0.5
        for idx, display in enumerate(active_displays[:-remainder]):
            row = idx // max_columns
            column = idx % max_columns
            x = self.display_area.left + column * dx + hx
            y = self.display_area.top - row * dy - hy
            display.target_position = (x, y)
            display.update_max_size(max_size)

        if remainder == 0:
            return

        dx = self.display_area.width / remainder
        y = self.display_area.bottom + hy
        for idx, display in enumerate(active_displays[-remainder:]):
            display.target_position = ((idx + 0.5) * dx, y)
            display.update_max_size(max_size)
    
        