from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle
import math
from typing import Any
from arcade import Sprite, SpriteCircle, SpriteList, Texture, Vec2
from arcade.math import rotate_point
from arcade.clock import GLOBAL_CLOCK
from arcade.types import Point2
import arcade

from jam2025.core.game.score_tracker import ScoreTracker
from jam2025.core.settings import settings
from jam2025.data.loading import load_sound
from jam2025.core.game.character import Character
from jam2025.lib import noa
from jam2025.lib.typing import NEVER, Seconds
from jam2025.lib.utils import draw_cross, point_in_circle

class Bullet:
    def __init__(self, radius: float = 10, damage: float = 1, live_time: float = 10, owner: Any = None) -> None:
        self.sprite = SpriteCircle(radius, arcade.color.RED)  #type: ignore -- float -> int
        self.damage = damage
        self.live = True
        self.live_time = live_time
        self.owner: Any = owner

        self.speed: float = 100
        self.angular_speed: float = 0
        self.direction = Vec2.from_heading(0)

        self._creation_time = GLOBAL_CLOCK.time

        self.on_spawn()

    @property
    def position(self) -> Point2:
        return self.sprite.position

    @position.setter
    def position(self, pos: Point2) -> None:
        self.sprite.position = pos

    @property
    def vulnerable(self) -> bool:
        """Override this for a different system of choosing vulnerablility; currently half-way through lifetime."""
        return self._creation_time + self.live_time / 2 < GLOBAL_CLOCK.time

    def collide(self, character: Character, score_tracker: ScoreTracker) -> None:
        if self.owner is character:
            return
        if point_in_circle(character.position, character.size, self.sprite.position) and self.live:
            self.on_collide(character, score_tracker)

    def move(self, delta_time: float) -> None:
        """Override this for non-straight bullets."""
        self.direction = Vec2.from_heading(self.direction.heading() + (delta_time * self.angular_speed * math.tau))

        dx, dy = self.direction * self.speed * delta_time
        self.sprite.position = (self.sprite.position[0] + dx, self.sprite.position[1] + dy)

    def update(self, delta_time: float) -> None:
        self.on_update(delta_time)
        self.sprite.alpha = 128 if self.vulnerable else 255
        self.move(delta_time)
        if self._creation_time + self.live_time < GLOBAL_CLOCK.time:
            self.live = False
            self.on_death()
            self.on_timeout()

    def draw(self) -> None:
        ...

    def on_update(self, delta_time: float) -> None:
        ...

    def on_collide(self, character: Character, score_tracker: ScoreTracker) -> None:
        if not character.invincible:
            if self.vulnerable:
                self.live = False
                score_tracker.get_kill()
            else:
                character.health -= self.damage
                character.iframes()
                self.live = False
                self.on_death()
                self.on_killed()

    def on_spawn(self) -> None:
        ...

    def on_death(self) -> None:
        ...

    def on_killed(self) -> None:
        ...

    def on_timeout(self) -> None:
        ...

class RainbowBullet(Bullet):
    COLOR_IDX = 0

    def __init__(self, radius: Seconds = 10, damage: Seconds = 1, live_time: Seconds = 10, owner: Any = None) -> None:
        super().__init__(radius, damage, live_time, owner)
        self.sprite.color = noa.get_color(self.__class__.COLOR_IDX, 8, 8)
        self.__class__.COLOR_IDX += 1
        self.__class__.COLOR_IDX %= 12

class BulletList:
    def __init__(self, bullets: list[Bullet] | None = None) -> None:
        self.bullets = bullets if bullets else []
        self.sprite_list = SpriteList()

    def spawn_bullet(self, bullet_type: type[Bullet], pos: Point2, direction: Point2 = (0, 0),
                     speed: float = 100, angular_speed: float = 0,
                     owner: Any = None) -> None:
        new_bullet = bullet_type()
        new_bullet.position = pos
        new_bullet.direction = Vec2(*direction)
        new_bullet.speed = speed
        new_bullet.angular_speed = angular_speed
        new_bullet.owner = owner
        self.bullets.append(new_bullet)
        self.sprite_list.append(new_bullet.sprite)

    def update(self, delta_time: float, character: Character, score_tracker: ScoreTracker) -> None:
        for bullet in self.bullets:
            bullet.update(delta_time)
            bullet.collide(character, score_tracker)

        for bullet in [b for b in self.bullets if not b.live]:
            self.bullets.remove(bullet)
            self.sprite_list.remove(bullet.sprite)

    def draw(self) -> None:
        self.sprite_list.draw()
        for bullet in self.bullets:
            bullet.draw()

class BulletEmitter:
    def __init__(self, pos: Point2, bullet_list: BulletList, bullet_type: type[Bullet] = Bullet, starting_pattern: BulletPattern | None = None) -> None:
        # !!!: The webcam enabling seems to render this sprite invisible??
        # self.sprite = Sprite(get_emitter_tex())
        self.sprite = SpriteCircle(10, arcade.color.GREEN)
        self.sprite.position = pos
        self.sprite_list = SpriteList()
        self.sprite_list.append(self.sprite)
        self.bullet_type = bullet_type
        self.bullet_list = bullet_list

        self.current_pattern: BulletPattern | None = starting_pattern
        self.current_pattern_start_time: Seconds = GLOBAL_CLOCK.time

        self.direction = 0.0
        self.vulnerable = False
        self.live = True

        self.sound = load_sound('blast')

    def set_pattern(self, new_pattern: BulletPattern | None) -> None:
        self.current_pattern = new_pattern
        self.current_pattern_start_time = GLOBAL_CLOCK.time

    def collide(self, character: Character, score_tracker: ScoreTracker) -> None:
        if point_in_circle(character.position, character.size, self.sprite.position):
            if not character.invincible:
                if self.vulnerable:
                    self.live = False
                    score_tracker.get_kill()

    def update(self, delta_time: float) -> None:
        if not self.current_pattern or not self.live:
            return
        new_events = self.current_pattern.get_events(GLOBAL_CLOCK.time - self.current_pattern_start_time)
        if new_events:
            self.sound.play(0.3)
        for e in new_events:
            v = Vec2(e.direction_x, e.direction_y).normalize()
            v = v.rotate(self.direction)
            angular_speed = 0 if not e.radius else (e.speed / (math.tau * e.radius))
            self.bullet_list.spawn_bullet(self.bullet_type, self.sprite.position,
                                          v, e.speed, angular_speed)
    def draw(self) -> None:
        if self.live:
            self.sprite_list.draw()

class CycleBulletEmitter(BulletEmitter):
    def __init__(self, pos: tuple[float | int, float | int] | Vec2,
                 bullet_list: BulletList, bullet_type: type[Bullet] = Bullet, cycle_time: Seconds = 10.0,
                 patterns: list[BulletPattern] | None = None) -> None:
        super().__init__(pos, bullet_list, bullet_type, starting_pattern = None if patterns is None else patterns[0])

        self.cycle_time = cycle_time
        self.pattern_cycle = cycle(patterns) if patterns else None
        self.pattern_time = 0.0

    def update(self, delta_time: Seconds) -> None:
        self.pattern_time += delta_time
        if self.pattern_time >= self.cycle_time and self.pattern_cycle:
            self.pattern_time = 0.0
            self.set_pattern(next(self.pattern_cycle))

        super().update(delta_time)

class SpinningBulletEmitter(BulletEmitter):
    def __init__(self, pos: tuple[float | int, float | int] | Vec2, bullet_list: BulletList,
                 bullet_type: type[Bullet] = Bullet, starting_pattern: BulletPattern | None = None,
                 spin_radius: float = 40.0, spin_speed: float = 1.0) -> None:
        super().__init__(pos, bullet_list, bullet_type, starting_pattern)
        self.anchor_pos = (self.sprite.position[0] + spin_radius, self.sprite.position[1])
        self.original_pos = (self.sprite.position[0], self.sprite.position[1])
        self.spin_speed = spin_speed

    def update(self, delta_time: Seconds) -> None:
        self.sprite.position = rotate_point(self.original_pos[0], self.original_pos[1], self.anchor_pos[0], self.anchor_pos[1], GLOBAL_CLOCK.time * self.spin_speed * 360)
        super().update(delta_time)

    def draw(self) -> None:
        super().draw()
        if settings.debug:
            self.debug_draw()

    def debug_draw(self) -> None:
        draw_cross(Vec2(*self.anchor_pos), self.sprite.height, thickness = 3)

# TODO: bullet pos offset (rotate with emiiter direction?)
@dataclass
class BulletEvent:
    time: Seconds
    direction_x: float
    direction_y: float
    speed: float = 100
    radius: float = 0

class BulletPattern:
    def __init__(self, loop_time: Seconds, pattern: list[BulletEvent]) -> None:
        self.loop_time = loop_time
        self.pattern = pattern

        self._current_pattern = pattern.copy()
        self._last_pattern_time = NEVER

    def get_events(self, time: Seconds) -> list[BulletEvent]:
        current_pattern_time = time % self.loop_time
        if self._last_pattern_time > current_pattern_time:
            self._current_pattern = self.pattern.copy()
        returned_patterns = [p for p in self._current_pattern if p.time <= current_pattern_time]
        for p in returned_patterns:
            self._current_pattern.remove(p)
        self._last_pattern_time = current_pattern_time
        return returned_patterns

PATTERNS: dict[str, BulletPattern] = {
    "right": BulletPattern(0.5, [BulletEvent(0, 1, 0)]),
    "top": BulletPattern(0.5, [BulletEvent(0, 0, 1)]),
    "bottom": BulletPattern(0.5, [BulletEvent(0, 0, -1)]),
    "left": BulletPattern(0.5, [BulletEvent(0, -1, 0)]),
    "fourway": BulletPattern(0.5, [BulletEvent(0, 1, 0), BulletEvent(0, 0, 1), BulletEvent(0, 0, -1), BulletEvent(0, -1, 0)]),
    "fourwayspin": BulletPattern(0.5, [BulletEvent(0, 1, 0, radius = 200),
                                       BulletEvent(0, 0, 1, radius = 200),
                                       BulletEvent(0, 0, -1, radius = 200),
                                       BulletEvent(0, -1, 0, radius = 200)]),
    "fourwaystagger": BulletPattern(0.8, [BulletEvent(0, 0, 1),
                                          BulletEvent(0.2, 0, 0),
                                          BulletEvent(0.4, 0, -1),
                                          BulletEvent(0.6, -1, 0)]),
    "chaos": BulletPattern(
        math.pi,
        [
            BulletEvent(0*math.pi/7,  math.cos(0*math.tau/7),  math.sin(0*math.tau/7)),
            BulletEvent(0*math.pi/7, -math.cos(0*math.tau/7), -math.sin(0*math.tau/7)),
            BulletEvent(0*math.pi/7, -math.sin(0*math.tau/7),  math.cos(0*math.tau/7)),
            BulletEvent(0*math.pi/7,  math.sin(0*math.tau/7), -math.cos(0*math.tau/7)),
            BulletEvent(1*math.pi/7,  math.cos(1*math.tau/7),  math.sin(1*math.tau/7)),
            BulletEvent(1*math.pi/7, -math.cos(1*math.tau/7), -math.sin(1*math.tau/7)),
            BulletEvent(1*math.pi/7, -math.sin(1*math.tau/7),  math.cos(1*math.tau/7)),
            BulletEvent(1*math.pi/7,  math.sin(1*math.tau/7), -math.cos(1*math.tau/7)),
            BulletEvent(2*math.pi/7,  math.cos(2*math.tau/7),  math.sin(2*math.tau/7)),
            BulletEvent(2*math.pi/7, -math.cos(2*math.tau/7), -math.sin(2*math.tau/7)),
            BulletEvent(2*math.pi/7, -math.sin(2*math.tau/7),  math.cos(2*math.tau/7)),
            BulletEvent(2*math.pi/7,  math.sin(2*math.tau/7), -math.cos(2*math.tau/7)),
            BulletEvent(3*math.pi/7,  math.cos(3*math.tau/7),  math.sin(3*math.tau/7)),
            BulletEvent(3*math.pi/7, -math.cos(3*math.tau/7), -math.sin(3*math.tau/7)),
            BulletEvent(3*math.pi/7, -math.sin(3*math.tau/7),  math.cos(3*math.tau/7)),
            BulletEvent(3*math.pi/7,  math.sin(3*math.tau/7), -math.cos(3*math.tau/7)),
            BulletEvent(4*math.pi/7,  math.cos(4*math.tau/7),  math.sin(4*math.tau/7)),
            BulletEvent(4*math.pi/7, -math.cos(4*math.tau/7), -math.sin(4*math.tau/7)),
            BulletEvent(4*math.pi/7, -math.sin(4*math.tau/7),  math.cos(4*math.tau/7)),
            BulletEvent(4*math.pi/7,  math.sin(4*math.tau/7), -math.cos(4*math.tau/7)),
            BulletEvent(5*math.pi/7,  math.cos(5*math.tau/7),  math.sin(5*math.tau/7)),
            BulletEvent(5*math.pi/7, -math.cos(5*math.tau/7), -math.sin(5*math.tau/7)),
            BulletEvent(5*math.pi/7, -math.sin(5*math.tau/7),  math.cos(5*math.tau/7)),
            BulletEvent(5*math.pi/7,  math.sin(5*math.tau/7), -math.cos(5*math.tau/7)),
            BulletEvent(6*math.pi/7,  math.cos(6*math.tau/7),  math.sin(6*math.tau/7)),
            BulletEvent(6*math.pi/7, -math.cos(6*math.tau/7), -math.sin(6*math.tau/7)),
            BulletEvent(6*math.pi/7, -math.sin(6*math.tau/7),  math.cos(6*math.tau/7)),
            BulletEvent(6*math.pi/7,  math.sin(6*math.tau/7), -math.cos(6*math.tau/7)),
        ]
    )
}

emitter_tex: Texture | None = None

def get_emitter_tex() -> Texture:
    global emitter_tex
    if emitter_tex:
        return emitter_tex
    emitter_tex = Texture.create_empty("_emitter", (20, 20))
    default_atlas = arcade.get_window().ctx.default_atlas
    default_atlas.add(emitter_tex)
    with default_atlas.render_into(emitter_tex) as fbo:
        fbo.clear()
        draw_cross(Vec2(10, 10), 20, arcade.color.GREEN, 3)
    return emitter_tex
