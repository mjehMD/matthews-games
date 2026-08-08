from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


# ============================================================
# TUNNEL RUNNER
# VERSION 0.1.0
# ============================================================
#
# This is the main configuration file for the entire game.
#
# The goal of Tunnel Runner is to create a fast 3D tunnel game
# inspired by the feel of Tunnel Rush:
#
# - First-person 3D camera
# - Player moves around the inside of a tunnel
# - A / D or Left / Right controls
# - Geometric obstacles rush toward the camera
# - Rotating walls, bars, crosses, wedges and openings
# - 50 campaign levels
# - Endless Mode
# - Endless leaderboard measured in metres
# - Website account integration
# - Browser / Pygbag support
# - Fullscreen support
# - Version number shown in the menu
#
# Every future file will use these exact names.
#
# ============================================================


# ============================================================
# GAME IDENTITY
# ============================================================

GAME_TITLE: Final[str] = "Tunnel Runner"

GAME_SLUG: Final[str] = "tunnel-runner"

GAME_VERSION: Final[str] = "0.1.0"

WINDOW_TITLE: Final[str] = (
    f"{GAME_TITLE} - Version {GAME_VERSION}"
)

WEBSITE_NAME: Final[str] = "Matthew's Games"


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIRECTORY: Final[Path] = (
    Path(__file__).resolve().parent
)

ASSETS_DIRECTORY: Final[Path] = (
    PROJECT_DIRECTORY
    / "assets"
)

SOUNDS_DIRECTORY: Final[Path] = (
    ASSETS_DIRECTORY
    / "sounds"
)

IMAGES_DIRECTORY: Final[Path] = (
    ASSETS_DIRECTORY
    / "images"
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

STATISTICS_FILE: Final[Path] = (
    SAVE_DIRECTORY
    / "statistics.json"
)


# ============================================================
# DISPLAY
# ============================================================

GAME_WIDTH: Final[int] = 1280
GAME_HEIGHT: Final[int] = 720

GAME_CENTER_X: Final[int] = (
    GAME_WIDTH
    // 2
)

GAME_CENTER_Y: Final[int] = (
    GAME_HEIGHT
    // 2
)

FPS: Final[int] = 60

START_FULLSCREEN: Final[bool] = False

ALLOW_FULLSCREEN: Final[bool] = True

ALLOW_RESIZING: Final[bool] = True

USE_SMOOTH_SCALING: Final[bool] = True

MIN_WINDOW_WIDTH: Final[int] = 640
MIN_WINDOW_HEIGHT: Final[int] = 360

BACKGROUND_COLOUR: Final[
    tuple[int, int, int]
] = (
    2,
    3,
    9,
)

LETTERBOX_COLOUR: Final[
    tuple[int, int, int]
] = (
    0,
    0,
    0,
)


# ============================================================
# GAME STATES
# ============================================================

STATE_LOADING: Final[str] = "loading"

STATE_SIGN_IN_REQUIRED: Final[str] = (
    "sign_in_required"
)

STATE_MAIN_MENU: Final[str] = (
    "main_menu"
)

STATE_LEVEL_SELECT: Final[str] = (
    "level_select"
)

STATE_PLAYING: Final[str] = (
    "playing"
)

STATE_PAUSED: Final[str] = (
    "paused"
)

STATE_GAME_OVER: Final[str] = (
    "game_over"
)

STATE_LEVEL_COMPLETE: Final[str] = (
    "level_complete"
)

STATE_LEADERBOARD: Final[str] = (
    "leaderboard"
)

STATE_SETTINGS: Final[str] = (
    "settings"
)

STATE_HELP: Final[str] = (
    "help"
)

STATE_STATISTICS: Final[str] = (
    "statistics"
)

STATE_ACHIEVEMENTS: Final[str] = (
    "achievements"
)


# ============================================================
# GAME MODES
# ============================================================

MODE_LEVELS: Final[str] = "levels"

MODE_ENDLESS: Final[str] = "endless"


# ============================================================
# COLOURS
# ============================================================

BLACK: Final[
    tuple[int, int, int]
] = (
    0,
    0,
    0,
)

WHITE: Final[
    tuple[int, int, int]
] = (
    245,
    250,
    255,
)

GREY: Final[
    tuple[int, int, int]
] = (
    120,
    130,
    150,
)

LIGHT_GREY: Final[
    tuple[int, int, int]
] = (
    195,
    205,
    225,
)

DARK_GREY: Final[
    tuple[int, int, int]
] = (
    42,
    48,
    64,
)

RED: Final[
    tuple[int, int, int]
] = (
    255,
    55,
    70,
)

ORANGE: Final[
    tuple[int, int, int]
] = (
    255,
    135,
    45,
)

YELLOW: Final[
    tuple[int, int, int]
] = (
    255,
    225,
    60,
)

GREEN: Final[
    tuple[int, int, int]
] = (
    70,
    235,
    135,
)

CYAN: Final[
    tuple[int, int, int]
] = (
    80,
    235,
    255,
)

BLUE: Final[
    tuple[int, int, int]
] = (
    60,
    120,
    255,
)

LIGHT_BLUE: Final[
    tuple[int, int, int]
] = (
    125,
    205,
    255,
)

PURPLE: Final[
    tuple[int, int, int]
] = (
    170,
    80,
    255,
)

PINK: Final[
    tuple[int, int, int]
] = (
    255,
    80,
    195,
)


# ============================================================
# 3D CAMERA
# ============================================================
#
# geometry.py will use a proper perspective camera.
#
# World axes:
#
# X = horizontal
# Y = vertical
# Z = forward
#
# The player camera moves automatically along +Z.
#
# ============================================================

CAMERA_FOV_DEGREES: Final[float] = 82.0

CAMERA_NEAR_CLIP: Final[float] = 0.15

CAMERA_FAR_CLIP: Final[float] = 260.0

CAMERA_HEIGHT: Final[float] = 0.0

CAMERA_FORWARD_SPEED_MULTIPLIER: Final[
    float
] = 1.0

CAMERA_SHAKE_ENABLED: Final[bool] = True

CAMERA_SHAKE_AMOUNT: Final[float] = 0.16

CAMERA_SHAKE_DURATION: Final[float] = 0.45


# ============================================================
# TUNNEL GEOMETRY
# ============================================================

TUNNEL_RADIUS: Final[float] = 8.0

TUNNEL_SEGMENTS: Final[int] = 20

TUNNEL_VISIBLE_LENGTH: Final[float] = 180.0

TUNNEL_RING_SPACING: Final[float] = 6.0

TUNNEL_SECTION_LENGTH: Final[float] = 6.0

TUNNEL_WALL_THICKNESS: Final[float] = 0.35

TUNNEL_ROTATION_SPEED: Final[float] = 0.0

TUNNEL_ALLOW_CURVES: Final[bool] = True

TUNNEL_CURVE_STRENGTH: Final[float] = 2.0

TUNNEL_CURVE_SPEED: Final[float] = 0.75

TUNNEL_ALLOW_COLOUR_CHANGES: Final[
    bool
] = True


# ============================================================
# PLAYER MOVEMENT
# ============================================================
#
# The player is not shown as a ship.
#
# The player has an angle around the tunnel wall.
#
# ============================================================

PLAYER_START_ANGLE: Final[float] = 0.0

PLAYER_MAX_ROTATION_SPEED: Final[float] = 190.0

PLAYER_ROTATION_ACCELERATION: Final[
    float
] = 950.0

PLAYER_ROTATION_DECELERATION: Final[
    float
] = 1100.0

PLAYER_ROTATION_SMOOTHING: Final[
    float
] = 10.0

PLAYER_COLLISION_ANGLE: Final[float] = 12.0

PLAYER_COLLISION_RADIUS: Final[float] = (
    TUNNEL_RADIUS
    - 0.35
)

PLAYER_LIVES: Final[int] = 1


# ============================================================
# CONTROLS
# ============================================================

CONTROL_LEFT_KEYS: Final[
    tuple[str, ...]
] = (
    "a",
    "left",
)

CONTROL_RIGHT_KEYS: Final[
    tuple[str, ...]
] = (
    "d",
    "right",
)

PAUSE_KEYS: Final[
    tuple[str, ...]
] = (
    "escape",
    "p",
)

FULLSCREEN_KEY: Final[str] = "f11"

RESTART_KEY: Final[str] = "r"


# ============================================================
# CAMPAIGN
# ============================================================

TOTAL_LEVELS: Final[int] = 50

FIRST_UNLOCKED_LEVEL: Final[int] = 1

LEVEL_BASE_LENGTH: Final[float] = 360.0

LEVEL_LENGTH_INCREASE: Final[float] = 18.0

LEVEL_50_LENGTH: Final[float] = 1500.0

LEVEL_START_COUNTDOWN: Final[int] = 3

LEVEL_COMPLETE_DELAY_MS: Final[int] = 700

CRASH_DELAY_MS: Final[int] = 500


# ============================================================
# CAMPAIGN SPEED
# ============================================================

CAMPAIGN_BASE_SPEED: Final[float] = 28.0

CAMPAIGN_MAX_SPEED: Final[float] = 68.0

LEVEL_SPEED_GAIN: Final[float] = 0.55

LEVEL_MAX_SPEED_GAIN: Final[float] = 0.75


# ============================================================
# ENDLESS MODE
# ============================================================

ENDLESS_START_SPEED: Final[float] = 30.0

ENDLESS_MAX_SPEED: Final[float] = 72.0

ENDLESS_SPEED_GAIN_PER_100M: Final[
    float
] = 0.70

ENDLESS_GENERATE_AHEAD: Final[float] = 220.0

ENDLESS_REMOVE_BEHIND: Final[float] = 20.0

ENDLESS_MIN_OBSTACLE_GAP: Final[float] = 10.0

ENDLESS_START_OBSTACLE_GAP: Final[
    float
] = 32.0

ENDLESS_GAP_REDUCTION_PER_100M: Final[
    float
] = 0.35

ENDLESS_MAX_OBJECTS: Final[int] = 80

ENDLESS_LEADERBOARD_MAX_DISTANCE: Final[
    int
] = 100_000_000


# ============================================================
# OBSTACLE IDS
# ============================================================

OBSTACLE_WALL: Final[str] = "wall"

OBSTACLE_GAP_WALL: Final[str] = (
    "gap_wall"
)

OBSTACLE_ROTATING_BAR: Final[str] = (
    "rotating_bar"
)

OBSTACLE_DOUBLE_BAR: Final[str] = (
    "double_bar"
)

OBSTACLE_CROSS: Final[str] = "cross"

OBSTACLE_SPINNER: Final[str] = "spinner"

OBSTACLE_TRIANGLE: Final[str] = (
    "triangle"
)

OBSTACLE_DOUBLE_TRIANGLE: Final[str] = (
    "double_triangle"
)

OBSTACLE_WEDGE: Final[str] = "wedge"

OBSTACLE_ROTATING_WEDGE: Final[str] = (
    "rotating_wedge"
)

OBSTACLE_SLIDING_WALL: Final[str] = (
    "sliding_wall"
)

OBSTACLE_CLOSING_WALL: Final[str] = (
    "closing_wall"
)

OBSTACLE_DIAMOND: Final[str] = "diamond"

OBSTACLE_BLADE: Final[str] = "blade"

OBSTACLE_DOUBLE_BLADE: Final[str] = (
    "double_blade"
)

OBSTACLE_TRIPLE_BLADE: Final[str] = (
    "triple_blade"
)

OBSTACLE_ROTATING_CROSS: Final[str] = (
    "rotating_cross"
)

OBSTACLE_RING_GAP: Final[str] = (
    "ring_gap"
)

OBSTACLE_MOVING_GAP: Final[str] = (
    "moving_gap"
)

OBSTACLE_FINISH: Final[str] = "finish"


ALL_OBSTACLE_TYPES: Final[
    tuple[str, ...]
] = (
    OBSTACLE_WALL,
    OBSTACLE_GAP_WALL,
    OBSTACLE_ROTATING_BAR,
    OBSTACLE_DOUBLE_BAR,
    OBSTACLE_CROSS,
    OBSTACLE_SPINNER,
    OBSTACLE_TRIANGLE,
    OBSTACLE_DOUBLE_TRIANGLE,
    OBSTACLE_WEDGE,
    OBSTACLE_ROTATING_WEDGE,
    OBSTACLE_SLIDING_WALL,
    OBSTACLE_CLOSING_WALL,
    OBSTACLE_DIAMOND,
    OBSTACLE_BLADE,
    OBSTACLE_DOUBLE_BLADE,
    OBSTACLE_TRIPLE_BLADE,
    OBSTACLE_ROTATING_CROSS,
    OBSTACLE_RING_GAP,
    OBSTACLE_MOVING_GAP,
    OBSTACLE_FINISH,
)


# ============================================================
# OBSTACLE SETTINGS
# ============================================================

OBSTACLE_COLLISION_DISTANCE: Final[
    float
] = 1.2

OBSTACLE_NEAR_VISIBLE_DISTANCE: Final[
    float
] = 0.5

OBSTACLE_FAR_VISIBLE_DISTANCE: Final[
    float
] = TUNNEL_VISIBLE_LENGTH

OBSTACLE_DEFAULT_THICKNESS: Final[
    float
] = 0.85

OBSTACLE_ROTATION_MIN_SPEED: Final[
    float
] = 30.0

OBSTACLE_ROTATION_MAX_SPEED: Final[
    float
] = 130.0

OBSTACLE_MIN_SAFE_ANGLE: Final[
    float
] = 26.0

OBSTACLE_MAX_SAFE_ANGLE: Final[
    float
] = 110.0


# ============================================================
# LEVEL DIFFICULTY TIERS
# ============================================================

@dataclass(frozen=True)
class DifficultyTier:
    name: str

    first_level: int
    last_level: int

    speed_multiplier: float

    obstacle_density: float

    rotating_chance: float

    moving_chance: float

    minimum_safe_angle: float

    colour_theme: str


DIFFICULTY_TIERS: Final[
    tuple[
        DifficultyTier,
        ...,
    ]
] = (
    DifficultyTier(
        name="Beginner",
        first_level=1,
        last_level=5,
        speed_multiplier=0.82,
        obstacle_density=0.65,
        rotating_chance=0.00,
        moving_chance=0.00,
        minimum_safe_angle=90.0,
        colour_theme="blue",
    ),

    DifficultyTier(
        name="Easy",
        first_level=6,
        last_level=10,
        speed_multiplier=0.90,
        obstacle_density=0.80,
        rotating_chance=0.05,
        moving_chance=0.02,
        minimum_safe_angle=78.0,
        colour_theme="cyan",
    ),

    DifficultyTier(
        name="Medium",
        first_level=11,
        last_level=20,
        speed_multiplier=1.00,
        obstacle_density=0.95,
        rotating_chance=0.15,
        moving_chance=0.08,
        minimum_safe_angle=66.0,
        colour_theme="purple",
    ),

    DifficultyTier(
        name="Hard",
        first_level=21,
        last_level=30,
        speed_multiplier=1.08,
        obstacle_density=1.12,
        rotating_chance=0.25,
        moving_chance=0.15,
        minimum_safe_angle=54.0,
        colour_theme="orange",
    ),

    DifficultyTier(
        name="Extreme",
        first_level=31,
        last_level=40,
        speed_multiplier=1.16,
        obstacle_density=1.28,
        rotating_chance=0.38,
        moving_chance=0.24,
        minimum_safe_angle=42.0,
        colour_theme="red",
    ),

    DifficultyTier(
        name="Insane",
        first_level=41,
        last_level=49,
        speed_multiplier=1.26,
        obstacle_density=1.45,
        rotating_chance=0.52,
        moving_chance=0.35,
        minimum_safe_angle=32.0,
        colour_theme="white",
    ),

    DifficultyTier(
        name="Final",
        first_level=50,
        last_level=50,
        speed_multiplier=1.34,
        obstacle_density=1.60,
        rotating_chance=0.68,
        moving_chance=0.45,
        minimum_safe_angle=26.0,
        colour_theme="final",
    ),
)


# ============================================================
# VISUAL THEMES
# ============================================================

@dataclass(frozen=True)
class TunnelTheme:
    name: str

    background: tuple[int, int, int]

    tunnel_primary: tuple[int, int, int]

    tunnel_secondary: tuple[int, int, int]

    tunnel_lines: tuple[int, int, int]

    obstacle_primary: tuple[int, int, int]

    obstacle_secondary: tuple[int, int, int]

    glow: tuple[int, int, int]


TUNNEL_THEMES: Final[
    dict[
        str,
        TunnelTheme,
    ]
] = {
    "blue": TunnelTheme(
        name="Blue Core",

        background=(
            2,
            4,
            12,
        ),

        tunnel_primary=(
            15,
            38,
            92,
        ),

        tunnel_secondary=(
            35,
            90,
            180,
        ),

        tunnel_lines=(
            90,
            180,
            255,
        ),

        obstacle_primary=RED,

        obstacle_secondary=ORANGE,

        glow=CYAN,
    ),

    "cyan": TunnelTheme(
        name="Cyan Pulse",

        background=(
            1,
            8,
            12,
        ),

        tunnel_primary=(
            10,
            55,
            65,
        ),

        tunnel_secondary=(
            20,
            135,
            145,
        ),

        tunnel_lines=CYAN,

        obstacle_primary=PURPLE,

        obstacle_secondary=PINK,

        glow=WHITE,
    ),

    "purple": TunnelTheme(
        name="Violet",

        background=(
            8,
            2,
            18,
        ),

        tunnel_primary=(
            45,
            15,
            80,
        ),

        tunnel_secondary=(
            120,
            45,
            185,
        ),

        tunnel_lines=PURPLE,

        obstacle_primary=CYAN,

        obstacle_secondary=LIGHT_BLUE,

        glow=PINK,
    ),

    "orange": TunnelTheme(
        name="Solar",

        background=(
            18,
            5,
            1,
        ),

        tunnel_primary=(
            75,
            28,
            5,
        ),

        tunnel_secondary=(
            180,
            75,
            10,
        ),

        tunnel_lines=ORANGE,

        obstacle_primary=CYAN,

        obstacle_secondary=WHITE,

        glow=YELLOW,
    ),

    "red": TunnelTheme(
        name="Reactor",

        background=(
            16,
            1,
            4,
        ),

        tunnel_primary=(
            72,
            8,
            18,
        ),

        tunnel_secondary=(
            170,
            20,
            40,
        ),

        tunnel_lines=RED,

        obstacle_primary=YELLOW,

        obstacle_secondary=WHITE,

        glow=ORANGE,
    ),

    "white": TunnelTheme(
        name="Void",

        background=(
            3,
            3,
            6,
        ),

        tunnel_primary=(
            28,
            30,
            40,
        ),

        tunnel_secondary=(
            105,
            112,
            135,
        ),

        tunnel_lines=WHITE,

        obstacle_primary=RED,

        obstacle_secondary=CYAN,

        glow=WHITE,
    ),

    "final": TunnelTheme(
        name="Final Core",

        background=BLACK,

        tunnel_primary=(
            30,
            30,
            30,
        ),

        tunnel_secondary=(
            125,
            125,
            125,
        ),

        tunnel_lines=WHITE,

        obstacle_primary=RED,

        obstacle_secondary=YELLOW,

        glow=CYAN,
    ),
}


# ============================================================
# VISUAL EFFECTS
# ============================================================

ENABLE_SPEED_LINES: Final[bool] = True

ENABLE_PARTICLES: Final[bool] = True

ENABLE_SCREEN_FLASH: Final[bool] = True

ENABLE_GLOW: Final[bool] = True

ENABLE_DEPTH_FOG: Final[bool] = True

MAX_PARTICLES: Final[int] = 350

CRASH_PARTICLE_COUNT: Final[int] = 65

SPEED_LINE_COUNT: Final[int] = 65

SPEED_LINE_START_SPEED: Final[float] = 36.0

CRASH_FLASH_DURATION_MS: Final[int] = 220


# ============================================================
# USER INTERFACE
# ============================================================

TITLE_FONT_SIZE: Final[int] = 84

LARGE_FONT_SIZE: Final[int] = 58

HEADING_FONT_SIZE: Final[int] = 42

NORMAL_FONT_SIZE: Final[int] = 30

SMALL_FONT_SIZE: Final[int] = 22

TINY_FONT_SIZE: Final[int] = 17

VERSION_FONT_SIZE: Final[int] = 18

BUTTON_WIDTH: Final[int] = 340

BUTTON_HEIGHT: Final[int] = 64

BUTTON_CORNER_RADIUS: Final[int] = 12

PANEL_CORNER_RADIUS: Final[int] = 16

PANEL_ALPHA: Final[int] = 225


# ============================================================
# LEVEL SELECT
# ============================================================

LEVELS_PER_PAGE: Final[int] = 10

LEVEL_COLUMNS: Final[int] = 5

LEVEL_ROWS: Final[int] = 2

LEVEL_BUTTON_WIDTH: Final[int] = 170

LEVEL_BUTTON_HEIGHT: Final[int] = 100

LEVEL_BUTTON_GAP_X: Final[int] = 30

LEVEL_BUTTON_GAP_Y: Final[int] = 52


# ============================================================
# HUD
# ============================================================

HUD_MARGIN: Final[int] = 18

HUD_WIDTH: Final[int] = 280

HUD_HEIGHT: Final[int] = 105

SHOW_SPEED: Final[bool] = True

SHOW_DISTANCE: Final[bool] = True

SHOW_LEVEL: Final[bool] = True


# ============================================================
# ACCOUNT INTEGRATION
# ============================================================

REQUIRE_WEBSITE_ACCOUNT: Final[bool] = True

ALLOW_DESKTOP_TEST_ACCOUNT: Final[bool] = True

DESKTOP_TEST_USERNAME: Final[str] = (
    "DesktopTester"
)


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_PROJECT_URL: Final[str] = (
    "https://bcarxudxfmsibvnteoaj.supabase.co"
)

SUPABASE_PUBLISHABLE_KEY: Final[str] = (
    "sb_publishable_"
    "S7ki2S3tODs4shwWovSY6w_-2jknXXg"
)

SUPABASE_SCORES_TABLE: Final[str] = (
    "scores"
)

SUPABASE_PROFILES_TABLE: Final[str] = (
    "profiles"
)

LEADERBOARD_GAME_NAME: Final[str] = (
    GAME_SLUG
)

MAX_LEADERBOARD_ENTRIES: Final[int] = 10


# ============================================================
# DEFAULT SAVE DATA
# ============================================================

DEFAULT_SAVE_DATA: Final[
    dict[
        str,
        object,
    ]
] = {
    "save_version": 1,

    "highest_unlocked_level": 1,

    "completed_levels": [],

    "level_best_times": {},

    "level_attempts": {},

    "endless_best_distance": 0,

    "total_runs": 0,

    "total_crashes": 0,

    "total_distance": 0,

    "achievements": [],
}


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS_DATA: Final[
    dict[
        str,
        object,
    ]
] = {
    "fullscreen": START_FULLSCREEN,

    "screen_shake": True,

    "particles": True,

    "speed_lines": True,

    "glow": True,

    "show_fps": False,

    "master_volume": 0.8,

    "music_volume": 0.5,

    "sfx_volume": 0.85,

    "music_enabled": True,

    "sfx_enabled": True,
}


# ============================================================
# DEFAULT STATISTICS
# ============================================================

DEFAULT_STATISTICS_DATA: Final[
    dict[
        str,
        object,
    ]
] = {
    "total_runs": 0,

    "campaign_runs": 0,

    "endless_runs": 0,

    "total_crashes": 0,

    "levels_completed": 0,

    "total_distance": 0,

    "total_play_time_seconds": 0,

    "maximum_speed": 0.0,

    "longest_endless_run": 0,
}


# ============================================================
# ACHIEVEMENTS
# ============================================================

ACHIEVEMENT_DEFINITIONS: Final[
    dict[
        str,
        dict[
            str,
            object,
        ],
    ]
] = {
    "first_run": {
        "name": "Into the Tunnel",

        "description": (
            "Start your first run."
        ),

        "hidden": False,
    },

    "first_level": {
        "name": "First Escape",

        "description": (
            "Complete Level 1."
        ),

        "hidden": False,
    },

    "level_10": {
        "name": "Getting Faster",

        "description": (
            "Complete Level 10."
        ),

        "hidden": False,
    },

    "level_25": {
        "name": "Halfway",

        "description": (
            "Complete Level 25."
        ),

        "hidden": False,
    },

    "level_50": {
        "name": "Tunnel Master",

        "description": (
            "Complete Level 50."
        ),

        "hidden": False,
    },

    "endless_500": {
        "name": "500 Metres",

        "description": (
            "Run 500 metres in Endless Mode."
        ),

        "hidden": False,
    },

    "endless_1000": {
        "name": "One Kilometre",

        "description": (
            "Run 1,000 metres in Endless Mode."
        ),

        "hidden": False,
    },

    "endless_2500": {
        "name": "Tunnel Survivor",

        "description": (
            "Run 2,500 metres in Endless Mode."
        ),

        "hidden": False,
    },

    "endless_5000": {
        "name": "Endurance",

        "description": (
            "Run 5,000 metres in Endless Mode."
        ),

        "hidden": False,
    },

    "endless_10000": {
        "name": "Beyond the Tunnel",

        "description": (
            "Run 10,000 metres in Endless Mode."
        ),

        "hidden": True,
    },
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
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
    return (
        float(
            angle
        )
        % 360.0
    )


def shortest_angle_difference(
    first_angle: float,
    second_angle: float,
) -> float:
    return (
        (
            second_angle
            - first_angle
            + 180.0
        )
        % 360.0
        - 180.0
    )


def get_difficulty_tier(
    level_number: int,
) -> DifficultyTier:
    level_number = int(
        clamp(
            level_number,
            1,
            TOTAL_LEVELS,
        )
    )

    for tier in DIFFICULTY_TIERS:
        if (
            tier.first_level
            <= level_number
            <= tier.last_level
        ):
            return tier

    return DIFFICULTY_TIERS[-1]


def get_theme(
    theme_name: str,
) -> TunnelTheme:
    return TUNNEL_THEMES.get(
        theme_name,
        TUNNEL_THEMES[
            "blue"
        ],
    )


def calculate_level_length(
    level_number: int,
) -> float:
    level_number = int(
        clamp(
            level_number,
            1,
            TOTAL_LEVELS,
        )
    )

    progress = (
        level_number - 1
    ) / max(
        1,
        TOTAL_LEVELS - 1,
    )

    progress = (
        progress
        ** 1.20
    )

    return (
        LEVEL_BASE_LENGTH
        + (
            LEVEL_50_LENGTH
            - LEVEL_BASE_LENGTH
        )
        * progress
    )


def calculate_level_speed(
    level_number: int,
) -> float:
    level_number = int(
        clamp(
            level_number,
            1,
            TOTAL_LEVELS,
        )
    )

    tier = get_difficulty_tier(
        level_number
    )

    speed = (
        CAMPAIGN_BASE_SPEED
        + (
            level_number - 1
        )
        * LEVEL_SPEED_GAIN
    )

    speed *= (
        tier.speed_multiplier
    )

    return clamp(
        speed,
        CAMPAIGN_BASE_SPEED
        * 0.75,
        CAMPAIGN_MAX_SPEED,
    )


def calculate_endless_speed(
    distance: float,
) -> float:
    speed = (
        ENDLESS_START_SPEED
        + (
            max(
                0.0,
                distance,
            )
            / 100.0
        )
        * ENDLESS_SPEED_GAIN_PER_100M
    )

    return clamp(
        speed,
        ENDLESS_START_SPEED,
        ENDLESS_MAX_SPEED,
    )


def calculate_endless_gap(
    distance: float,
) -> float:
    gap = (
        ENDLESS_START_OBSTACLE_GAP
        - (
            max(
                0.0,
                distance,
            )
            / 100.0
        )
        * ENDLESS_GAP_REDUCTION_PER_100M
    )

    return clamp(
        gap,
        ENDLESS_MIN_OBSTACLE_GAP,
        ENDLESS_START_OBSTACLE_GAP,
    )


def format_distance(
    distance: float,
) -> str:
    return (
        f"{max(0, round(distance)):,} m"
    )


def format_version(
) -> str:
    return (
        f"Version {GAME_VERSION}"
    )


def ensure_directories(
) -> None:
    directories = (
        ASSETS_DIRECTORY,
        SOUNDS_DIRECTORY,
        IMAGES_DIRECTORY,
        SAVE_DIRECTORY,
    )

    for directory in directories:
        try:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        except OSError:
            pass


# ============================================================
# CONFIG VALIDATION
# ============================================================

def validate_config(
) -> None:
    if TOTAL_LEVELS != 50:
        raise ValueError(
            "Tunnel Runner must have exactly 50 levels."
        )

    if GAME_WIDTH <= 0:
        raise ValueError(
            "GAME_WIDTH must be positive."
        )

    if GAME_HEIGHT <= 0:
        raise ValueError(
            "GAME_HEIGHT must be positive."
        )

    if TUNNEL_RADIUS <= 0:
        raise ValueError(
            "TUNNEL_RADIUS must be positive."
        )

    if TUNNEL_SEGMENTS < 8:
        raise ValueError(
            "TUNNEL_SEGMENTS is too low."
        )

    if (
        CAMERA_NEAR_CLIP
        >= CAMERA_FAR_CLIP
    ):
        raise ValueError(
            "Camera clipping range is invalid."
        )

    if (
        ENDLESS_MAX_SPEED
        <= ENDLESS_START_SPEED
    ):
        raise ValueError(
            "Endless max speed must be greater than start speed."
        )

    if (
        CAMPAIGN_MAX_SPEED
        <= CAMPAIGN_BASE_SPEED
    ):
        raise ValueError(
            "Campaign max speed must be greater than base speed."
        )

    for obstacle_type in (
        ALL_OBSTACLE_TYPES
    ):
        if not obstacle_type:
            raise ValueError(
                "Invalid obstacle type."
            )


ensure_directories()
validate_config()