from .calibration_step1 import MouseCalibrationView
from .player_test import PlayerTestView
from .integration_test import IntegrationTestView
from .select import ViewSelectView

from .calibration.select_webcam import SelectWebcamView

__all__ = (
    "MouseCalibrationView",
    "PlayerTestView",
    "IntegrationTestView",
    "ViewSelectView",
    "SelectWebcamView"
)

