import math
import arcade
from jam2025.core.game.bullet import BasicBullet, BossBullet, BulletEmitter, BulletEvent, BulletList, BulletPattern, RainbowBullet, RandomizedBulletEmitter
from jam2025.core.game.enemy import BossEnemy, Enemy
from jam2025.core.game.wave import BossWave, Keyframe, MotionPath, Wave
from jam2025.core.settings import settings

PATTERNS: dict[str, BulletPattern] = {}
WAVES: dict[str, Wave] = {}

dummy_bullet_list = BulletList()

width = settings.window_width
height = settings.window_height
center = (width / 2, height / 2)

def load_constants() -> None:
    global PATTERNS, WAVES
    PATTERNS = {
        "right": BulletPattern(0.5, [BulletEvent(0, 1, 0)]),
        "top": BulletPattern(0.5, [BulletEvent(0, 0, 1)]),
        "bottom": BulletPattern(0.5, [BulletEvent(0, 0, -1)]),
        "left": BulletPattern(0.5, [BulletEvent(0, -1, 0)]),
        "fourway": BulletPattern(0.5, [BulletEvent(0, 1, 0), BulletEvent(0, 0, 1), BulletEvent(0, 0, -1), BulletEvent(0, -1, 0)]),
        "eightway": BulletPattern(0.5, [BulletEvent(0, 1, 0), BulletEvent(0, 0, 1), BulletEvent(0, 0, -1), BulletEvent(0, -1, 0),
                                        BulletEvent(0, 1, 1), BulletEvent(0, -1, 1), BulletEvent(0, 1, -1), BulletEvent(0, -1, -1)]),
        "eightwayfast": BulletPattern(0.33, [BulletEvent(0, 1, 0), BulletEvent(0, 0, 1), BulletEvent(0, 0, -1), BulletEvent(0, -1, 0),
                                        BulletEvent(0, 1, 1), BulletEvent(0, -1, 1), BulletEvent(0, 1, -1), BulletEvent(0, -1, -1)]),
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

    WAVES = {
        "rectangle": Wave(30, [
            MotionPath(Enemy(arcade.color.RED,
                BulletEmitter(center,
                            dummy_bullet_list,
                            BasicBullet,
                            PATTERNS["fourway"])),
            [Keyframe(0, (width * 0.25, height * 0.25)),
            Keyframe(2.5, (width * 0.75, height * 0.25)),
            Keyframe(5, (width * 0.75, height * 0.75)),
            Keyframe(7.5, (width * 0.25, height * 0.75)),
            Keyframe(10, (width * 0.25, height * 0.25))])
        ]),
        "left_and_right": Wave(20, [
            MotionPath(Enemy(arcade.color.RED,
                BulletEmitter((640, 480),
                            dummy_bullet_list,
                            BasicBullet,
                            PATTERNS["right"])),
                    [Keyframe(0, (width * 0.1, height * 0.1)),
                    Keyframe(1, (width * 0.1, height * 0.9)),
                    Keyframe(2, (width * 0.1, height * 0.1))]),
            MotionPath(Enemy(arcade.color.RED,
                BulletEmitter((640, 480),
                            dummy_bullet_list,
                            BasicBullet,
                            PATTERNS["left"])),
                    [Keyframe(0, (width * 0.9, height * 0.1)),
                    Keyframe(1, (width * 0.9, height * 0.9)),
                    Keyframe(2, (width * 0.9, height * 0.1))])
        ]),
        "boss": BossWave(600, [
            MotionPath(BossEnemy(
                RandomizedBulletEmitter(center, 64, dummy_bullet_list, BossBullet, PATTERNS["eightwayfast"])),
                    [Keyframe(0, center)])],
            lambda w, c, s: s.kills_per_wave[s.wave] >= 25)
    }

def resize_waves() -> None:
    global WAVES, width, height

    new_width_ratio = settings.window_width / width
    new_height_ratio = settings.window_width / width

    for w in WAVES.values():
        for mp in w.motion_paths:
            for k in mp.keyframes:
                k.position = (k.position[0] * new_width_ratio, k.position[1] * new_height_ratio)

    width = settings.webcam_width
    height = settings.webcam_height
