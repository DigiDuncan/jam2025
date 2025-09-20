from jam2025.core.game.constants import load_constants
from .core.settings import settings, write_settings
from .core.navigation import navigation
from .core.application import Window
from jam2025.lib import logging

def launch() -> None:
    logging.setup()

    win = Window()
    load_constants()

    # I have to import these here...
    from .views import MouseCalibrationView, SelectWebcamView, ViewSelectView, GameView
    from jam2025.tests.animation_test import AnimationTestView
    from jam2025.tests.lux_blob_test import LuxBlobTest

    navigation.add_views({
        "lux": (LuxBlobTest, False),
        "v_select": (ViewSelectView, False),
        "m_calibration": (MouseCalibrationView, False),
        "select_webcam": (SelectWebcamView, False),
        "animation_test": (AnimationTestView, False),
        "game": (GameView, False)
    })
    navigation.show_view(settings.initial_view, show_splash = settings.initial_splash)
    win.run()

    write_settings(settings)
