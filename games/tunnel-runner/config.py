from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


# ============================================================
# TUNNEL RUNNER
# CONFIG
# VERSION 0.2.0
# ============================================================


# ============================================================
# PROJECT
# ============================================================

GAME_TITLE: Final[str] = "Tunnel Runner"

GAME_VERSION: Final[str] = "0.2.0"

WINDOW_TITLE: Final[str] = (
    f"{GAME_TITLE} - v{GAME_VERSION}"
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR: Final[Path] = (
    Path(__file__).resolve().parent
)

SAVE_DIR: Final[Path] = (
    PROJECT_DIR
    / "saves"
)

SAVE_FILE: Final[Path] = (
    SAVE_DIR
    / "tunnel_runner_save.json"
)

SETTINGS_FILE: Final[Path] = (
    SAVE_DIR
    / "tunnel_runner_settings.json"
)


def ensure_project_directories() -> None:
    try:
        SAVE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError:
        pass


ensure_project_directories()


# ============================================================
# SCREEN
# ============================================================

GAME_WIDTH: Final[int] = 1280

GAME_HEIGHT: Final[int] = 720

GAME_CENTER_X: Final[int] = (
    GAME_WIDTH // 2
)

GAME_CENTER_Y: Final[int] = (
    GAME_HEIGHT // 2
)

FPS: Final[int] = 60

START_FULLSCREEN: Final[bool] = False

ALLOW_FULLSCREEN: Final[bool] = True

ALLOW_RESIZING: Final[bool] = True

# Compatibility alias.
ALLOW_WINDOW_RESIZE: Final[bool] = (
    ALLOW_RESIZING
)

USE_SMOOTH_SCALING: Final[bool] = False


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_PROJECT_URL: Final[str] = (
    "https://bcarxudxfmsibvnteoaj.supabase.co"
)

SUPABASE_PUBLISHABLE_KEY: Final[str] = (
    "sb_publishable_S7ki2S3tODs4shwWovSY6w_-2jknXXg"
)

SUPABASE_SCORES_TABLE: Final[str] = (
    "scores"
)

# IMPORTANT:
# New scores are saved under Tunnel Runner.
#
# online_leaderboard.py also loads legacy orbit-runner scores.

LEADERBOARD_GAME_NAME: Final[str] = (
    "tunnel-runner"
)

MAX_LEADERBOARD_ENTRIES: Final[int] = 10

ENDLESS_LEADERBOARD_MAX_DISTANCE: Final[int] = (
    100_000_000
)


# ============================================================
# COLOURS
# ============================================================

BLACK: Final[tuple[int, int, int]] = (
    0,
    0,
    0,
)

WHITE: Final[tuple[int, int, int]] = (
    245,
    250,
    255,
)

GREY: Final[tuple[int, int, int]] = (
    105,
    115,
    135,
)

DARK_GREY: Final[tuple[int, int, int]] = (
    38,
    45,
    60,
)

LIGHT_GREY: Final[tuple[int, int, int]] = (
    175,
    188,
    210,
)

RED: Final[tuple[int, int, int]] = (
    255,
    60,
    80,
)

ORANGE: Final[tuple[int, int, int]] = (
    255,
    145,
    45,
)

YELLOW: Final[tuple[int, int, int]] = (
    255,
    225,
    65,
)

GREEN: Final[tuple[int, int, int]] = (
    75,
    235,
    130,
)

CYAN: Final[tuple[int, int, int]] = (
    40,
    225,
    255,
)

LIGHT_BLUE: Final[tuple[int, int, int]] = (
    95,
    175,
    255,
)

BLUE: Final[tuple[int, int, int]] = (
    50,
    100,
    255,
)

DARK_BLUE: Final[tuple[int, int, int]] = (
    18,
    35,
    75,
)

DEEP_BLUE: Final[tuple[int, int, int]] = (
    5,
    13,
    35,
)

PURPLE: Final[tuple[int, int, int]] = (
    175,
    75,
    255,
)

PINK: Final[tuple[int, int, int]] = (
    255,
    65,
    190,
)

SPACE_BLACK: Final[tuple[int, int, int]] = (
    2,
    4,
    12,
)

DEEP_SPACE: Final[tuple[int, int, int]] = (
    3,
    7,
    20,
)

BACKGROUND_COLOUR: Final[
    tuple[int, int, int]
] = (
    3,
    7,
    20,
)

LETTERBOX_COLOUR: Final[
    tuple[int, int, int]
] = BLACK


# ============================================================
# FONTS
# ============================================================

TITLE_FONT_SIZE: Final[int] = 82

LARGE_FONT_SIZE: Final[int] = 58

HEADING_FONT_SIZE: Final[int] = 42

NORMAL_FONT_SIZE: Final[int] = 30

SMALL_FONT_SIZE: Final[int] = 22

TINY_FONT_SIZE: Final[int] = 17

VERSION_FONT_SIZE: Final[int] = 17


# ============================================================
# BUTTONS
# ============================================================

BUTTON_WIDTH: Final[int] = 360

BUTTON_HEIGHT: Final[int] = 64

BUTTON_CORNER_RADIUS: Final[int] = 13


# ============================================================
# PANELS / HUD
# ============================================================

PANEL_ALPHA: Final[int] = 210

PANEL_CORNER_RADIUS: Final[int] = 14

UI_PANEL_ALPHA: Final[int] = PANEL_ALPHA

HUD_MARGIN: Final[int] = 20

HUD_WIDTH: Final[int] = 245

HUD_HEIGHT: Final[int] = 105

# Compatibility names.

HUD_PANEL_WIDTH: Final[int] = HUD_WIDTH

HUD_PANEL_HEIGHT: Final[int] = HUD_HEIGHT


# ============================================================
# VERSION DISPLAY
# ============================================================

SHOW_VERSION_ON_MAIN_MENU: Final[bool] = True

SHOW_VERSION_ON_PAUSE: Final[bool] = False

VERSION_MARGIN_RIGHT: Final[int] = 18

VERSION_MARGIN_BOTTOM: Final[int] = 18


# ============================================================
# MODES
# ============================================================

MODE_LEVELS: Final[str] = "levels"

MODE_ENDLESS: Final[str] = "endless"


# ============================================================
# GAME STATES
# ============================================================

STATE_LOADING: Final[str] = "loading"

STATE_SIGN_IN_REQUIRED: Final[str] = (
    "sign_in_required"
)

STATE_MAIN_MENU: Final[str] = "main_menu"

STATE_LEVEL_SELECT: Final[str] = (
    "level_select"
)

STATE_PLAYING: Final[str] = "playing"

STATE_PAUSED: Final[str] = "paused"

STATE_GAME_OVER: Final[str] = "game_over"

STATE_LEVEL_COMPLETE: Final[str] = (
    "level_complete"
)

STATE_LEADERBOARD: Final[str] = (
    "leaderboard"
)

STATE_SETTINGS: Final[str] = "settings"

STATE_HELP: Final[str] = "help"

STATE_STATISTICS: Final[str] = "statistics"

STATE_ACHIEVEMENTS: Final[str] = (
    "achievements"
)

# Compatibility aliases from older builds.

STATE_ACCOUNT_LOADING: Final[str] = (
    STATE_LOADING
)

STATE_ACCOUNT_REQUIRED: Final[str] = (
    STATE_SIGN_IN_REQUIRED
)

STATE_MODE_SELECT: Final[str] = (
    STATE_MAIN_MENU
)


# ============================================================
# DISPLAY OPTIONS
# ============================================================

SHOW_DISTANCE: Final[bool] = True

SHOW_SPEED: Final[bool] = True

SHOW_LEVEL: Final[bool] = True


# ============================================================
# PLAYER
# ============================================================

PLAYER_START_ANGLE: Final[float] = 0.0

# Compatibility alias.

PLAYER_STARTING_ANGLE: Final[float] = (
    PLAYER_START_ANGLE
)

# ------------------------------------------------------------
# Rotation
# ------------------------------------------------------------
#
# Fairly quick movement is important because the game itself
# now travels much faster.
#

PLAYER_MAX_ROTATION_SPEED: Final[float] = (
    255.0
)

PLAYER_ROTATION_SPEED: Final[float] = (
    PLAYER_MAX_ROTATION_SPEED
)

PLAYER_ROTATION_ACCELERATION: Final[float] = (
    900.0
)

PLAYER_ROTATION_DECELERATION: Final[float] = (
    1100.0
)

# Collision size around player's angle.

PLAYER_COLLISION_ANGLE: Final[float] = 6.0


# ============================================================
# TUNNEL
# ============================================================

TUNNEL_RADIUS: Final[float] = 11.5

# Number of visual sides before main.py performance limiting.

TUNNEL_SEGMENTS: Final[int] = 12

TUNNEL_SECTION_LENGTH: Final[float] = 9.0

# main.py reduces this again for actual rendering.

TUNNEL_VISIBLE_LENGTH: Final[float] = 260.0

TUNNEL_LANE_COUNT: Final[int] = 12


# ============================================================
# LEVEL SYSTEM
# ============================================================

TOTAL_LEVELS: Final[int] = 50

FIRST_UNLOCKED_LEVEL: Final[int] = 1


# ============================================================
# GAME SPEED
# ============================================================
#
# This is the global forward-speed multiplier.
#
# 1.00 = original
# 1.20 = quicker
# 1.30 = fast
# 1.40 = very fast
#
# 1.30 is a good balance with the faster rotation controls.
#

GAME_SPEED_MULTIPLIER: Final[float] = 1.30


# ============================================================
# CAMPAIGN SPEED
# ============================================================

LEVEL_1_START_SPEED: Final[float] = 33.0

LEVEL_START_SPEED_INCREASE: Final[float] = 0.55

LEVEL_MAX_SPEED_BONUS: Final[float] = 14.0

LEVEL_MAX_SPEED_INCREASE: Final[float] = 0.65

LEVEL_1_LENGTH: Final[float] = 420.0

LEVEL_LENGTH_INCREASE: Final[float] = 20.0


def calculate_level_length(
    level_number: int,
) -> float:

    level_number = max(
        1,
        int(
            level_number
        ),
    )

    return (
        LEVEL_1_LENGTH
        + (
            level_number
            - 1
        )
        * LEVEL_LENGTH_INCREASE
    )


def calculate_level_start_speed(
    level_number: int,
) -> float:

    level_number = max(
        1,
        int(
            level_number
        ),
    )

    speed = (
        LEVEL_1_START_SPEED
        + (
            level_number
            - 1
        )
        * LEVEL_START_SPEED_INCREASE
    )

    return (
        speed
        * GAME_SPEED_MULTIPLIER
    )


def calculate_level_max_speed(
    level_number: int,
) -> float:

    level_number = max(
        1,
        int(
            level_number
        ),
    )

    base = (
        calculate_level_start_speed(
            level_number
        )
    )

    bonus = (
        LEVEL_MAX_SPEED_BONUS
        + (
            level_number
            - 1
        )
        * LEVEL_MAX_SPEED_INCREASE
    )

    return (
        base
        + bonus
    )


# ============================================================
# ENDLESS SPEED
# ============================================================

ENDLESS_START_SPEED: Final[float] = 38.0

ENDLESS_SPEED_PER_1000M: Final[float] = 5.0

ENDLESS_MAX_SPEED: Final[float] = 115.0


def calculate_endless_speed(
    distance: float,
) -> float:

    distance = max(
        0.0,
        float(
            distance
        ),
    )

    speed = (
        ENDLESS_START_SPEED
        + (
            distance
            / 1000.0
        )
        * ENDLESS_SPEED_PER_1000M
    )

    speed *= (
        GAME_SPEED_MULTIPLIER
    )

    return clamp(
        speed,
        0.0,
        ENDLESS_MAX_SPEED,
    )


# ============================================================
# ENDLESS DIFFICULTY
# ============================================================

ENDLESS_MAX_DIFFICULTY: Final[float] = 10.0

ENDLESS_SAFE_START_DISTANCE: Final[float] = 90.0

ENDLESS_GENERATE_AHEAD_DISTANCE: Final[float] = (
    600.0
)

# Compatibility alias.

ENDLESS_GENERATION_AHEAD_DISTANCE: Final[
    float
] = (
    ENDLESS_GENERATE_AHEAD_DISTANCE
)

ENDLESS_MAX_ACTIVE_OBSTACLES: Final[int] = 80

ENDLESS_MAX_GENERATION_PER_FRAME: Final[int] = 4

ENDLESS_REMOVE_BEHIND_DISTANCE: Final[float] = (
    30.0
)

ENDLESS_SAFE_LANE_MAX_CHANGE: Final[float] = (
    95.0
)

ENDLESS_MAX_HARD_PATTERNS_IN_ROW: Final[int] = 3

ENDLESS_EASY_RECOVERY_SECTION_CHANCE: Final[
    float
] = 0.18


def calculate_endless_difficulty(
    distance: float,
) -> float:

    distance = max(
        0.0,
        float(
            distance
        ),
    )

    difficulty = (
        distance
        / 850.0
    )

    return clamp(
        difficulty,
        0.0,
        ENDLESS_MAX_DIFFICULTY,
    )


def calculate_endless_gap(
    distance: float,
) -> float:

    difficulty = (
        calculate_endless_difficulty(
            distance
        )
    )

    return clamp(
        105.0
        - difficulty
        * 4.5,
        55.0,
        105.0,
    )


# ============================================================
# DIFFICULTY TIERS
# ============================================================

def get_difficulty_tier(
    level_number: int,
) -> str:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(
                level_number
            ),
        ),
    )

    if level_number <= 5:
        return "Beginner"

    if level_number <= 10:
        return "Easy"

    if level_number <= 20:
        return "Medium"

    if level_number <= 30:
        return "Hard"

    if level_number <= 40:
        return "Extreme"

    return "Impossible"


# ============================================================
# OBSTACLE TYPES
# ============================================================

OBSTACLE_WALL: Final[str] = "wall"

OBSTACLE_GAP_WALL: Final[str] = (
    "gap_wall"
)

OBSTACLE_RING_GAP: Final[str] = (
    "ring_gap"
)

OBSTACLE_SLIDING_WALL: Final[str] = (
    "sliding_wall"
)

OBSTACLE_MOVING_GAP: Final[str] = (
    "moving_gap"
)

OBSTACLE_CLOSING_WALL: Final[str] = (
    "closing_wall"
)

OBSTACLE_ROTATING_BAR: Final[str] = (
    "rotating_bar"
)

OBSTACLE_DOUBLE_BAR: Final[str] = (
    "double_bar"
)

OBSTACLE_ROTATING_CROSS: Final[str] = (
    "rotating_cross"
)

OBSTACLE_SPINNER: Final[str] = (
    "spinner"
)

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

OBSTACLE_DIAMOND: Final[str] = (
    "diamond"
)

OBSTACLE_BLADE: Final[str] = "blade"

OBSTACLE_DOUBLE_BLADE: Final[str] = (
    "double_blade"
)

OBSTACLE_TRIPLE_BLADE: Final[str] = (
    "triple_blade"
)

OBSTACLE_FINISH: Final[str] = (
    "finish"
)


# ============================================================
# COLLISION
# ============================================================

OBSTACLE_COLLISION_DISTANCE: Final[float] = (
    1.25
)


# ============================================================
# CAMERA / EFFECTS
# ============================================================

CAMERA_SHAKE_AMOUNT: Final[float] = 0.35

CAMERA_SHAKE_DURATION: Final[float] = 0.28


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_SETTINGS: Final[dict[str, object]] = {
    "fullscreen": False,
    "screen_shake": True,
    "particles": True,
    "speed_lines": True,
    "glow": True,
    "show_fps": False,
}

# Older storage versions used this name.

DEFAULT_SETTINGS_DATA: Final[
    dict[str, object]
] = dict(
    DEFAULT_SETTINGS
)


# ============================================================
# SAVE DATA
# ============================================================

DEFAULT_SAVE_DATA: Final[dict[str, object]] = {
    "highest_unlocked_level": (
        FIRST_UNLOCKED_LEVEL
    ),

    "completed_levels": [],

    "level_best_times": {},

    "endless_best_distance": 0,

    "statistics": {
        "total_runs": 0,
        "total_crashes": 0,
        "total_distance": 0.0,
        "total_play_time": 0.0,
        "maximum_speed": 0.0,
    },

    "achievements": [],
}


# ============================================================
# ACHIEVEMENTS
# ============================================================

ACHIEVEMENT_DEFINITIONS: Final[
    dict[str, dict[str, object]]
] = {

    "first_run": {
        "name": "First Run",
        "description": (
            "Start your first run."
        ),
        "hidden": False,
    },

    "first_level": {
        "name": "Tunnel Rookie",
        "description": (
            "Complete your first level."
        ),
        "hidden": False,
    },

    "level_5": {
        "name": "Getting Faster",
        "description": (
            "Complete Level 5."
        ),
        "hidden": False,
    },

    "level_10": {
        "name": "Tunnel Racer",
        "description": (
            "Complete Level 10."
        ),
        "hidden": False,
    },

    "level_20": {
        "name": "Outside World",
        "description": (
            "Reach Level 20."
        ),
        "hidden": False,
    },

    "level_30": {
        "name": "Expert Runner",
        "description": (
            "Complete Level 30."
        ),
        "hidden": False,
    },

    "level_40": {
        "name": "Tunnel Master",
        "description": (
            "Complete Level 40."
        ),
        "hidden": False,
    },

    "level_50": {
        "name": "Tunnel Legend",
        "description": (
            "Complete all 50 levels."
        ),
        "hidden": False,
    },

    "endless_500": {
        "name": "500 Metres",
        "description": (
            "Run 500 metres in Endless."
        ),
        "hidden": False,
    },

    "endless_1000": {
        "name": "Breaking Out",
        "description": (
            "Run 1,000 metres in Endless."
        ),
        "hidden": False,
    },

    "endless_2500": {
        "name": "Long Distance",
        "description": (
            "Run 2,500 metres in Endless."
        ),
        "hidden": False,
    },

    "endless_5000": {
        "name": "Speed Demon",
        "description": (
            "Run 5,000 metres in Endless."
        ),
        "hidden": False,
    },

    "endless_10000": {
        "name": "Unstoppable",
        "description": (
            "Run 10,000 metres in Endless."
        ),
        "hidden": True,
    },
}


# ============================================================
# THEMES
# ============================================================

@dataclass(
    frozen=True
)
class TunnelTheme:
    name: str

    background: tuple[
        int,
        int,
        int,
    ]

    tunnel_primary: tuple[
        int,
        int,
        int,
    ]

    tunnel_secondary: tuple[
        int,
        int,
        int,
    ]

    tunnel_lines: tuple[
        int,
        int,
        int,
    ]

    glow: tuple[
        int,
        int,
        int,
    ]


THEMES: Final[
    dict[str, TunnelTheme]
] = {

    "blue": TunnelTheme(
        name="blue",

        background=(
            2,
            7,
            22,
        ),

        tunnel_primary=(
            25,
            85,
            225,
        ),

        tunnel_secondary=(
            7,
            28,
            100,
        ),

        tunnel_lines=(
            70,
            180,
            255,
        ),

        glow=(
            65,
            210,
            255,
        ),
    ),

    "electric_blue": TunnelTheme(
        name="electric_blue",

        background=(
            2,
            9,
            28,
        ),

        tunnel_primary=(
            35,
            120,
            255,
        ),

        tunnel_secondary=(
            10,
            42,
            120,
        ),

        tunnel_lines=(
            100,
            220,
            255,
        ),

        glow=(
            80,
            230,
            255,
        ),
    ),

    "cyan": TunnelTheme(
        name="cyan",

        background=(
            1,
            18,
            25,
        ),

        tunnel_primary=(
            20,
            210,
            225,
        ),

        tunnel_secondary=(
            4,
            75,
            90,
        ),

        tunnel_lines=(
            100,
            255,
            255,
        ),

        glow=(
            75,
            255,
            245,
        ),
    ),

    "purple": TunnelTheme(
        name="purple",

        background=(
            12,
            2,
            28,
        ),

        tunnel_primary=(
            155,
            40,
            245,
        ),

        tunnel_secondary=(
            58,
            10,
            105,
        ),

        tunnel_lines=(
            220,
            100,
            255,
        ),

        glow=(
            215,
            75,
            255,
        ),
    ),

    "orange": TunnelTheme(
        name="orange",

        background=(
            28,
            8,
            2,
        ),

        tunnel_primary=(
            245,
            105,
            28,
        ),

        tunnel_secondary=(
            100,
            32,
            5,
        ),

        tunnel_lines=(
            255,
            190,
            65,
        ),

        glow=(
            255,
            160,
            45,
        ),
    ),

    "red": TunnelTheme(
        name="red",

        background=(
            27,
            2,
            7,
        ),

        tunnel_primary=(
            225,
            35,
            65,
        ),

        tunnel_secondary=(
            95,
            8,
            25,
        ),

        tunnel_lines=(
            255,
            110,
            125,
        ),

        glow=(
            255,
            70,
            90,
        ),
    ),

    "pink": TunnelTheme(
        name="pink",

        background=(
            25,
            2,
            25,
        ),

        tunnel_primary=(
            245,
            45,
            190,
        ),

        tunnel_secondary=(
            95,
            12,
            80,
        ),

        tunnel_lines=(
            255,
            120,
            225,
        ),

        glow=(
            255,
            70,
            215,
        ),
    ),

    "white": TunnelTheme(
        name="white",

        background=(
            8,
            10,
            15,
        ),

        tunnel_primary=(
            210,
            225,
            245,
        ),

        tunnel_secondary=(
            70,
            90,
            120,
        ),

        tunnel_lines=(
            255,
            255,
            255,
        ),

        glow=(
            190,
            230,
            255,
        ),
    ),
}


def get_theme(
    theme_name: str,
) -> TunnelTheme:

    cleaned = str(
        theme_name
    ).strip().lower()

    return THEMES.get(
        cleaned,
        THEMES[
            "blue"
        ],
    )


# ============================================================
# UI POSITION COMPATIBILITY
# ============================================================

MAIN_MENU_TITLE_Y: Final[int] = 90

MAIN_MENU_USERNAME_Y: Final[int] = 160

MAIN_MENU_DESCRIPTION_Y: Final[int] = 215

LEVELS_BUTTON_Y: Final[int] = 310

PERSONAL_BEST_Y: Final[int] = 380

LEADERBOARD_BUTTON_Y: Final[int] = 490

HELP_BUTTON_Y: Final[int] = (
    GAME_HEIGHT
    - 65
)

LEVELS_PER_PAGE: Final[int] = 10

LEVEL_COLUMNS: Final[int] = 5

LEVEL_BUTTON_WIDTH: Final[int] = 160

LEVEL_BUTTON_HEIGHT: Final[int] = 92

LEVEL_BUTTON_START_X: Final[int] = 150

LEVEL_BUTTON_START_Y: Final[int] = 255

LEVEL_BUTTON_HORIZONTAL_GAP: Final[int] = 40

LEVEL_BUTTON_VERTICAL_GAP: Final[int] = 68


# ============================================================
# OLD CYLINDER COMPATIBILITY CONSTANTS
# ============================================================

CYLINDER_CENTER_X: Final[int] = (
    GAME_CENTER_X
)

CYLINDER_HORIZON_Y: Final[int] = (
    GAME_CENTER_Y
)

CYLINDER_NEAR_RADIUS: Final[int] = 500

CYLINDER_FAR_RADIUS: Final[int] = 22

CYLINDER_PLAYER_Y: Final[int] = (
    GAME_HEIGHT
    - 110
)

CYLINDER_LANE_COUNT: Final[int] = (
    TUNNEL_LANE_COUNT
)

CYLINDER_RING_COUNT: Final[int] = 28

CYLINDER_RING_SPACING: Final[float] = 9.0

CYLINDER_BASE_COLOUR: Final[
    tuple[int, int, int]
] = BLUE

CYLINDER_DARK_COLOUR: Final[
    tuple[int, int, int]
] = DARK_BLUE

CYLINDER_GLOW_COLOUR: Final[
    tuple[int, int, int]
] = CYAN

CYLINDER_LANE_COLOUR: Final[
    tuple[int, int, int]
] = LIGHT_BLUE

CYLINDER_RING_COLOUR: Final[
    tuple[int, int, int]
] = DARK_GREY


# ============================================================
# OLD EFFECT COMPATIBILITY
# ============================================================

ENABLE_GLOW_EFFECTS: Final[bool] = True

BACKGROUND_STAR_COUNT: Final[int] = 90

PANEL_BLUE: Final[
    tuple[int, int, int]
] = (
    10,
    25,
    55,
)

HUD_DISTANCE_POSITION: Final[
    tuple[int, int]
] = (
    20,
    20,
)

HUD_SPEED_POSITION: Final[
    tuple[int, int]
] = (
    20,
    70,
)

HUD_LEVEL_POSITION: Final[
    tuple[int, int]
] = (
    GAME_WIDTH
    - 250,
    20,
)


# ============================================================
# ACCOUNT MESSAGES
# ============================================================

ACCOUNT_LOADING_MESSAGE: Final[str] = (
    "Checking your Matthew's Games account..."
)

ACCOUNT_REQUIRED_MESSAGE: Final[str] = (
    "Sign in on Matthew's Games to play Tunnel Runner."
)


# ============================================================
# GENERAL HELPERS
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


def lerp(
    start: float,
    end: float,
    amount: float,
) -> float:

    amount = clamp(
        amount,
        0.0,
        1.0,
    )

    return (
        start
        + (
            end
            - start
        )
        * amount
    )


def format_distance(
    value: float | int,
) -> str:

    try:
        distance = max(
            0,
            int(
                round(
                    float(
                        value
                    )
                )
            ),
        )

    except (
        TypeError,
        ValueError,
    ):
        distance = 0

    return (
        f"{distance:,} m"
    )


def format_version() -> str:

    return (
        f"Version {GAME_VERSION}"
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_config() -> None:

    if GAME_WIDTH <= 0:
        raise ValueError(
            "GAME_WIDTH must be positive."
        )

    if GAME_HEIGHT <= 0:
        raise ValueError(
            "GAME_HEIGHT must be positive."
        )

    if FPS < 60:
        raise ValueError(
            "Tunnel Runner should target at least 60 FPS."
        )

    if TOTAL_LEVELS != 50:
        raise ValueError(
            "Tunnel Runner must contain 50 levels."
        )

    if TUNNEL_RADIUS <= 0:
        raise ValueError(
            "TUNNEL_RADIUS must be positive."
        )

    if (
        PLAYER_MAX_ROTATION_SPEED
        <= 0
    ):
        raise ValueError(
            "Player rotation speed must be positive."
        )

    if (
        GAME_SPEED_MULTIPLIER
        <= 0
    ):
        raise ValueError(
            "GAME_SPEED_MULTIPLIER must be positive."
        )

    if not SUPABASE_PROJECT_URL:
        raise ValueError(
            "Missing Supabase URL."
        )

    if not SUPABASE_PUBLISHABLE_KEY:
        raise ValueError(
            "Missing Supabase publishable key."
        )

    if (
        LEADERBOARD_GAME_NAME
        != "tunnel-runner"
    ):
        raise ValueError(
            "Leaderboard game name must be tunnel-runner."
        )


validate_config()