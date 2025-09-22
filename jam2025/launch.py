from jam2025.core.game.constants import load_constants
from jam2025.core.settings import settings, write_settings
from jam2025.core.navigation import navigation
from jam2025.core.application import Window
from jam2025.lib import logging
from jam2025.lib.webcam import Webcam

from .views import MouseCalibrationView, SelectWebcamView, ViewSelectView, GameView

def launch() -> None:
    try:
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
    except Exception as e:
        print("fatal exception caught flushing connected webcams")
        for webcam in Webcam._cache:
            webcam.disconnect(True)
        raise e from e
