from arcade import View as ArcadeView, Sprite, SpriteList, Rect, LRBT

from jam2025.core.settings import settings
from jam2025.core.webcam import SimpleAnimatedWebcamDisplay

from jam2025.lib.webcam import Webcam


WEBCAM_FRACTIONS: tuple[tuple[tuple[float, float], ...], ...] = (
    (),
    ((1/2, 1/2),),
    ((1/3, 1/2), (2/3, 1/2)),
    ((1/3, 2/3), (2/3, 2/3), (1/2, 1/3)),
    ((1/3, 2/3), (2/3, 2/3), (1/3, 1/3), (2/3, 1/3)),
    ((1/4, 2/3), (2/4, 2/3), (3/4, 2/3), (1/3, 1/3), (2/3, 1/3)),
    ((1/4, 2/3), (2/4, 2/3), (3/4, 2/3), (1/4, 1/3), (2/4, 1/3), (3/4, 1/3))
)
WEBCAM_SIZING = (
    (1, 1),
    (1, 1),
    (2, 1),
    (2, 2),
    (2, 2),
    (3, 2),
    (3, 2),
)


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
    WEBCAM_CAP = 6
    PADDING = 30.0

    def __init__(self) -> None:
        super().__init__()

        self.query_index: int
        self.failed_queries: int

        self.connecting_webcam: Webcam | None

        self.webcams: list[Webcam]
        self.displays: list[SimpleAnimatedWebcamDisplay]
        self.spritelist: SpriteList[Sprite]

        self.display_area: Rect

    def on_show_view(self) -> None:
        self.spritelist = SpriteList()

        initial_id = settings.webcam_id
        webcam = Webcam(initial_id)
        webcam.connect(True)

        self.connecting_webcam = webcam

        self.webcams = []
        self.displays = []
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
            display.update(delta_time)

    def _validate_webcams(self):
        if self.connecting_webcam is None:
            return
        
        state = self.connecting_webcam.state
        if state == Webcam.ERROR or state == Webcam.DISCONNECTED:
            # This webcam failed to connect
            self.failed_queries += 1
            self._setup_next_webcam()
            return
        
        if state == Webcam.CONNECTED:
            self.webcams.append(self.connecting_webcam)
            display = SimpleAnimatedWebcamDisplay(self.connecting_webcam)
            self.displays.append(display)
            self.spritelist.append(display.sprite)
            self._layout_displays()
            self._setup_next_webcam()

    def _setup_next_webcam(self):
        if self.failed_queries >= SelectWebcamView.WEBCAM_FAIL_CAP:
            self.connecting_webcam = None
            return
        self.query_index += 1
        if self.query_index >= SelectWebcamView.WEBCAM_CAP:
            self.connecting_webcam = None
            return
        self.connecting_webcam = Webcam(self.query_index)
        self.connecting_webcam.connect(True)


    def _layout_displays(self):
        padding = SelectWebcamView.PADDING
        displays = self.displays
        count = len(displays)

        position_arrays = WEBCAM_FRACTIONS[count]
        columns, rows = WEBCAM_SIZING[count]

        width = (self.display_area.width - (columns - 1) * padding)
        print(self.display_area.width, width)
        height = (self.display_area.height - (rows - 1) * padding)
        max_size = (width / columns, height / rows)
        for display, position in zip(self.displays, position_arrays):
            display.target_position = self.display_area.uv_to_position(position)
            display.update_max_size(max_size)
    
        