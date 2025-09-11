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
        "game": (GameView, False),
        "select_webcam": (SelectWebcamView, False)
    })

    logging.setup()

    win = Window()
    navigation.show_view(settings.initial_view)
    win.run()

    write_settings(settings)
