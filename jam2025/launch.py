from .core.config import CONFIG, VIEWS
from .core.application import Window
from jam2025.lib import logging

from .views import MouseCalibrationView, PlayerTestView, IntegrationTestView

def launch() -> None:
    VIEWS.add_views({
        "m_calibration": (MouseCalibrationView, False),
        "p_test": (PlayerTestView, False),
        "i_test1": (IntegrationTestView, False)
    })

    logging.setup()

    win = Window()
    VIEWS.show_view(CONFIG.initial_view)
    win.run()
