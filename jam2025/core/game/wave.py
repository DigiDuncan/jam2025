from dataclasses import dataclass
from typing import Self
from collections.abc import Callable, Sequence
from arcade import SpriteList, Vec2
from arcade.types import Point2
from arcade.clock import GLOBAL_CLOCK

from jam2025.core.game.bullet import BulletList
from jam2025.core.game.character import Character
from jam2025.core.game.enemy import Enemy
from jam2025.core.game.score_tracker import ScoreTracker
from jam2025.lib.anim import lerp, perc
from jam2025.lib.typing import Seconds

@dataclass
class Keyframe:
    time: Seconds
    position: Point2

type KeyframeList = Sequence[Keyframe]

@dataclass
class MotionPath:
    enemy: Enemy
    keyframes: KeyframeList

    def update_position(self, time: Seconds) -> None:
        if time <= self.keyframes[0].time:
            # We're before keyframe 1
            self.enemy.position = self.keyframes[0].position
        elif time >= self.keyframes[-1].time:
            # We're after the last keyframe
            self.enemy.position = self.keyframes[-1].position
        else:
            # Get the index we're within:
            current_keyframe = Keyframe(0, (0, 0))
            current_keyframe_index = 0
            for i, k in enumerate(self.keyframes):
                if k.time <= time:
                    current_keyframe = k
                    current_keyframe_index = i
                else:
                    break
            next_keyframe = self.keyframes[current_keyframe_index + 1]
            current_x = lerp(current_keyframe.position[0], next_keyframe.position[0], perc(current_keyframe.time, next_keyframe.time, time))
            current_y = lerp(current_keyframe.position[1], next_keyframe.position[1], perc(current_keyframe.time, next_keyframe.time, time))
            self.enemy.position = Vec2(current_x, current_y)


@dataclass
class Wave:
    total_time: Seconds
    motion_paths: Sequence[MotionPath]
    skip_condition: Callable[[Self, Character, ScoreTracker], bool] = lambda x, y, z: False

class BossWave(Wave):
    ...

class WavePlayer:
    def __init__(self, waves: list[Wave], character: Character, score_tracker: ScoreTracker) -> None:
        self.waves = waves
        self._waves = self.waves.copy()

        self.wave_count = 0

        self.character = character
        self.score_tracker = score_tracker

        self.bullet_list = BulletList()
        self.spritelist = SpriteList()

        for w in self.waves:
            for mp in w.motion_paths:
                mp.enemy.emitter.bullet_list = self.bullet_list
        self.playing = False
        self.strict = False

    def start(self) -> None:
        self.playing = True
        self.next_wave()

    def next_wave(self) -> None:
        if self._waves:
            self.current_wave = self._waves.pop(0)
            self.current_wave_start_time = GLOBAL_CLOCK.time
        elif self.strict:
            raise RuntimeError("No more waves!")
        else:
            self._waves = self.waves.copy()
            self.current_wave = self._waves.pop(0)
            self.current_wave_start_time = GLOBAL_CLOCK.time

        self.spritelist.clear()
        self.wave_count += 1
        self.score_tracker.wave = self.wave_count
        self.character.health = min(self.character.max_health, self.character.health + 1)

    def reset(self) -> None:
        self.playing = False
        self._waves = self.waves.copy()
        self.bullet_list.reset()
        self.spritelist.clear()
        self.score_tracker.reset()
        self.wave_count = 0
        self.score_tracker.wave = 0

    def update(self, delta_time: Seconds) -> None:
        if self.playing:
            if (GLOBAL_CLOCK.time > self.current_wave_start_time + self.current_wave.total_time or
                self.current_wave.skip_condition(self.current_wave, self.character, self.score_tracker)):
                self.next_wave()

            self.bullet_list.update(delta_time, self.character, self.score_tracker)
            self.score_tracker.update(delta_time)
            self.spritelist.update(delta_time)

            for mp in self.current_wave.motion_paths:
                mp.update_position(GLOBAL_CLOCK.time - self.current_wave_start_time)
                mp.enemy.emitter.update(delta_time)
                if hasattr(mp.enemy, "sprite_list"):
                    mp.enemy.sprite_list.update_animation(delta_time)

    def draw(self) -> None:
        self.spritelist.draw()
        self.bullet_list.draw()
        self.character.draw()
        for mp in self.current_wave.motion_paths:
            mp.enemy.emitter.sprite_list.draw()
            mp.enemy.draw()
