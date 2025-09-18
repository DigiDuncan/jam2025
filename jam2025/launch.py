from .core.settings import settings, write_settings
from .core.navigation import navigation
from .core.application import Window
from jam2025.lib import logging

from .views import MouseCalibrationView, SelectWebcamView, ViewSelectView, GameView
from jam2025.tests.animation_test import AnimationTestView
from jam2025.tests.integration_test import IntegrationTestView
from jam2025.tests.lux_blob_test import LuxBlobTest
from jam2025.tests.player_test import PlayerTestView

def launch() -> None:
    navigation.add_views({
        "lux": (LuxBlobTest, False),
        "v_select": (ViewSelectView, False),
        "m_calibration": (MouseCalibrationView, False),
        "p_test": (PlayerTestView, False),
        "i_test1": (IntegrationTestView, False),
        "select_webcam": (SelectWebcamView, False),
        "animation_test": (AnimationTestView, False),
        "game": (GameView, False)
    })

    logging.setup()

    win = Window()
    navigation.show_view(settings.initial_view, show_splash = False)
    win.run()

    write_settings(settings)
