from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


# ============================================================
# GAME IDENTITY
# ============================================================

GAME_TITLE: Final[str] = "Orbit Rush"
GAME_SLUG: Final[str] = "orbit-rush"

# Increase this after every game update.
GAME_VERSION: Final[str] = "0.1.0"

WINDOW_TITLE: Final[str] = (
    f"{GAME_TITLE} - Version {GAME_VERSION}"
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIRECTORY: Final[Path] = Path(__file__).resolve().parent

ASSETS_DIRECTORY: Final[Path] = (
    PROJECT_DIRECTORY
    / "assets"
)

IMAGES_DIRECTORY: Final[Path] = (
    ASSETS_DIRECTORY
    / "images"
)

SOUNDS_DIRECTORY: Final[Path] = (
    ASSETS_DIRECTORY
    / "sounds"
)

FONTS_DIRECTORY: Final[Path] = (
    ASSETS_DIRECTORY
    / "fonts"
)

SAVE_DIRECTORY: Final[Path] = (
    PROJECT_DIRECTORY
    / "saves"
)

SAVE_FILE: Final[Path] = (
    SAVE_DIRECTORY
    / "progress.json"
)

SETTINGS_FILE: Final[Path] = (
    SAVE_DIRECTORY
    / "settings.json"
)

LOCAL_LEADERBOARD_FILE: Final[Path] = (
    SAVE_DIRECTORY
    / "leaderboard.json"
)


# ============================================================
# DISPLAY
# ============================================================

GAME_WIDTH: Final[int] = 1200
GAME_HEIGHT: Final[int] = 760

GAME_ASPECT_RATIO: Final[float] = (
    GAME_WIDTH
    / GAME_HEIGHT
)

FPS: Final[int] = 60

START_FULLSCREEN: Final[bool] = False
ALLOW_FULLSCREEN: Final[bool] = True
ALLOW_RESIZING: Final[bool] = True

USE_INTEGER_SCALING_WHEN_POSSIBLE: Final[bool] = True
USE_SMOOTH_SCALING: Final[bool] = True

LETTERBOX_COLOUR: Final[tuple[int, int, int]] = (
    1,
    3,
    10,
)


# ============================================================
# GAME STATES
# ============================================================

STATE_ACCOUNT_LOADING: Final[str] = "account_loading"
STATE_ACCOUNT_REQUIRED: Final[str] = "account_required"

STATE_MAIN_MENU: Final[str] = "main_menu"
STATE_MODE_SELECT: Final[str] = "mode_select"
STATE_LEVEL_SELECT: Final[str] = "level_select"

STATE_COUNTDOWN: Final[str] = "countdown"
STATE_PLAYING: Final[str] = "playing"
STATE_PAUSED: Final[str] = "paused"

STATE_LEVEL_COMPLETE: Final[str] = "level_complete"
STATE_GAME_OVER: Final[str] = "game_over"
STATE_LEADERBOARD: Final[str] = "leaderboard"

STATE_SETTINGS: Final[str] = "settings"
STATE_ACHIEVEMENTS: Final[str] = "achievements"
STATE_STATISTICS: Final[str] = "statistics"


# ============================================================
# GAME MODES
# ============================================================

MODE_LEVELS: Final[str] = "levels"
MODE_ENDLESS: Final[str] = "endless"

VALID_GAME_MODES: Final[tuple[str, ...]] = (
    MODE_LEVELS,
    MODE_ENDLESS,
)


# ============================================================
# CYLINDER GEOMETRY
# ============================================================

CYLINDER_CENTER_X: Final[int] = (
    GAME_WIDTH
    // 2
)

CYLINDER_HORIZON_Y: Final[int] = 178

CYLINDER_PLAYER_Y: Final[int] = (
    GAME_HEIGHT
    - 118
)

CYLINDER_NEAR_RADIUS: Final[float] = 480.0
CYLINDER_FAR_RADIUS: Final[float] = 34.0

CYLINDER_VISIBLE_DISTANCE: Final[float] = 170.0
CYLINDER_NEAR_CLIP_DISTANCE: Final[float] = 1.0

CYLINDER_RING_SPACING: Final[float] = 8.0
CYLINDER_RING_COUNT: Final[int] = 24

CYLINDER_LANE_COUNT: Final[int] = 12

CYLINDER_FULL_ROTATION: Final[float] = 360.0

CYLINDER_LANE_ANGLE: Final[float] = (
    CYLINDER_FULL_ROTATION
    / CYLINDER_LANE_COUNT
)

CYLINDER_ROTATION_SPEED: Final[float] = 145.0
CYLINDER_ROTATION_ACCELERATION: Final[float] = 620.0
CYLINDER_ROTATION_FRICTION: Final[float] = 8.5

CYLINDER_MAX_ROTATION_VELOCITY: Final[float] = 180.0

CYLINDER_PERSPECTIVE_POWER: Final[float] = 1.72
CYLINDER_CURVE_STRENGTH: Final[float] = 0.92

CYLINDER_SURFACE_SEGMENTS: Final[int] = 72


# ============================================================
# PLAYER
# ============================================================

PLAYER_SCREEN_WIDTH: Final[int] = 50
PLAYER_SCREEN_HEIGHT: Final[int] = 62

PLAYER_COLLISION_WIDTH: Final[float] = 16.0
PLAYER_COLLISION_DEPTH: Final[float] = 4.4

PLAYER_STARTING_ANGLE: Final[float] = 0.0

PLAYER_BASE_FORWARD_SPEED: Final[float] = 22.0
PLAYER_MAX_FORWARD_SPEED: Final[float] = 68.0

PLAYER_SPEED_ACCELERATION: Final[float] = 0.014
PLAYER_SPEED_INCREASE_INTERVAL: Final[float] = 10.0

PLAYER_LEVEL_RESTART_DELAY_MS: Final[int] = 900
PLAYER_CRASH_DELAY_MS: Final[int] = 1250

PLAYER_INVINCIBILITY_MS: Final[int] = 1200

PLAYER_PARTICLE_RATE: Final[int] = 4
PLAYER_TRAIL_LENGTH: Final[int] = 18

PLAYER_DEFAULT_LIVES: Final[int] = 1

ALLOW_PLAYER_JUMP: Final[bool] = False
ALLOW_PLAYER_POWERUPS: Final[bool] = True
ALLOW_PLAYER_COSMETICS: Final[bool] = True


# ============================================================
# DISTANCE AND SCORING
# ============================================================

WORLD_UNITS_PER_METRE: Final[float] = 1.0

DISTANCE_DECIMAL_PLACES: Final[int] = 0

ENDLESS_SCORE_MULTIPLIER: Final[float] = 1.0

LEVEL_COMPLETION_SCORE_BASE: Final[int] = 1000
LEVEL_COMPLETION_SCORE_PER_METRE: Final[int] = 2

PERFECT_LEVEL_BONUS: Final[int] = 500
NO_BRAKE_BONUS: Final[int] = 250

MAX_LEADERBOARD_ENTRIES: Final[int] = 10

LEADERBOARD_DISTANCE_LIMIT: Final[int] = 100_000_000

LEADERBOARD_GAME_ID: Final[str] = GAME_SLUG


# ============================================================
# ENDLESS MODE
# ============================================================

ENDLESS_STARTING_SPEED: Final[float] = 24.0
ENDLESS_MAX_SPEED: Final[float] = 72.0

ENDLESS_SPEED_GAIN_PER_100_METRES: Final[float] = 1.55

ENDLESS_STARTING_OBSTACLE_GAP: Final[float] = 34.0
ENDLESS_MINIMUM_OBSTACLE_GAP: Final[float] = 10.0

ENDLESS_GAP_REDUCTION_PER_100_METRES: Final[float] = 0.72

ENDLESS_STARTING_DIFFICULTY: Final[float] = 1.0
ENDLESS_MAX_DIFFICULTY: Final[float] = 25.0

ENDLESS_DIFFICULTY_PER_100_METRES: Final[float] = 0.68

ENDLESS_SECTION_LENGTH_MIN: Final[float] = 60.0
ENDLESS_SECTION_LENGTH_MAX: Final[float] = 130.0

ENDLESS_SAFE_START_DISTANCE: Final[float] = 70.0

ENDLESS_GENERATION_AHEAD_DISTANCE: Final[float] = 280.0
ENDLESS_REMOVE_BEHIND_DISTANCE: Final[float] = 24.0

ENDLESS_MAX_ACTIVE_OBSTACLES: Final[int] = 90

ENDLESS_GUARANTEE_POSSIBLE_PATH: Final[bool] = True
ENDLESS_MAX_CONSECUTIVE_HARD_PATTERNS: Final[int] = 3

ENDLESS_MOVING_OBSTACLE_UNLOCK_DISTANCE: Final[int] = 350
ENDLESS_ROTATING_OBSTACLE_UNLOCK_DISTANCE: Final[int] = 650
ENDLESS_FAKE_GAP_UNLOCK_DISTANCE: Final[int] = 1000
ENDLESS_PULSE_OBSTACLE_UNLOCK_DISTANCE: Final[int] = 1400
ENDLESS_CHASER_UNLOCK_DISTANCE: Final[int] = 2000


# ============================================================
# CAMPAIGN LEVELS
# ============================================================

TOTAL_LEVELS: Final[int] = 50

FIRST_UNLOCKED_LEVEL: Final[int] = 1

LEVEL_MINIMUM_LENGTH: Final[float] = 220.0
LEVEL_MAXIMUM_LENGTH: Final[float] = 1650.0

LEVEL_STARTING_SPEED_MIN: Final[float] = 18.0
LEVEL_STARTING_SPEED_MAX: Final[float] = 48.0

LEVEL_FINISH_LINE_DISTANCE: Final[float] = 12.0

LEVEL_COUNTDOWN_SECONDS: Final[int] = 3

LEVEL_UNLOCK_NEXT_ON_COMPLETION: Final[bool] = True
LEVEL_ALLOW_REPLAY: Final[bool] = True

LEVEL_CHECKPOINTS_ENABLED: Final[bool] = False

LEVEL_DIFFICULTY_NAMES: Final[tuple[str, ...]] = (
    "Beginner",
    "Easy",
    "Moderate",
    "Challenging",
    "Hard",
    "Extreme",
    "Impossible",
)


# ============================================================
# LEVEL DIFFICULTY TIERS
# ============================================================

@dataclass(frozen=True)
class LevelTier:
    name: str

    first_level: int
    last_level: int

    starting_speed: float
    maximum_speed: float

    obstacle_gap: float
    obstacle_density: float

    moving_obstacle_chance: float
    rotating_obstacle_chance: float
    fake_gap_chance: float

    pattern_complexity: int


LEVEL_TIERS: Final[tuple[LevelTier, ...]] = (
    LevelTier(
        name="Beginner",
        first_level=1,
        last_level=5,
        starting_speed=18.0,
        maximum_speed=24.0,
        obstacle_gap=33.0,
        obstacle_density=0.35,
        moving_obstacle_chance=0.00,
        rotating_obstacle_chance=0.00,
        fake_gap_chance=0.00,
        pattern_complexity=1,
    ),

    LevelTier(
        name="Easy",
        first_level=6,
        last_level=10,
        starting_speed=21.0,
        maximum_speed=29.0,
        obstacle_gap=29.0,
        obstacle_density=0.44,
        moving_obstacle_chance=0.04,
        rotating_obstacle_chance=0.00,
        fake_gap_chance=0.00,
        pattern_complexity=2,
    ),

    LevelTier(
        name="Moderate",
        first_level=11,
        last_level=20,
        starting_speed=25.0,
        maximum_speed=36.0,
        obstacle_gap=25.0,
        obstacle_density=0.54,
        moving_obstacle_chance=0.10,
        rotating_obstacle_chance=0.04,
        fake_gap_chance=0.00,
        pattern_complexity=3,
    ),

    LevelTier(
        name="Challenging",
        first_level=21,
        last_level=30,
        starting_speed=30.0,
        maximum_speed=43.0,
        obstacle_gap=21.5,
        obstacle_density=0.64,
        moving_obstacle_chance=0.18,
        rotating_obstacle_chance=0.10,
        fake_gap_chance=0.03,
        pattern_complexity=4,
    ),

    LevelTier(
        name="Hard",
        first_level=31,
        last_level=40,
        starting_speed=35.0,
        maximum_speed=52.0,
        obstacle_gap=18.5,
        obstacle_density=0.73,
        moving_obstacle_chance=0.25,
        rotating_obstacle_chance=0.17,
        fake_gap_chance=0.08,
        pattern_complexity=5,
    ),

    LevelTier(
        name="Extreme",
        first_level=41,
        last_level=49,
        starting_speed=41.0,
        maximum_speed=62.0,
        obstacle_gap=15.0,
        obstacle_density=0.82,
        moving_obstacle_chance=0.34,
        rotating_obstacle_chance=0.25,
        fake_gap_chance=0.14,
        pattern_complexity=6,
    ),

    LevelTier(
        name="Impossible",
        first_level=50,
        last_level=50,
        starting_speed=48.0,
        maximum_speed=70.0,
        obstacle_gap=11.5,
        obstacle_density=0.92,
        moving_obstacle_chance=0.45,
        rotating_obstacle_chance=0.38,
        fake_gap_chance=0.20,
        pattern_complexity=8,
    ),
)


# ============================================================
# OBSTACLE TYPES
# ============================================================

OBSTACLE_BLOCK: Final[str] = "block"
OBSTACLE_WIDE_BLOCK: Final[str] = "wide_block"
OBSTACLE_TALL_BLOCK: Final[str] = "tall_block"

OBSTACLE_WALL_GAP: Final[str] = "wall_gap"
OBSTACLE_DOUBLE_GAP: Final[str] = "double_gap"
OBSTACLE_NARROW_GATE: Final[str] = "narrow_gate"

OBSTACLE_MOVING_BLOCK: Final[str] = "moving_block"
OBSTACLE_ROTATING_WALL: Final[str] = "rotating_wall"

OBSTACLE_PULSE_BLOCK: Final[str] = "pulse_block"
OBSTACLE_FAKE_GAP: Final[str] = "fake_gap"
OBSTACLE_CHASER: Final[str] = "chaser"

OBSTACLE_SPIKE: Final[str] = "spike"
OBSTACLE_LASER: Final[str] = "laser"

OBSTACLE_FINISH_LINE: Final[str] = "finish_line"


@dataclass(frozen=True)
class ObstacleDefinition:
    obstacle_type: str
    display_name: str

    lane_width: float
    depth: float
    height: float

    base_colour: tuple[int, int, int]
    highlight_colour: tuple[int, int, int]

    movement_speed: float = 0.0
    rotation_speed: float = 0.0

    lethal: bool = True
    animated: bool = False

    minimum_level: int = 1
    minimum_endless_distance: int = 0

    score_value: int = 0


OBSTACLE_DEFINITIONS: Final[
    dict[str, ObstacleDefinition]
] = {
    OBSTACLE_BLOCK: ObstacleDefinition(
        obstacle_type=OBSTACLE_BLOCK,
        display_name="Barrier",
        lane_width=0.72,
        depth=5.0,
        height=1.0,
        base_colour=(235, 65, 92),
        highlight_colour=(255, 150, 170),
        minimum_level=1,
    ),

    OBSTACLE_WIDE_BLOCK: ObstacleDefinition(
        obstacle_type=OBSTACLE_WIDE_BLOCK,
        display_name="Wide Barrier",
        lane_width=1.65,
        depth=5.5,
        height=1.0,
        base_colour=(235, 95, 55),
        highlight_colour=(255, 185, 100),
        minimum_level=4,
    ),

    OBSTACLE_TALL_BLOCK: ObstacleDefinition(
        obstacle_type=OBSTACLE_TALL_BLOCK,
        display_name="Tower Barrier",
        lane_width=0.78,
        depth=6.0,
        height=1.55,
        base_colour=(165, 70, 235),
        highlight_colour=(220, 155, 255),
        minimum_level=7,
    ),

    OBSTACLE_WALL_GAP: ObstacleDefinition(
        obstacle_type=OBSTACLE_WALL_GAP,
        display_name="Gap Wall",
        lane_width=9.5,
        depth=5.5,
        height=1.2,
        base_colour=(60, 145, 235),
        highlight_colour=(135, 215, 255),
        minimum_level=3,
    ),

    OBSTACLE_DOUBLE_GAP: ObstacleDefinition(
        obstacle_type=OBSTACLE_DOUBLE_GAP,
        display_name="Double Gap Wall",
        lane_width=9.5,
        depth=5.8,
        height=1.25,
        base_colour=(45, 185, 205),
        highlight_colour=(140, 255, 255),
        minimum_level=12,
    ),

    OBSTACLE_NARROW_GATE: ObstacleDefinition(
        obstacle_type=OBSTACLE_NARROW_GATE,
        display_name="Narrow Gate",
        lane_width=10.5,
        depth=6.2,
        height=1.3,
        base_colour=(255, 180, 55),
        highlight_colour=(255, 235, 130),
        minimum_level=18,
    ),

    OBSTACLE_MOVING_BLOCK: ObstacleDefinition(
        obstacle_type=OBSTACLE_MOVING_BLOCK,
        display_name="Moving Barrier",
        lane_width=0.85,
        depth=5.0,
        height=1.15,
        base_colour=(255, 75, 185),
        highlight_colour=(255, 165, 225),
        movement_speed=65.0,
        animated=True,
        minimum_level=8,
        minimum_endless_distance=(
            ENDLESS_MOVING_OBSTACLE_UNLOCK_DISTANCE
        ),
    ),

    OBSTACLE_ROTATING_WALL: ObstacleDefinition(
        obstacle_type=OBSTACLE_ROTATING_WALL,
        display_name="Rotating Wall",
        lane_width=7.0,
        depth=6.0,
        height=1.35,
        base_colour=(95, 105, 255),
        highlight_colour=(180, 190, 255),
        rotation_speed=52.0,
        animated=True,
        minimum_level=16,
        minimum_endless_distance=(
            ENDLESS_ROTATING_OBSTACLE_UNLOCK_DISTANCE
        ),
    ),

    OBSTACLE_PULSE_BLOCK: ObstacleDefinition(
        obstacle_type=OBSTACLE_PULSE_BLOCK,
        display_name="Pulse Barrier",
        lane_width=1.0,
        depth=5.0,
        height=1.0,
        base_colour=(255, 55, 105),
        highlight_colour=(255, 220, 235),
        animated=True,
        minimum_level=28,
        minimum_endless_distance=(
            ENDLESS_PULSE_OBSTACLE_UNLOCK_DISTANCE
        ),
    ),

    OBSTACLE_FAKE_GAP: ObstacleDefinition(
        obstacle_type=OBSTACLE_FAKE_GAP,
        display_name="False Opening",
        lane_width=9.5,
        depth=6.0,
        height=1.25,
        base_colour=(190, 65, 255),
        highlight_colour=(240, 180, 255),
        animated=True,
        minimum_level=34,
        minimum_endless_distance=(
            ENDLESS_FAKE_GAP_UNLOCK_DISTANCE
        ),
    ),

    OBSTACLE_CHASER: ObstacleDefinition(
        obstacle_type=OBSTACLE_CHASER,
        display_name="Tracking Barrier",
        lane_width=0.9,
        depth=5.5,
        height=1.2,
        base_colour=(255, 55, 55),
        highlight_colour=(255, 180, 180),
        movement_speed=42.0,
        animated=True,
        minimum_level=42,
        minimum_endless_distance=(
            ENDLESS_CHASER_UNLOCK_DISTANCE
        ),
    ),

    OBSTACLE_SPIKE: ObstacleDefinition(
        obstacle_type=OBSTACLE_SPIKE,
        display_name="Energy Spike",
        lane_width=0.6,
        depth=4.0,
        height=1.8,
        base_colour=(235, 225, 70),
        highlight_colour=(255, 255, 190),
        minimum_level=23,
    ),

    OBSTACLE_LASER: ObstacleDefinition(
        obstacle_type=OBSTACLE_LASER,
        display_name="Laser Gate",
        lane_width=4.0,
        depth=3.0,
        height=1.45,
        base_colour=(255, 45, 75),
        highlight_colour=(255, 220, 225),
        animated=True,
        minimum_level=38,
    ),

    OBSTACLE_FINISH_LINE: ObstacleDefinition(
        obstacle_type=OBSTACLE_FINISH_LINE,
        display_name="Finish Line",
        lane_width=12.0,
        depth=4.0,
        height=0.15,
        base_colour=(65, 235, 145),
        highlight_colour=(210, 255, 225),
        lethal=False,
        minimum_level=1,
    ),
}


# ============================================================
# OBSTACLE PATTERN TYPES
# ============================================================

PATTERN_SINGLE: Final[str] = "single"
PATTERN_DOUBLE: Final[str] = "double"
PATTERN_TRIPLE: Final[str] = "triple"

PATTERN_WALL: Final[str] = "wall"
PATTERN_ZIGZAG: Final[str] = "zigzag"
PATTERN_SLALOM: Final[str] = "slalom"

PATTERN_SPIRAL: Final[str] = "spiral"
PATTERN_ROTATING: Final[str] = "rotating"
PATTERN_MOVING: Final[str] = "moving"

PATTERN_GAUNTLET: Final[str] = "gauntlet"
PATTERN_BOSS_SECTION: Final[str] = "boss_section"

ALL_PATTERN_TYPES: Final[tuple[str, ...]] = (
    PATTERN_SINGLE,
    PATTERN_DOUBLE,
    PATTERN_TRIPLE,
    PATTERN_WALL,
    PATTERN_ZIGZAG,
    PATTERN_SLALOM,
    PATTERN_SPIRAL,
    PATTERN_ROTATING,
    PATTERN_MOVING,
    PATTERN_GAUNTLET,
    PATTERN_BOSS_SECTION,
)


# ============================================================
# COLLECTIBLES AND POWER-UPS
# ============================================================

COLLECTIBLE_ENERGY: Final[str] = "energy"
COLLECTIBLE_SHIELD: Final[str] = "shield"
COLLECTIBLE_SLOW_TIME: Final[str] = "slow_time"
COLLECTIBLE_SCORE_MULTIPLIER: Final[str] = "score_multiplier"

POWERUPS_ENABLED_IN_LEVELS: Final[bool] = True
POWERUPS_ENABLED_IN_ENDLESS: Final[bool] = True

POWERUP_SPAWN_CHANCE: Final[float] = 0.08

SHIELD_DURATION_MS: Final[int] = 6500
SLOW_TIME_DURATION_MS: Final[int] = 5000
SCORE_MULTIPLIER_DURATION_MS: Final[int] = 7000

SLOW_TIME_SPEED_MULTIPLIER: Final[float] = 0.65
SCORE_MULTIPLIER_VALUE: Final[int] = 2


# ============================================================
# VISUAL EFFECTS
# ============================================================

MAX_PARTICLES: Final[int] = 650
MAX_TRAIL_POINTS: Final[int] = 120

ENABLE_SCREEN_SHAKE: Final[bool] = True
ENABLE_GLOW_EFFECTS: Final[bool] = True
ENABLE_PARTICLES: Final[bool] = True
ENABLE_MOTION_BLUR: Final[bool] = False

CRASH_SHAKE_STRENGTH: Final[float] = 18.0
CRASH_SHAKE_DURATION_MS: Final[int] = 550

SPEED_LINE_COUNT: Final[int] = 85
SPEED_LINE_MIN_SPEED: Final[float] = 30.0

DISTANCE_FOG_START: Final[float] = 105.0
DISTANCE_FOG_END: Final[float] = 170.0

BACKGROUND_STAR_COUNT: Final[int] = 150
BACKGROUND_PLANET_COUNT: Final[int] = 2


# ============================================================
# COLOURS
# ============================================================

BLACK: Final[tuple[int, int, int]] = (
    2,
    4,
    12,
)

SPACE_BLACK: Final[tuple[int, int, int]] = (
    4,
    7,
    18,
)

DEEP_BLUE: Final[tuple[int, int, int]] = (
    8,
    19,
    44,
)

DARK_BLUE: Final[tuple[int, int, int]] = (
    16,
    39,
    82,
)

PANEL_BLUE: Final[tuple[int, int, int]] = (
    20,
    51,
    102,
)

BLUE: Final[tuple[int, int, int]] = (
    50,
    125,
    245,
)

LIGHT_BLUE: Final[tuple[int, int, int]] = (
    115,
    205,
    255,
)

CYAN: Final[tuple[int, int, int]] = (
    90,
    245,
    255,
)

WHITE: Final[tuple[int, int, int]] = (
    245,
    250,
    255,
)

LIGHT_GREY: Final[tuple[int, int, int]] = (
    195,
    208,
    230,
)

GREY: Final[tuple[int, int, int]] = (
    120,
    140,
    175,
)

DARK_GREY: Final[tuple[int, int, int]] = (
    47,
    58,
    84,
)

GREEN: Final[tuple[int, int, int]] = (
    65,
    225,
    130,
)

YELLOW: Final[tuple[int, int, int]] = (
    255,
    220,
    70,
)

ORANGE: Final[tuple[int, int, int]] = (
    255,
    135,
    55,
)

RED: Final[tuple[int, int, int]] = (
    240,
    60,
    80,
)

PURPLE: Final[tuple[int, int, int]] = (
    165,
    85,
    245,
)

PINK: Final[tuple[int, int, int]] = (
    255,
    80,
    190,
)

CYLINDER_BASE_COLOUR: Final[tuple[int, int, int]] = (
    21,
    40,
    80,
)

CYLINDER_DARK_COLOUR: Final[tuple[int, int, int]] = (
    9,
    18,
    42,
)

CYLINDER_LANE_COLOUR: Final[tuple[int, int, int]] = (
    58,
    185,
    255,
)

CYLINDER_RING_COLOUR: Final[tuple[int, int, int]] = (
    44,
    100,
    180,
)

CYLINDER_GLOW_COLOUR: Final[tuple[int, int, int]] = (
    75,
    225,
    255,
)

PLAYER_COLOUR: Final[tuple[int, int, int]] = (
    75,
    215,
    255,
)

PLAYER_HIGHLIGHT_COLOUR: Final[tuple[int, int, int]] = (
    225,
    250,
    255,
)

PLAYER_TRAIL_COLOUR: Final[tuple[int, int, int]] = (
    75,
    145,
    255,
)


# ============================================================
# UI
# ============================================================

UI_PANEL_ALPHA: Final[int] = 235

BUTTON_WIDTH: Final[int] = 330
BUTTON_HEIGHT: Final[int] = 66

BUTTON_CORNER_RADIUS: Final[int] = 14
PANEL_CORNER_RADIUS: Final[int] = 18

TITLE_FONT_SIZE: Final[int] = 82
HEADING_FONT_SIZE: Final[int] = 44
NORMAL_FONT_SIZE: Final[int] = 28
SMALL_FONT_SIZE: Final[int] = 21
TINY_FONT_SIZE: Final[int] = 17

VERSION_FONT_SIZE: Final[int] = 18

VERSION_MARGIN_RIGHT: Final[int] = 18
VERSION_MARGIN_BOTTOM: Final[int] = 15

HUD_DISTANCE_POSITION: Final[tuple[int, int]] = (
    28,
    24,
)

HUD_SPEED_POSITION: Final[tuple[int, int]] = (
    28,
    64,
)

HUD_LEVEL_POSITION: Final[tuple[int, int]] = (
    GAME_WIDTH - 28,
    24,
)

SHOW_VERSION_ON_MAIN_MENU: Final[bool] = True
SHOW_VERSION_ON_PAUSE_MENU: Final[bool] = True


# ============================================================
# AUDIO
# ============================================================

MASTER_VOLUME_DEFAULT: Final[float] = 0.80
MUSIC_VOLUME_DEFAULT: Final[float] = 0.55
SOUND_VOLUME_DEFAULT: Final[float] = 0.85

ALLOW_MUSIC: Final[bool] = True
ALLOW_SOUND_EFFECTS: Final[bool] = True

MENU_MUSIC_FILE: Final[str] = "menu_theme.ogg"
GAMEPLAY_MUSIC_FILE: Final[str] = "gameplay_theme.ogg"
EXTREME_MUSIC_FILE: Final[str] = "extreme_theme.ogg"

BUTTON_SOUND_FILE: Final[str] = "button_click.wav"
CRASH_SOUND_FILE: Final[str] = "crash.wav"
LEVEL_COMPLETE_SOUND_FILE: Final[str] = "level_complete.wav"
POWERUP_SOUND_FILE: Final[str] = "powerup.wav"


# ============================================================
# CONTROLS
# ============================================================

CONTROL_ROTATE_LEFT: Final[tuple[str, ...]] = (
    "a",
    "left",
)

CONTROL_ROTATE_RIGHT: Final[tuple[str, ...]] = (
    "d",
    "right",
)

CONTROL_PAUSE: Final[tuple[str, ...]] = (
    "escape",
    "p",
)

CONTROL_FULLSCREEN: Final[tuple[str, ...]] = (
    "f11",
    "alt+enter",
)

CONTROL_CONFIRM: Final[tuple[str, ...]] = (
    "enter",
    "space",
)


# ============================================================
# SAVE DATA DEFAULTS
# ============================================================

DEFAULT_SAVE_DATA: Final[dict[str, object]] = {
    "save_version": 1,

    "highest_unlocked_level": (
        FIRST_UNLOCKED_LEVEL
    ),

    "completed_levels": [],

    "level_best_times": {},
    "level_best_scores": {},

    "endless_best_distance": 0,

    "total_distance": 0,
    "total_runs": 0,
    "total_crashes": 0,

    "powerups_collected": 0,
    "perfect_levels": 0,

    "achievements": [],

    "selected_player_skin": "default",
    "unlocked_player_skins": [
        "default",
    ],

    "selected_cylinder_theme": "neon_blue",
    "unlocked_cylinder_themes": [
        "neon_blue",
    ],
}


DEFAULT_SETTINGS_DATA: Final[
    dict[str, object]
] = {
    "fullscreen": START_FULLSCREEN,

    "master_volume": MASTER_VOLUME_DEFAULT,
    "music_volume": MUSIC_VOLUME_DEFAULT,
    "sound_volume": SOUND_VOLUME_DEFAULT,

    "music_enabled": ALLOW_MUSIC,
    "sound_enabled": ALLOW_SOUND_EFFECTS,

    "screen_shake_enabled": ENABLE_SCREEN_SHAKE,
    "particles_enabled": ENABLE_PARTICLES,
    "glow_enabled": ENABLE_GLOW_EFFECTS,

    "show_fps": False,

    "control_left": "a",
    "control_right": "d",
}


# ============================================================
# ACHIEVEMENTS
# ============================================================

ACHIEVEMENT_FIRST_RUN: Final[str] = "first_run"
ACHIEVEMENT_FIRST_LEVEL: Final[str] = "first_level"
ACHIEVEMENT_LEVEL_10: Final[str] = "level_10"
ACHIEVEMENT_LEVEL_25: Final[str] = "level_25"
ACHIEVEMENT_LEVEL_50: Final[str] = "level_50"

ACHIEVEMENT_1000_METRES: Final[str] = "1000_metres"
ACHIEVEMENT_5000_METRES: Final[str] = "5000_metres"
ACHIEVEMENT_10000_METRES: Final[str] = "10000_metres"

ACHIEVEMENT_SPEED_DEMON: Final[str] = "speed_demon"
ACHIEVEMENT_PERFECT_RUN: Final[str] = "perfect_run"

ACHIEVEMENT_DEFINITIONS: Final[
    dict[str, dict[str, object]]
] = {
    ACHIEVEMENT_FIRST_RUN: {
        "name": "First Rotation",
        "description": "Start your first run.",
        "hidden": False,
    },

    ACHIEVEMENT_FIRST_LEVEL: {
        "name": "Getting Started",
        "description": "Complete Level 1.",
        "hidden": False,
    },

    ACHIEVEMENT_LEVEL_10: {
        "name": "Picking Up Speed",
        "description": "Complete Level 10.",
        "hidden": False,
    },

    ACHIEVEMENT_LEVEL_25: {
        "name": "Halfway Around",
        "description": "Complete Level 25.",
        "hidden": False,
    },

    ACHIEVEMENT_LEVEL_50: {
        "name": "Orbit Master",
        "description": "Complete Level 50.",
        "hidden": False,
    },

    ACHIEVEMENT_1000_METRES: {
        "name": "Long Distance",
        "description": (
            "Run at least 1,000 metres "
            "in Endless Mode."
        ),
        "hidden": False,
    },

    ACHIEVEMENT_5000_METRES: {
        "name": "Endurance Runner",
        "description": (
            "Run at least 5,000 metres "
            "in Endless Mode."
        ),
        "hidden": False,
    },

    ACHIEVEMENT_10000_METRES: {
        "name": "Beyond the Horizon",
        "description": (
            "Run at least 10,000 metres "
            "in Endless Mode."
        ),
        "hidden": True,
    },

    ACHIEVEMENT_SPEED_DEMON: {
        "name": "Speed Demon",
        "description": "Reach maximum running speed.",
        "hidden": False,
    },

    ACHIEVEMENT_PERFECT_RUN: {
        "name": "Untouchable",
        "description": (
            "Complete a difficult level "
            "without using a power-up."
        ),
        "hidden": False,
    },
}


# ============================================================
# WEBSITE ACCOUNT SETTINGS
# ============================================================

REQUIRE_WEBSITE_ACCOUNT: Final[bool] = True
ALLOW_DESKTOP_GUEST_MODE: Final[bool] = False

ACCOUNT_REQUIRED_MESSAGE: Final[str] = (
    "Sign in on Matthew's Games before "
    "opening Orbit Rush."
)

ACCOUNT_LOADING_MESSAGE: Final[str] = (
    "Checking your Matthew's Games account..."
)


# ============================================================
# ONLINE LEADERBOARD SETTINGS
# ============================================================

SUPABASE_PROJECT_URL: Final[str] = (
    "https://bcarxudxfmsibvnteoaj.supabase.co"
)

SUPABASE_PUBLISHABLE_KEY: Final[str] = (
    "sb_publishable_"
    "S7ki2S3tODs4shwWovSY6w_-2jknXXg"
)

SUPABASE_SCORES_TABLE: Final[str] = "scores"

ONLINE_LEADERBOARD_ENABLED: Final[bool] = True
ONLINE_LEADERBOARD_REQUIRES_ACCOUNT: Final[bool] = True

LEADERBOARD_DISTANCE_FIELD: Final[str] = "score"
LEADERBOARD_DISPLAY_UNIT: Final[str] = "m"

LEADERBOARD_ORDER_FIELDS: Final[
    tuple[str, ...]
] = (
    "score",
    "created_at",
)


# ============================================================
# VALIDATION HELPERS
# ============================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Keep a numeric value inside a range.
    """

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def normalize_angle(
    angle: float,
) -> float:
    """
    Normalize an angle to the range 0 <= angle < 360.
    """

    return (
        angle
        % CYLINDER_FULL_ROTATION
    )


def shortest_angle_difference(
    first_angle: float,
    second_angle: float,
) -> float:
    """
    Return the shortest signed angular difference.
    """

    difference = (
        second_angle
        - first_angle
        + 180.0
    ) % 360.0 - 180.0

    return difference


def lane_to_angle(
    lane_index: int,
) -> float:
    """
    Convert a cylinder lane index to its central angle.
    """

    normalized_lane = (
        lane_index
        % CYLINDER_LANE_COUNT
    )

    return normalize_angle(
        normalized_lane
        * CYLINDER_LANE_ANGLE
    )


def angle_to_lane(
    angle: float,
) -> int:
    """
    Convert an angle to the nearest cylinder lane.
    """

    normalized = normalize_angle(
        angle
    )

    lane = round(
        normalized
        / CYLINDER_LANE_ANGLE
    )

    return (
        lane
        % CYLINDER_LANE_COUNT
    )


def get_level_tier(
    level_number: int,
) -> LevelTier:
    """
    Return the difficulty tier containing a level.
    """

    cleaned_level = int(
        clamp(
            level_number,
            1,
            TOTAL_LEVELS,
        )
    )

    for tier in LEVEL_TIERS:
        if (
            tier.first_level
            <= cleaned_level
            <= tier.last_level
        ):
            return tier

    return LEVEL_TIERS[-1]


def get_level_progress(
    level_number: int,
) -> float:
    """
    Return campaign progress from 0.0 to 1.0.
    """

    cleaned_level = clamp(
        level_number,
        1,
        TOTAL_LEVELS,
    )

    if TOTAL_LEVELS <= 1:
        return 1.0

    return (
        cleaned_level - 1
    ) / (
        TOTAL_LEVELS - 1
    )


def calculate_level_length(
    level_number: int,
) -> float:
    """
    Calculate a level's intended distance.

    Later levels become considerably longer.
    """

    progress = get_level_progress(
        level_number
    )

    curved_progress = (
        progress
        ** 1.38
    )

    return (
        LEVEL_MINIMUM_LENGTH
        + (
            LEVEL_MAXIMUM_LENGTH
            - LEVEL_MINIMUM_LENGTH
        )
        * curved_progress
    )


def calculate_level_speed(
    level_number: int,
) -> float:
    """
    Calculate the opening speed for a campaign level.
    """

    tier = get_level_tier(
        level_number
    )

    tier_size = max(
        1,
        tier.last_level
        - tier.first_level,
    )

    tier_progress = (
        level_number
        - tier.first_level
    ) / tier_size

    return (
        tier.starting_speed
        + (
            tier.maximum_speed
            - tier.starting_speed
        )
        * clamp(
            tier_progress,
            0.0,
            1.0,
        )
    )


def calculate_endless_difficulty(
    distance_metres: float,
) -> float:
    """
    Return Endless Mode difficulty from distance.
    """

    difficulty = (
        ENDLESS_STARTING_DIFFICULTY
        + (
            distance_metres
            / 100.0
        )
        * ENDLESS_DIFFICULTY_PER_100_METRES
    )

    return clamp(
        difficulty,
        ENDLESS_STARTING_DIFFICULTY,
        ENDLESS_MAX_DIFFICULTY,
    )


def calculate_endless_speed(
    distance_metres: float,
) -> float:
    """
    Calculate forward speed in Endless Mode.
    """

    speed = (
        ENDLESS_STARTING_SPEED
        + (
            distance_metres
            / 100.0
        )
        * ENDLESS_SPEED_GAIN_PER_100_METRES
    )

    return clamp(
        speed,
        ENDLESS_STARTING_SPEED,
        ENDLESS_MAX_SPEED,
    )


def calculate_endless_gap(
    distance_metres: float,
) -> float:
    """
    Calculate obstacle spacing in Endless Mode.
    """

    gap = (
        ENDLESS_STARTING_OBSTACLE_GAP
        - (
            distance_metres
            / 100.0
        )
        * ENDLESS_GAP_REDUCTION_PER_100_METRES
    )

    return clamp(
        gap,
        ENDLESS_MINIMUM_OBSTACLE_GAP,
        ENDLESS_STARTING_OBSTACLE_GAP,
    )


def format_distance(
    distance_metres: float,
) -> str:
    """
    Format a distance for the HUD and leaderboard.
    """

    cleaned_distance = max(
        0.0,
        float(distance_metres),
    )

    if DISTANCE_DECIMAL_PLACES <= 0:
        return (
            f"{round(cleaned_distance):,} m"
        )

    return (
        f"{cleaned_distance:,.{DISTANCE_DECIMAL_PLACES}f} m"
    )


def format_version() -> str:
    """
    Return the visible version label.
    """

    return (
        f"Version {GAME_VERSION}"
    )


def ensure_project_directories() -> None:
    """
    Create save and asset directories when missing.
    """

    for directory in (
        ASSETS_DIRECTORY,
        IMAGES_DIRECTORY,
        SOUNDS_DIRECTORY,
        FONTS_DIRECTORY,
        SAVE_DIRECTORY,
    ):
        try:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        except OSError:
            pass