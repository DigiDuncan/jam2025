from arcade import View as ArcadeView, Sprite, SpriteList, Rect, LRBT

from jam2025.core.settings import settings
from jam2025.core.webcam import SimpleAnimatedWebcamDisplay

from jam2025.lib.webcam import Webcam

WEBCAM_FRACTIONS: tuple[tuple[tuple[float, float], ...], ...] = (
    (),
    ((1/2, 1/2),),
    ((1/4, 1/2), (3/4, 1/2)),
    ((1/4, 3/4), (3/4, 3/4), (1/2, 1/4)),
    ((1/4, 3/4), (3/4, 3/4), (1/4, 1/4), (3/4, 1/4)),
    ((1/6, 3/4), (3/6, 3/4), (5/6, 3/4), (1/4, 1/4), (3/4, 1/4)),
    ((1/6, 3/4), (3/6, 3/4), (5/6, 3/4), (1/6, 1/4), (2/6, 1/4), (3/4, 1/4))
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
    PADDING = 80.0

    def __init__(self) -> None:
        super().__init__()

        self.query_index: int
        self.failed_queries: int

        self.connecting_webcam: Webcam | None
        self.hovered_display: SimpleAnimatedWebcamDisplay | None

        self.webcams: list[Webcam]
        self.displays: list[SimpleAnimatedWebcamDisplay]
        self.spritelist: SpriteList[Sprite]

        self.display_area: Rect

    def on_show_view(self) -> None:
        self.spritelist = SpriteList()
        padding = SelectWebcamView.PADDING
        self.display_area = LRBT(
            padding*0.5,
            self.width - padding*0.5,
            padding*0.5,
            self.height - padding*0.5
        )

        if settings.connected_webcam is not None:
            pass    

        initial_id = settings.webcam_id
        webcam = Webcam(initial_id)
        webcam.connect(True)

        self.connecting_webcam = webcam
        self.hovered_display = None
        self.clicked_display = None

        self.webcams = []
        self.displays = []
        self.query_index = 0
        self.failed_queries = 0

    def _create_display(self, webcam: Webcam) -> SimpleAnimatedWebcamDisplay:
        display = SimpleAnimatedWebcamDisplay(webcam)
        self.spritelist.append(display.sprite)
        return display

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

        if not displays:
            return

        positions = WEBCAM_FRACTIONS[count]
        sizing = WEBCAM_SIZING[count]

        width = self.display_area.width / sizing[0]
        height = self.display_area.height / sizing[1]
        full_size = width, height
        size = width - padding, height - padding
        sub_size = width - 2*padding, height - 2*padding

        for position, display in zip(positions, displays):
            display.target_position = self.display_area.uv_to_position(position)
            if display is self.clicked_display:
                display.update_max_size(sub_size)
            else:
                display.update_max_size(full_size if display is self.hovered_display else size)


    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        p = (x, y)

        for display in self.displays:
            if display.contains_point(p):
                if display == self.hovered_display:
                    break
                self.hovered_display = display
                self._layout_displays()
                break
        else:
            if self.hovered_display is not None:
                self.hovered_display = None
                self._layout_displays()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        pass

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        pass