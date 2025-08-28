from typing import Protocol
from arcade.types import Point2

NEVER = -float("inf")
FOREVER = float("inf")

# !!! TEMPORARY
class Character(Protocol):
    position: Point2
    velocity: Point2
    size: float  # The character is a circle
    health: float
