from __future__ import annotations

from pathlib import Path
from typing import Final

GAME_TITLE: Final = "Orbit Rush"
GAME_SLUG: Final = "orbit-rush"
GAME_VERSION: Final = "0.3.0"
WINDOW_TITLE: Final = f"{GAME_TITLE} - Version {GAME_VERSION}"

ROOT: Final = Path(__file__).resolve().parent
SAVE_DIR: Final = ROOT / "saves"
SAVE_FILE: Final = SAVE_DIR / "progress.json"
SETTINGS_FILE: Final = SAVE_DIR / "settings.json"

GAME_WIDTH: Final = 1200
GAME_HEIGHT: Final = 760
FPS: Final = 60

# First-person tunnel geometry.
TUNNEL_CENTER_X: Final = GAME_WIDTH // 2
TUNNEL_CENTER_Y: Final = GAME_HEIGHT // 2 + 10
TUNNEL_NEAR_RADIUS: Final = 690.0
TUNNEL_FAR_RADIUS: Final = 24.0
VISIBLE_DISTANCE: Final = 210.0
NEAR_CLIP: Final = 1.0
RING_COUNT: Final = 18
RING_SEGMENTS: Final = 48
TUNNEL_SIDES: Final = 12
LANE_ANGLE: Final = 360.0 / TUNNEL_SIDES
PERSPECTIVE_POWER: Final = 1.72

PLAYER_START_ANGLE: Final = 270.0
PLAYER_ANGULAR_SPEED: Final = 205.0
PLAYER_ANGULAR_ACCELERATION: Final = 720.0
PLAYER_ANGULAR_FRICTION: Final = 8.0
PLAYER_COLLISION_HALF_WIDTH: Final = 11.5
PLAYER_INVULNERABLE_MS: Final = 700

CAMPAIGN_LEVELS: Final = 50
LEVELS_PER_PAGE: Final = 10
ENDLESS_START_SPEED: Final = 29.0
ENDLESS_MAX_SPEED: Final = 92.0
ENDLESS_SPEED_PER_100M: Final = 2.0
ENDLESS_START_GAP: Final = 31.0
ENDLESS_MIN_GAP: Final = 8.5
ENDLESS_GAP_REDUCTION_PER_100M: Final = 0.55
ENDLESS_GENERATE_AHEAD: Final = 280.0
ENDLESS_SAFE_OPENING: Final = 75.0
MAX_ACTIVE_OBSTACLES: Final = 85

# Obstacle kinds.
OBSTACLE_GATE = "gate"
OBSTACLE_DOUBLE_GATE = "double_gate"
OBSTACLE_BAR = "bar"
OBSTACLE_CROSS = "cross"
OBSTACLE_FAN = "fan"
OBSTACLE_SHUTTER = "shutter"
OBSTACLE_SLIDER = "slider"
OBSTACLE_PULSE = "pulse"
OBSTACLE_ZIGZAG = "zigzag"
OBSTACLE_FINISH = "finish"

OBSTACLE_TYPES: Final = (
    OBSTACLE_GATE,
    OBSTACLE_DOUBLE_GATE,
    OBSTACLE_BAR,
    OBSTACLE_CROSS,
    OBSTACLE_FAN,
    OBSTACLE_SHUTTER,
    OBSTACLE_SLIDER,
    OBSTACLE_PULSE,
    OBSTACLE_ZIGZAG,
)

# Colours.
BLACK = (2, 3, 9)
SPACE = (5, 8, 22)
DEEP_BLUE = (10, 20, 52)
PANEL = (15, 34, 76)
PANEL_2 = (25, 58, 116)
WHITE = (244, 249, 255)
GREY = (150, 168, 200)
LIGHT_GREY = (195, 210, 232)
CYAN = (85, 235, 255)
BLUE = (70, 130, 255)
GREEN = (65, 225, 135)
YELLOW = (255, 220, 75)
ORANGE = (255, 130, 55)
RED = (245, 65, 85)
PURPLE = (175, 85, 250)
PINK = (255, 80, 190)

TUNNEL_THEMES: Final = {
    "neon": {
        "background": (5, 8, 25),
        "near": (32, 100, 180),
        "far": (13, 30, 76),
        "line": CYAN,
        "accent": BLUE,
    },
    "solar": {
        "background": (24, 8, 8),
        "near": (190, 70, 25),
        "far": (70, 20, 15),
        "line": ORANGE,
        "accent": YELLOW,
    },
    "plasma": {
        "background": (16, 5, 30),
        "near": (135, 35, 195),
        "far": (48, 13, 75),
        "line": PINK,
        "accent": PURPLE,
    },
    "reactor": {
        "background": (22, 4, 10),
        "near": (180, 25, 55),
        "far": (65, 8, 25),
        "line": RED,
        "accent": ORANGE,
    },
    "void": {
        "background": (3, 4, 8),
        "near": (115, 125, 150),
        "far": (28, 32, 45),
        "line": WHITE,
        "accent": CYAN,
    },
}

DEFAULT_SAVE = {
    "save_version": 3,
    "highest_unlocked_level": 1,
    "completed_levels": [],
    "level_best_distances": {},
    "level_best_times_ms": {},
    "endless_best_distance": 0,
    "total_distance": 0,
    "total_runs": 0,
    "total_crashes": 0,
}

DEFAULT_SETTINGS = {
    "fullscreen": False,
    "screen_shake": True,
    "particles": True,
    "show_fps": False,
}

SUPABASE_URL: Final = "https://bcarxudxfmsibvnteoaj.supabase.co"
SUPABASE_KEY: Final = "sb_publishable_S7ki2S3tODs4shwWovSY6w_-2jknXXg"
SUPABASE_SCORES_TABLE: Final = "scores"
MAX_LEADERBOARD_ENTRIES: Final = 10


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def normalize_angle(angle: float) -> float:
    return angle % 360.0


def shortest_angle_difference(a: float, b: float) -> float:
    return (b - a + 180.0) % 360.0 - 180.0


def lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def colour_lerp(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = clamp(amount, 0.0, 1.0)
    return tuple(round(lerp(a[i], b[i], amount)) for i in range(3))


def format_distance(value: float) -> str:
    return f"{max(0, round(value)):,} m"


def ensure_directories() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
