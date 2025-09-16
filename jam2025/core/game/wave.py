from dataclasses import dataclass
from typing import Protocol, Self
from collections.abc import Callable, Sequence
from arcade import SpriteList
from arcade.types import Point2
from arcade.clock import GLOBAL_CLOCK

from jam2025.core.game.character import Character
from jam2025.core.game.score_tracker import ScoreTracker
from jam2025.lib.typing import Seconds
from .bullet import BulletEmitter, BulletList

class Enemy(Protocol):
    position: Point2
    emitter: BulletEmitter
    live: bool

@dataclass
class Keyframe:
    time: Seconds
    position: Point2

type KeyframeList = Sequence[Keyframe]

@dataclass
class EnemyKeyframes:
    enemy: Enemy
    keyframes: KeyframeList

@dataclass
class Wave:
    enemy_keyframes: Sequence[EnemyKeyframes]
    skip_condition: Callable[[Self, Character, ScoreTracker], bool] = lambda x, y, z: False

class WavePlayer:
    def __init__(self, waves: list[Wave]) -> None:
        self.waves = waves
        self._waves = self.waves.copy()

        self.bullet_list = BulletList()
        self.spritelist = SpriteList()

        self.current_wave = self._waves.pop(0)
        self.current_wave_start_time = 0.0
        self.playing = False

    def start(self) -> None:
        self.playing = True
        self.current_wave_start_time = GLOBAL_CLOCK.time

    def reset(self) -> None:
        self.playing = False
        self._waves = self.waves.copy()

    def update(self, delta_time: Seconds) -> None:
        if self.playing:
            ...
