from jam2025.views.animation_test import AnimationTestView
from jam2025.views.wave_test import WaveTestView
from .core.settings import settings, write_settings
from .core.navigation import navigation
from .core.application import Window
from jam2025.lib import logging

from .views import MouseCalibrationView, PlayerTestView, IntegrationTestView, LuxBlobTest, SelectWebcamView, ViewSelectView, GameView

def launch() -> None:
    navigation.add_views({
        "lux": (LuxBlobTest, False),
        "v_select": (ViewSelectView, False),
        "m_calibration": (MouseCalibrationView, False),
        "p_test": (PlayerTestView, False),
        "i_test1": (IntegrationTestView, False),
        "select_webcam": (SelectWebcamView, False),
        "animation_test": (AnimationTestView, False),
        "wave_test": (WaveTestView, False),
        "game": (GameView, False)
    })

    logging.setup()

    win = Window()
    navigation.show_view(settings.initial_view, show_splash = False)
    win.run()

    write_settings(settings)
