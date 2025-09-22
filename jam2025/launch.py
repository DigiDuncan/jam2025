from jam2025.core.game.constants import load_constants
from .core.settings import settings, write_settings
from .core.navigation import navigation
from .core.application import Window
from jam2025.lib import logging

from .views import MouseCalibrationView, SelectWebcamView, ViewSelectView, GameView

def launch() -> None:
    logging.setup()

    win = Window()
    load_constants()

    # I have to import these here...
    navigation.add_views({
        "v_select": (ViewSelectView, False),
        "select_webcam": (SelectWebcamView, False),
        "calibration": (MouseCalibrationView, False),
        "play": (GameView, False)
    })
    navigation.show_view(settings.initial_view, show_splash = settings.initial_splash)
    win.run()

    write_settings(settings)
