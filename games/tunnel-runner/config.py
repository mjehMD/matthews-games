from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


# ============================================================
# TUNNEL RUNNER
# CONFIG
# VERSION 0.2.5
# FULL COMPATIBILITY BUILD
# ============================================================


# ============================================================
# BASIC HELPERS
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
        float(amount),
        0.0,
        1.0,
    )

    return (
        float(start)
        + (
            float(end)
            - float(start)
        )
        * amount
    )


def smoothstep(
    value: float,
) -> float:
    value = clamp(
        float(value),
        0.0,
        1.0,
    )

    return (
        value
        * value
        * (
            3.0
            - 2.0
            * value
        )
    )


# ============================================================
# GAME INFORMATION
# ============================================================

GAME_TITLE: Final[str] = "Tunnel Runner"

GAME_VERSION: Final[str] = "0.2.8"

WINDOW_TITLE: Final[str] = (
    f"{GAME_TITLE} - Version {GAME_VERSION}"
)


def format_version() -> str:
    return (
        f"Version {GAME_VERSION}"
    )


# ============================================================
# PATHS
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

STATISTICS_FILE: Final[Path] = (
    SAVE_DIR
    / "tunnel_runner_statistics.json"
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

TARGET_FPS: Final[int] = FPS

START_FULLSCREEN: Final[bool] = False

ALLOW_FULLSCREEN: Final[bool] = True

ALLOW_RESIZING: Final[bool] = True

ALLOW_WINDOW_RESIZE: Final[bool] = (
    ALLOW_RESIZING
)

USE_SMOOTH_SCALING: Final[bool] = False


# ============================================================
# SUPABASE / LEADERBOARD
# ============================================================

SUPABASE_PROJECT_URL: Final[str] = (
    "https://bcarxudxfmsibvnteoaj.supabase.co"
)

SUPABASE_PUBLISHABLE_KEY: Final[str] = (
    "sb_publishable_S7ki2S3tODs4shwWovSY6w_-2jknXXg"
)

SUPABASE_SCORES_TABLE: Final[str] = "scores"


SUPABASE_PROFILES_TABLE: Final[str] = "profiles"

REQUIRE_WEBSITE_ACCOUNT: Final[bool] = True

ALLOW_DESKTOP_TEST_ACCOUNT: Final[bool] = True

DESKTOP_TEST_USERNAME: Final[str] = "Desktop Tester"


LEADERBOARD_GAME_NAME: Final[str] = (
    "tunnel-runner"
)

LEGACY_LEADERBOARD_GAME_NAME: Final[str] = (
    "orbit-runner"
)

MAX_LEADERBOARD_ENTRIES: Final[int] = 10

ENDLESS_LEADERBOARD_MAX_DISTANCE: Final[int] = (
    100_000_000
)


# ============================================================
# COLOURS
# ============================================================

BLACK = (
    0,
    0,
    0,
)

WHITE = (
    245,
    250,
    255,
)

GREY = (
    105,
    115,
    135,
)

GRAY = GREY

DARK_GREY = (
    38,
    45,
    60,
)

DARK_GRAY = DARK_GREY

LIGHT_GREY = (
    175,
    188,
    210,
)

LIGHT_GRAY = LIGHT_GREY

RED = (
    255,
    60,
    80,
)

DARK_RED = (
    120,
    25,
    40,
)

ORANGE = (
    255,
    145,
    45,
)

YELLOW = (
    255,
    225,
    65,
)

GREEN = (
    75,
    235,
    130,
)

LIGHT_GREEN = (
    130,
    255,
    170,
)

DARK_GREEN = (
    30,
    120,
    70,
)

CYAN = (
    40,
    225,
    255,
)

LIGHT_BLUE = (
    95,
    175,
    255,
)

BLUE = (
    50,
    100,
    255,
)

MID_BLUE = (
    30,
    65,
    145,
)

DARK_BLUE = (
    18,
    35,
    75,
)

DEEP_BLUE = (
    5,
    13,
    35,
)

PURPLE = (
    175,
    75,
    255,
)

DARK_PURPLE = (
    75,
    30,
    120,
)

PINK = (
    255,
    65,
    190,
)

SPACE_BLACK = (
    2,
    4,
    12,
)

DEEP_SPACE = (
    3,
    7,
    20,
)

BACKGROUND_COLOUR = (
    3,
    7,
    20,
)

BACKGROUND_COLOR = (
    BACKGROUND_COLOUR
)

LETTERBOX_COLOUR = BLACK

LETTERBOX_COLOR = (
    LETTERBOX_COLOUR
)

PANEL_BLUE = (
    10,
    25,
    55,
)


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
# UI
# ============================================================

BUTTON_WIDTH: Final[int] = 360

BUTTON_HEIGHT: Final[int] = 64

BUTTON_CORNER_RADIUS: Final[int] = 13

PANEL_ALPHA: Final[int] = 210

PANEL_CORNER_RADIUS: Final[int] = 14

UI_PANEL_ALPHA: Final[int] = PANEL_ALPHA

HUD_MARGIN: Final[int] = 20

HUD_WIDTH: Final[int] = 245

HUD_HEIGHT: Final[int] = 105

HUD_PANEL_WIDTH: Final[int] = HUD_WIDTH

HUD_PANEL_HEIGHT: Final[int] = HUD_HEIGHT

SHOW_DISTANCE: Final[bool] = True

SHOW_SPEED: Final[bool] = True

SHOW_LEVEL: Final[bool] = True

SHOW_VERSION_ON_MAIN_MENU: Final[bool] = True

SHOW_VERSION_ON_PAUSE: Final[bool] = False

VERSION_MARGIN_RIGHT: Final[int] = 18

VERSION_MARGIN_BOTTOM: Final[int] = 18


# ============================================================
# OLD HUD POSITIONS
# ============================================================

HUD_DISTANCE_POSITION = (
    20,
    20,
)

HUD_SPEED_POSITION = (
    20,
    70,
)

HUD_LEVEL_POSITION = (
    GAME_WIDTH - 250,
    20,
)


# ============================================================
# MENU POSITIONS
# ============================================================

MAIN_MENU_TITLE_Y: Final[int] = 90

MAIN_MENU_USERNAME_Y: Final[int] = 160

MAIN_MENU_DESCRIPTION_Y: Final[int] = 215

LEVELS_BUTTON_Y: Final[int] = 310

PERSONAL_BEST_Y: Final[int] = 380

LEADERBOARD_BUTTON_Y: Final[int] = 490

HELP_BUTTON_Y: Final[int] = (
    GAME_HEIGHT - 65
)


# ============================================================
# LEVEL SELECT
# ============================================================

LEVELS_PER_PAGE: Final[int] = 10

LEVEL_COLUMNS: Final[int] = 5

LEVEL_BUTTON_WIDTH: Final[int] = 160

LEVEL_BUTTON_HEIGHT: Final[int] = 92

LEVEL_BUTTON_START_X: Final[int] = 150

LEVEL_BUTTON_START_Y: Final[int] = 255

LEVEL_BUTTON_HORIZONTAL_GAP: Final[int] = 40

LEVEL_BUTTON_VERTICAL_GAP: Final[int] = 68


# ============================================================
# MODES
# ============================================================

MODE_LEVELS: Final[str] = "levels"

MODE_ENDLESS: Final[str] = "endless"


# ============================================================
# STATES
# ============================================================

STATE_LOADING: Final[str] = "loading"

STATE_SIGN_IN_REQUIRED: Final[str] = (
    "sign_in_required"
)

STATE_MAIN_MENU: Final[str] = "main_menu"

STATE_LEVEL_SELECT: Final[str] = "level_select"

STATE_PLAYING: Final[str] = "playing"

STATE_PAUSED: Final[str] = "paused"

STATE_GAME_OVER: Final[str] = "game_over"

STATE_LEVEL_COMPLETE: Final[str] = (
    "level_complete"
)

STATE_LEADERBOARD: Final[str] = "leaderboard"

STATE_SETTINGS: Final[str] = "settings"

STATE_HELP: Final[str] = "help"

STATE_STATISTICS: Final[str] = "statistics"

STATE_ACHIEVEMENTS: Final[str] = "achievements"

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
# PLAYER
# ============================================================

PLAYER_START_ANGLE: Final[float] = 0.0

PLAYER_STARTING_ANGLE: Final[float] = (
    PLAYER_START_ANGLE
)

PLAYER_MAX_ROTATION_SPEED: Final[float] = (
    260.0
)

PLAYER_ROTATION_SPEED: Final[float] = (
    PLAYER_MAX_ROTATION_SPEED
)

PLAYER_ROTATION_ACCELERATION: Final[float] = (
    950.0
)

PLAYER_ROTATION_DECELERATION: Final[float] = (
    1150.0
)

PLAYER_INPUT_SMOOTHING: Final[float] = 0.18

PLAYER_COLLISION_ANGLE: Final[float] = 6.0


# ============================================================
# TUNNEL
# ============================================================

TUNNEL_RADIUS: Final[float] = 11.5

TUNNEL_SEGMENTS: Final[int] = 12

TUNNEL_SECTION_LENGTH: Final[float] = 9.0

TUNNEL_VISIBLE_LENGTH: Final[float] = 260.0

TUNNEL_VISIBLE_DISTANCE: Final[float] = (
    TUNNEL_VISIBLE_LENGTH
)

TUNNEL_LANE_COUNT: Final[int] = 12

TUNNEL_LANES: Final[int] = (
    TUNNEL_LANE_COUNT
)

TUNNEL_FULL_ROTATION: Final[float] = 360.0

TUNNEL_LANE_ANGLE: Final[float] = (
    TUNNEL_FULL_ROTATION
    / TUNNEL_LANE_COUNT
)


# ============================================================
# TUNNEL PERSPECTIVE
# ============================================================

TUNNEL_NEAR_RADIUS: Final[float] = 520.0

TUNNEL_FAR_RADIUS: Final[float] = 18.0

TUNNEL_RING_COUNT: Final[int] = 34

TUNNEL_PERSPECTIVE_POWER: Final[float] = 1.72

TUNNEL_WOBBLE_ENABLED: Final[bool] = True

TUNNEL_WOBBLE_AMOUNT: Final[float] = 4.0

TUNNEL_WOBBLE_SPEED: Final[float] = 0.0015


# ============================================================
# ANGLE HELPERS
# ============================================================

def normalize_angle(
    angle: float,
) -> float:
    return (
        float(angle)
        % 360.0
    )


def shortest_angle_difference(
    start_angle: float,
    end_angle: float,
) -> float:
    return (
        (
            float(end_angle)
            - float(start_angle)
            + 180.0
        )
        % 360.0
        - 180.0
    )


def angular_distance(
    first_angle: float,
    second_angle: float,
) -> float:
    return abs(
        shortest_angle_difference(
            first_angle,
            second_angle,
        )
    )


def lane_to_angle(
    lane: float,
) -> float:
    return normalize_angle(
        float(lane)
        * TUNNEL_LANE_ANGLE
    )


def angle_to_lane(
    angle: float,
) -> float:
    return (
        normalize_angle(
            angle
        )
        / TUNNEL_LANE_ANGLE
    )


def lane_width_to_degrees(
    width_lanes: float,
) -> float:
    return max(
        0.0,
        float(width_lanes)
        * TUNNEL_LANE_ANGLE,
    )


# ============================================================
# COLLISION
# ============================================================

OBSTACLE_COLLISION_DISTANCE: Final[float] = 1.25

COLLISION_ACTIVE_DISTANCE_MIN: Final[float] = -1.6

COLLISION_ACTIVE_DISTANCE_MAX: Final[float] = 2.2

COLLISION_GRACE_ANGLE: Final[float] = 2.5


# ============================================================
# EFFECTS / PERFORMANCE
# ============================================================

ENABLE_SCREEN_SHAKE: Final[bool] = True

ENABLE_PARTICLES: Final[bool] = True

ENABLE_SPEED_LINES: Final[bool] = True

ENABLE_TUNNEL_GLOW: Final[bool] = True

ENABLE_DISTANCE_FOG: Final[bool] = True

ENABLE_FLASH_EFFECT: Final[bool] = True

ENABLE_GLOW_EFFECTS: Final[bool] = True

MAX_PARTICLES: Final[int] = 160

CRASH_PARTICLE_COUNT: Final[int] = 28

CRASH_FLASH_DURATION_MS: Final[int] = 140

CRASH_SCREEN_SHAKE_STRENGTH: Final[float] = 8.0

CRASH_SCREEN_SHAKE_DURATION_MS: Final[int] = 300

CAMERA_SHAKE_AMOUNT: Final[float] = 0.35

CAMERA_SHAKE_DURATION: Final[float] = 0.28

SPEED_LINE_ACTIVATION_SPEED: Final[float] = 34.0

SPEED_LINE_COUNT: Final[int] = 14

BACKGROUND_STAR_COUNT: Final[int] = 90


# ============================================================
# CAMPAIGN
# ============================================================

TOTAL_LEVELS: Final[int] = 50

FIRST_UNLOCKED_LEVEL: Final[int] = 1

GAME_SPEED_MULTIPLIER: Final[float] = 1.20


# ============================================================
# CAMPAIGN SPEED
# ============================================================

CAMPAIGN_BASE_SPEED: Final[float] = 32.0

CAMPAIGN_START_SPEED: Final[float] = (
    CAMPAIGN_BASE_SPEED
)

CAMPAIGN_MIN_SPEED: Final[float] = (
    CAMPAIGN_BASE_SPEED
)

CAMPAIGN_MAX_SPEED: Final[float] = 95.0

CAMPAIGN_SPEED_PER_LEVEL: Final[float] = 0.52

CAMPAIGN_MAX_SPEED_BONUS: Final[float] = 16.0

CAMPAIGN_ACCELERATION_BASE: Final[float] = 0.0035

CAMPAIGN_ACCELERATION_PER_LEVEL: Final[float] = (
    0.000275
)

CAMPAIGN_SPEED_ACCELERATION: Final[float] = (
    CAMPAIGN_ACCELERATION_BASE
)

CAMPAIGN_LEVEL_1_LENGTH: Final[float] = 420.0

CAMPAIGN_LENGTH_PER_LEVEL: Final[float] = 20.0


# ============================================================
# OLD CAMPAIGN NAMES
# ============================================================

LEVEL_1_START_SPEED: Final[float] = (
    CAMPAIGN_BASE_SPEED
)

LEVEL_START_SPEED_INCREASE: Final[float] = (
    CAMPAIGN_SPEED_PER_LEVEL
)

LEVEL_MAX_SPEED_BONUS: Final[float] = (
    CAMPAIGN_MAX_SPEED_BONUS
)

LEVEL_MAX_SPEED_INCREASE: Final[float] = 0.65

LEVEL_1_LENGTH: Final[float] = (
    CAMPAIGN_LEVEL_1_LENGTH
)

LEVEL_LENGTH_INCREASE: Final[float] = (
    CAMPAIGN_LENGTH_PER_LEVEL
)


# ============================================================
# CAMPAIGN CALCULATIONS
# ============================================================

def calculate_level_length(
    level_number: int,
) -> float:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(level_number),
        ),
    )

    return float(
        CAMPAIGN_LEVEL_1_LENGTH
        + (
            level_number - 1
        )
        * CAMPAIGN_LENGTH_PER_LEVEL
    )


def calculate_level_start_speed(
    level_number: int,
) -> float:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(level_number),
        ),
    )

    speed = (
        CAMPAIGN_BASE_SPEED
        + (
            level_number - 1
        )
        * CAMPAIGN_SPEED_PER_LEVEL
    )

    speed *= GAME_SPEED_MULTIPLIER

    return float(
        clamp(
            speed,
            CAMPAIGN_BASE_SPEED,
            CAMPAIGN_MAX_SPEED,
        )
    )


def calculate_level_max_speed(
    level_number: int,
) -> float:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(level_number),
        ),
    )

    start_speed = (
        calculate_level_start_speed(
            level_number
        )
    )

    bonus = (
        CAMPAIGN_MAX_SPEED_BONUS
        + (
            level_number - 1
        )
        * LEVEL_MAX_SPEED_INCREASE
    )

    return float(
        clamp(
            start_speed + bonus,
            start_speed,
            CAMPAIGN_MAX_SPEED,
        )
    )


def calculate_level_acceleration(
    level_number: int,
) -> float:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(level_number),
        ),
    )

    progress = (
        (
            level_number - 1
        )
        / max(
            1,
            TOTAL_LEVELS - 1,
        )
    )

    return float(
        0.0035
        + progress
        * 0.0135
    )


def calculate_level_speed(
    level_number: int,
    distance: float = 0.0,
) -> float:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(level_number),
        ),
    )

    distance = max(
        0.0,
        float(distance),
    )

    starting_speed = float(
        calculate_level_start_speed(
            level_number
        )
    )

    maximum_speed = float(
        calculate_level_max_speed(
            level_number
        )
    )

    acceleration = float(
        calculate_level_acceleration(
            level_number
        )
    )

    speed = (
        starting_speed
        + distance
        * acceleration
    )

    return float(
        clamp(
            speed,
            starting_speed,
            maximum_speed,
        )
    )


# ============================================================
# THEME
# ============================================================

@dataclass(
    frozen=True
)
class TunnelTheme:

    name: str

    background_colour: tuple[
        int,
        int,
        int,
    ]

    tunnel_dark: tuple[
        int,
        int,
        int,
    ]

    tunnel_bright: tuple[
        int,
        int,
        int,
    ]

    ring_colour: tuple[
        int,
        int,
        int,
    ]

    lane_colour: tuple[
        int,
        int,
        int,
    ]

    glow_colour: tuple[
        int,
        int,
        int,
    ]

    fog_colour: tuple[
        int,
        int,
        int,
    ]

    @property
    def background(
        self,
    ) -> tuple[int, int, int]:
        return self.background_colour

    @property
    def tunnel_primary(
        self,
    ) -> tuple[int, int, int]:
        return self.tunnel_bright

    @property
    def tunnel_secondary(
        self,
    ) -> tuple[int, int, int]:
        return self.tunnel_dark

    @property
    def tunnel_lines(
        self,
    ) -> tuple[int, int, int]:
        return self.ring_colour

    @property
    def glow(
        self,
    ) -> tuple[int, int, int]:
        return self.glow_colour


THEMES: Final[
    dict[
        str,
        TunnelTheme,
    ]
] = {

    "blue": TunnelTheme(
        name="blue",
        background_colour=(2, 7, 22),
        tunnel_dark=(7, 28, 100),
        tunnel_bright=(25, 85, 225),
        ring_colour=(70, 180, 255),
        lane_colour=(80, 205, 255),
        glow_colour=(65, 210, 255),
        fog_colour=(2, 7, 22),
    ),

    "electric_blue": TunnelTheme(
        name="electric_blue",
        background_colour=(2, 9, 28),
        tunnel_dark=(10, 42, 120),
        tunnel_bright=(35, 120, 255),
        ring_colour=(100, 220, 255),
        lane_colour=(110, 225, 255),
        glow_colour=(80, 230, 255),
        fog_colour=(2, 9, 28),
    ),

    "cyan": TunnelTheme(
        name="cyan",
        background_colour=(1, 18, 25),
        tunnel_dark=(4, 75, 90),
        tunnel_bright=(20, 210, 225),
        ring_colour=(100, 255, 255),
        lane_colour=(110, 255, 245),
        glow_colour=(75, 255, 245),
        fog_colour=(1, 18, 25),
    ),

    "purple": TunnelTheme(
        name="purple",
        background_colour=(12, 2, 28),
        tunnel_dark=(58, 10, 105),
        tunnel_bright=(155, 40, 245),
        ring_colour=(220, 100, 255),
        lane_colour=(225, 125, 255),
        glow_colour=(215, 75, 255),
        fog_colour=(12, 2, 28),
    ),

    "orange": TunnelTheme(
        name="orange",
        background_colour=(28, 8, 2),
        tunnel_dark=(100, 32, 5),
        tunnel_bright=(245, 105, 28),
        ring_colour=(255, 190, 65),
        lane_colour=(255, 205, 90),
        glow_colour=(255, 160, 45),
        fog_colour=(28, 8, 2),
    ),

    "red": TunnelTheme(
        name="red",
        background_colour=(27, 2, 7),
        tunnel_dark=(95, 8, 25),
        tunnel_bright=(225, 35, 65),
        ring_colour=(255, 110, 125),
        lane_colour=(255, 130, 140),
        glow_colour=(255, 70, 90),
        fog_colour=(27, 2, 7),
    ),

    "pink": TunnelTheme(
        name="pink",
        background_colour=(25, 2, 25),
        tunnel_dark=(95, 12, 80),
        tunnel_bright=(245, 45, 190),
        ring_colour=(255, 120, 225),
        lane_colour=(255, 145, 235),
        glow_colour=(255, 70, 215),
        fog_colour=(25, 2, 25),
    ),

    "white": TunnelTheme(
        name="white",
        background_colour=(8, 10, 15),
        tunnel_dark=(70, 90, 120),
        tunnel_bright=(210, 225, 245),
        ring_colour=(255, 255, 255),
        lane_colour=(220, 245, 255),
        glow_colour=(190, 230, 255),
        fog_colour=(8, 10, 15),
    ),
}


def get_theme(
    theme_name: str,
) -> TunnelTheme:

    cleaned = (
        str(theme_name)
        .strip()
        .lower()
    )

    return THEMES.get(
        cleaned,
        THEMES["blue"],
    )


# ============================================================
# DIFFICULTY TIER
# ============================================================

@dataclass(
    frozen=True
)
class DifficultyTier:

    name: str

    minimum_level: int

    maximum_level: int

    theme_name: str

    colour_theme: str

    minimum_gap_lanes: float

    minimum_safe_angle: float

    maximum_safe_angle: float

    minimum_section_length: float

    maximum_section_length: float

    minimum_recovery_length: float

    maximum_lane_change: float

    speed_multiplier: float = 1.0

    obstacle_density: float = 1.0

    movement_amount: float = 1.0

    movement_speed: float = 1.0

    rotation_speed: float = 1.0

    @property
    def color_theme(
        self,
    ) -> str:
        return self.colour_theme

    @property
    def min_gap_lanes(
        self,
    ) -> float:
        return self.minimum_gap_lanes

    @property
    def minimum_gap_angle(
        self,
    ) -> float:
        return self.minimum_safe_angle

    @property
    def safe_angle(
        self,
    ) -> float:
        return self.minimum_safe_angle

    @property
    def minimum_safe_angle_degrees(
        self,
    ) -> float:
        return self.minimum_safe_angle

    @property
    def maximum_safe_angle_degrees(
        self,
    ) -> float:
        return self.maximum_safe_angle


DIFFICULTY_TIERS: Final[
    tuple[
        DifficultyTier,
        ...,
    ]
] = (

    DifficultyTier(
        name="Beginner",
        minimum_level=1,
        maximum_level=5,
        theme_name="blue",
        colour_theme="blue",
        minimum_gap_lanes=4.0,
        minimum_safe_angle=120.0,
        maximum_safe_angle=220.0,
        minimum_section_length=28.0,
        maximum_section_length=78.0,
        minimum_recovery_length=26.0,
        maximum_lane_change=2.5,
        speed_multiplier=1.00,
        obstacle_density=0.65,
        movement_amount=0.55,
        movement_speed=0.55,
        rotation_speed=0.55,
    ),

    DifficultyTier(
        name="Easy",
        minimum_level=6,
        maximum_level=10,
        theme_name="cyan",
        colour_theme="cyan",
        minimum_gap_lanes=3.6,
        minimum_safe_angle=108.0,
        maximum_safe_angle=205.0,
        minimum_section_length=26.0,
        maximum_section_length=75.0,
        minimum_recovery_length=24.0,
        maximum_lane_change=3.0,
        speed_multiplier=1.02,
        obstacle_density=0.75,
        movement_amount=0.65,
        movement_speed=0.65,
        rotation_speed=0.65,
    ),

    DifficultyTier(
        name="Medium",
        minimum_level=11,
        maximum_level=20,
        theme_name="purple",
        colour_theme="purple",
        minimum_gap_lanes=3.2,
        minimum_safe_angle=96.0,
        maximum_safe_angle=190.0,
        minimum_section_length=23.0,
        maximum_section_length=70.0,
        minimum_recovery_length=22.0,
        maximum_lane_change=3.5,
        speed_multiplier=1.05,
        obstacle_density=0.85,
        movement_amount=0.80,
        movement_speed=0.80,
        rotation_speed=0.80,
    ),

    DifficultyTier(
        name="Hard",
        minimum_level=21,
        maximum_level=30,
        theme_name="orange",
        colour_theme="orange",
        minimum_gap_lanes=2.8,
        minimum_safe_angle=84.0,
        maximum_safe_angle=175.0,
        minimum_section_length=21.0,
        maximum_section_length=66.0,
        minimum_recovery_length=20.0,
        maximum_lane_change=4.0,
        speed_multiplier=1.08,
        obstacle_density=0.95,
        movement_amount=0.95,
        movement_speed=0.95,
        rotation_speed=0.95,
    ),

    DifficultyTier(
        name="Extreme",
        minimum_level=31,
        maximum_level=40,
        theme_name="red",
        colour_theme="red",
        minimum_gap_lanes=2.4,
        minimum_safe_angle=72.0,
        maximum_safe_angle=160.0,
        minimum_section_length=19.0,
        maximum_section_length=62.0,
        minimum_recovery_length=18.0,
        maximum_lane_change=4.5,
        speed_multiplier=1.12,
        obstacle_density=1.05,
        movement_amount=1.05,
        movement_speed=1.05,
        rotation_speed=1.05,
    ),

    DifficultyTier(
        name="Insane",
        minimum_level=41,
        maximum_level=49,
        theme_name="pink",
        colour_theme="pink",
        minimum_gap_lanes=2.1,
        minimum_safe_angle=63.0,
        maximum_safe_angle=145.0,
        minimum_section_length=18.0,
        maximum_section_length=59.0,
        minimum_recovery_length=17.0,
        maximum_lane_change=5.0,
        speed_multiplier=1.15,
        obstacle_density=1.12,
        movement_amount=1.12,
        movement_speed=1.12,
        rotation_speed=1.12,
    ),

    DifficultyTier(
        name="Finale",
        minimum_level=50,
        maximum_level=50,
        theme_name="white",
        colour_theme="white",
        minimum_gap_lanes=2.0,
        minimum_safe_angle=60.0,
        maximum_safe_angle=135.0,
        minimum_section_length=17.0,
        maximum_section_length=56.0,
        minimum_recovery_length=16.0,
        maximum_lane_change=5.0,
        speed_multiplier=1.18,
        obstacle_density=1.18,
        movement_amount=1.18,
        movement_speed=1.18,
        rotation_speed=1.18,
    ),
)


def get_difficulty_tier(
    level_number: int,
) -> DifficultyTier:

    level_number = max(
        1,
        min(
            TOTAL_LEVELS,
            int(level_number),
        ),
    )

    for tier in DIFFICULTY_TIERS:

        if (
            tier.minimum_level
            <= level_number
            <= tier.maximum_level
        ):
            return tier

    return DIFFICULTY_TIERS[-1]


# ============================================================
# ENDLESS SPEED
# ============================================================

ENDLESS_BASE_SPEED: Final[float] = 36.0

ENDLESS_START_SPEED: Final[float] = (
    ENDLESS_BASE_SPEED
)

ENDLESS_MIN_SPEED: Final[float] = (
    ENDLESS_BASE_SPEED
)

ENDLESS_MAX_SPEED: Final[float] = 110.0

ENDLESS_SPEED_PER_1000M: Final[float] = 4.8

ENDLESS_SPEED_INCREASE_PER_METRE: Final[float] = (
    ENDLESS_SPEED_PER_1000M
    / 1000.0
)


def calculate_endless_speed(
    distance: float,
) -> float:

    distance = max(
        0.0,
        float(distance),
    )

    speed = (
        ENDLESS_BASE_SPEED
        + distance
        * ENDLESS_SPEED_INCREASE_PER_METRE
    )

    speed *= GAME_SPEED_MULTIPLIER

    return float(
        clamp(
            speed,
            ENDLESS_MIN_SPEED,
            ENDLESS_MAX_SPEED,
        )
    )


# ============================================================
# ENDLESS DIFFICULTY
# ============================================================

ENDLESS_MAX_DIFFICULTY: Final[float] = 10.0

ENDLESS_DIFFICULTY_DISTANCE: Final[float] = 850.0

ENDLESS_SAFE_START_DISTANCE: Final[float] = 90.0

ENDLESS_SAFE_LANE_MAX_CHANGE: Final[float] = 95.0

ENDLESS_MAX_HARD_PATTERNS_IN_ROW: Final[int] = 3

ENDLESS_EASY_RECOVERY_SECTION_CHANCE: Final[float] = (
    0.18
)


def calculate_endless_difficulty(
    distance: float,
) -> float:

    distance = max(
        0.0,
        float(distance),
    )

    return float(
        clamp(
            distance
            / ENDLESS_DIFFICULTY_DISTANCE,
            0.0,
            ENDLESS_MAX_DIFFICULTY,
        )
    )


def calculate_endless_gap(
    distance: float,
) -> float:

    difficulty = (
        calculate_endless_difficulty(
            distance
        )
    )

    gap = (
        105.0
        - difficulty
        * 4.5
    )

    return float(
        clamp(
            gap,
            55.0,
            105.0,
        )
    )


# ============================================================
# ENDLESS GENERATION
# ============================================================

ENDLESS_GENERATE_AHEAD_DISTANCE: Final[float] = 600.0

ENDLESS_GENERATION_AHEAD_DISTANCE: Final[float] = (
    ENDLESS_GENERATE_AHEAD_DISTANCE
)

ENDLESS_GENERATE_AHEAD: Final[float] = (
    ENDLESS_GENERATE_AHEAD_DISTANCE
)

ENDLESS_GENERATION_AHEAD: Final[float] = (
    ENDLESS_GENERATE_AHEAD_DISTANCE
)

ENDLESS_GENERATION_DISTANCE: Final[float] = (
    ENDLESS_GENERATE_AHEAD_DISTANCE
)

ENDLESS_MAX_ACTIVE_OBSTACLES: Final[int] = 80

ENDLESS_MAX_OBJECTS: Final[int] = (
    ENDLESS_MAX_ACTIVE_OBSTACLES
)

ENDLESS_MAX_ACTIVE_OBJECTS: Final[int] = (
    ENDLESS_MAX_ACTIVE_OBSTACLES
)

ENDLESS_MAX_SECTIONS: Final[int] = (
    ENDLESS_MAX_ACTIVE_OBSTACLES
)

ENDLESS_MAX_GENERATION_PER_FRAME: Final[int] = 4

ENDLESS_GENERATE_PER_FRAME: Final[int] = (
    ENDLESS_MAX_GENERATION_PER_FRAME
)

ENDLESS_REMOVE_BEHIND_DISTANCE: Final[float] = 30.0

ENDLESS_REMOVE_BEHIND: Final[float] = (
    ENDLESS_REMOVE_BEHIND_DISTANCE
)

ENDLESS_CLEANUP_BEHIND: Final[float] = (
    ENDLESS_REMOVE_BEHIND_DISTANCE
)

ENDLESS_CLEANUP_DISTANCE: Final[float] = (
    ENDLESS_REMOVE_BEHIND_DISTANCE
)


# ============================================================
# ENVIRONMENTS
# ============================================================

ENVIRONMENT_INSIDE: Final[str] = "inside"

ENVIRONMENT_OUTSIDE: Final[str] = "outside"

ENVIRONMENT_TRANSITION: Final[str] = "transition"

ENDLESS_ENVIRONMENT_SECTION_LENGTH: Final[float] = (
    1000.0
)

ENDLESS_ENVIRONMENT_TRANSITION_LENGTH: Final[float] = (
    120.0
)

CAMPAIGN_ENVIRONMENT_TRANSITION_LENGTH: Final[float] = (
    90.0
)


# ============================================================
# OBSTACLE NAMES
# ============================================================

OBSTACLE_WALL = "wall"

OBSTACLE_GAP_WALL = "gap_wall"

OBSTACLE_RING_GAP = "ring_gap"

OBSTACLE_SLIDING_WALL = "sliding_wall"

OBSTACLE_MOVING_GAP = "moving_gap"

OBSTACLE_CLOSING_WALL = "closing_wall"

OBSTACLE_ROTATING_BAR = "rotating_bar"

OBSTACLE_DOUBLE_BAR = "double_bar"

OBSTACLE_ROTATING_CROSS = "rotating_cross"

OBSTACLE_SPINNER = "spinner"

OBSTACLE_TRIANGLE = "triangle"

OBSTACLE_DOUBLE_TRIANGLE = "double_triangle"

OBSTACLE_WEDGE = "wedge"

OBSTACLE_ROTATING_WEDGE = "rotating_wedge"

OBSTACLE_DIAMOND = "diamond"

OBSTACLE_BLADE = "blade"

OBSTACLE_DOUBLE_BLADE = "double_blade"

OBSTACLE_TRIPLE_BLADE = "triple_blade"

OBSTACLE_FINISH = "finish"

OBSTACLE_CROSS = "cross"


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_SETTINGS: Final[
    dict[str, object]
] = {

    "fullscreen": False,

    "screen_shake": True,

    "particles": True,

    "speed_lines": True,

    "glow": True,

    "show_fps": False,
}

DEFAULT_SETTINGS_DATA: Final[
    dict[str, object]
] = dict(
    DEFAULT_SETTINGS
)


# ============================================================
# DEFAULT STATISTICS
# ============================================================

DEFAULT_STATISTICS_DATA: Final[
    dict[str, object]
] = {
    "total_runs": 0,
    "total_crashes": 0,
    "total_distance": 0.0,
    "total_play_time": 0.0,
    "total_play_time_seconds": 0.0,
    "maximum_speed": 0.0,

    "campaign_runs": 0,
    "campaign_completions": 0,
    "campaign_crashes": 0,
    "campaign_distance": 0.0,
    "campaign_play_time": 0.0,
    "campaign_play_time_seconds": 0.0,
    "total_campaign_distance": 0.0,
    "total_campaign_play_time": 0.0,
    "total_campaign_play_time_seconds": 0.0,

    "endless_runs": 0,
    "endless_crashes": 0,
    "endless_distance": 0.0,
    "endless_play_time": 0.0,
    "endless_play_time_seconds": 0.0,
    "total_endless_distance": 0.0,
    "total_endless_play_time": 0.0,
    "total_endless_play_time_seconds": 0.0,

    "levels_completed": 0,
    "best_level": 0,
    "highest_level_completed": 0,
    "longest_endless_run": 0.0,
    "longest_endless_distance": 0.0,
    "best_endless_distance": 0.0,
}


# ============================================================
# DEFAULT SAVE DATA
# ============================================================

DEFAULT_SAVE_DATA: Final[
    dict[str, object]
] = {
    "highest_unlocked_level": 1,
    "completed_levels": [],
    "level_best_times": {},
    "level_attempts": {},
    "level_completions": {},
    "level_crashes": {},
    "endless_best_distance": 0,

    **dict(DEFAULT_STATISTICS_DATA),

    "statistics": dict(
        DEFAULT_STATISTICS_DATA
    ),

    "achievements": [],
    "unlocked_achievements": [],
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
        "name": "First Run",
        "description": "Start your first run.",
        "hidden": False,
    },

    "first_level": {
        "name": "Tunnel Rookie",
        "description": "Complete your first level.",
        "hidden": False,
    },

    "level_5": {
        "name": "Getting Faster",
        "description": "Complete Level 5.",
        "hidden": False,
    },

    "level_10": {
        "name": "Tunnel Racer",
        "description": "Complete Level 10.",
        "hidden": False,
    },

    "level_20": {
        "name": "Outside World",
        "description": "Complete Level 20.",
        "hidden": False,
    },

    "level_30": {
        "name": "Expert Runner",
        "description": "Complete Level 30.",
        "hidden": False,
    },

    "level_40": {
        "name": "Tunnel Master",
        "description": "Complete Level 40.",
        "hidden": False,
    },

    "level_50": {
        "name": "Tunnel Legend",
        "description": "Complete all 50 levels.",
        "hidden": False,
    },

    "endless_500": {
        "name": "500 Metres",
        "description": "Run 500 metres in Endless.",
        "hidden": False,
    },

    "endless_1000": {
        "name": "Breaking Out",
        "description": "Run 1,000 metres in Endless.",
        "hidden": False,
    },

    "endless_2500": {
        "name": "Long Distance",
        "description": "Run 2,500 metres in Endless.",
        "hidden": False,
    },

    "endless_5000": {
        "name": "Speed Demon",
        "description": "Run 5,000 metres in Endless.",
        "hidden": False,
    },

    "endless_10000": {
        "name": "Unstoppable",
        "description": "Run 10,000 metres in Endless.",
        "hidden": True,
    },
}


# ============================================================
# OLD CYLINDER ENGINE COMPATIBILITY
# ============================================================

CYLINDER_CENTER_X: Final[int] = (
    GAME_CENTER_X
)

CYLINDER_HORIZON_Y: Final[int] = (
    GAME_CENTER_Y
)

CYLINDER_NEAR_RADIUS: Final[int] = (
    round(
        TUNNEL_NEAR_RADIUS
    )
)

CYLINDER_FAR_RADIUS: Final[int] = (
    round(
        TUNNEL_FAR_RADIUS
    )
)

CYLINDER_PLAYER_Y: Final[int] = (
    GAME_HEIGHT - 110
)

CYLINDER_LANE_COUNT: Final[int] = (
    TUNNEL_LANE_COUNT
)

CYLINDER_RING_COUNT: Final[int] = (
    TUNNEL_RING_COUNT
)

CYLINDER_RING_SPACING: Final[float] = 9.0

CYLINDER_BASE_COLOUR = BLUE

CYLINDER_DARK_COLOUR = DARK_BLUE

CYLINDER_GLOW_COLOUR = CYAN

CYLINDER_LANE_COLOUR = LIGHT_BLUE

CYLINDER_RING_COLOUR = DARK_GREY


# ============================================================
# ACCOUNT TEXT
# ============================================================

ACCOUNT_LOADING_MESSAGE: Final[str] = (
    "Checking your Matthew's Games account..."
)

ACCOUNT_REQUIRED_MESSAGE: Final[str] = (
    "Sign in on Matthew's Games to play Tunnel Runner."
)


# ============================================================
# FORMAT DISTANCE
# ============================================================

def format_distance(
    value: float | int,
) -> str:

    try:
        distance = max(
            0,
            int(
                round(
                    float(value)
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


# ============================================================
# CONFIG SELF TEST
# ============================================================

def validate_config() -> None:

    # --------------------------------------------------------
    # Screen
    # --------------------------------------------------------

    assert GAME_WIDTH > 0
    assert GAME_HEIGHT > 0
    assert FPS >= 60

    # --------------------------------------------------------
    # Levels
    # --------------------------------------------------------

    assert TOTAL_LEVELS == 50

    for level_number in (
        1,
        5,
        10,
        20,
        30,
        40,
        50,
    ):

        tier = get_difficulty_tier(
            level_number
        )

        assert isinstance(
            tier.name,
            str,
        )

        assert isinstance(
            tier.theme_name,
            str,
        )

        assert isinstance(
            tier.colour_theme,
            str,
        )

        assert isinstance(
            tier.minimum_gap_lanes,
            float,
        )

        assert isinstance(
            tier.minimum_safe_angle,
            float,
        )

        assert isinstance(
            tier.maximum_safe_angle,
            float,
        )

        assert (
            tier.minimum_safe_angle
            > 0
        )

        assert (
            tier.maximum_safe_angle
            >= tier.minimum_safe_angle
        )

        assert (
            tier.minimum_section_length
            > 0
        )

        assert (
            tier.maximum_section_length
            >= tier.minimum_section_length
        )

        assert (
            tier.minimum_recovery_length
            > 0
        )

        assert (
            tier.maximum_lane_change
            > 0
        )

        length = calculate_level_length(
            level_number
        )

        start_speed = (
            calculate_level_start_speed(
                level_number
            )
        )

        max_speed = (
            calculate_level_max_speed(
                level_number
            )
        )

        acceleration = (
            calculate_level_acceleration(
                level_number
            )
        )

        speed = calculate_level_speed(
            level_number,
            100.0,
        )

        assert isinstance(
            length,
            float,
        )

        assert isinstance(
            start_speed,
            float,
        )

        assert isinstance(
            max_speed,
            float,
        )

        assert isinstance(
            acceleration,
            float,
        )

        assert isinstance(
            speed,
            float,
        )

        assert length > 0

        assert start_speed > 0

        assert max_speed >= start_speed

        assert acceleration > 0

        assert speed >= start_speed

        assert speed <= max_speed

    # --------------------------------------------------------
    # Themes
    # --------------------------------------------------------

    for theme_name in THEMES:

        theme = get_theme(
            theme_name
        )

        colours = (
            theme.background_colour,
            theme.tunnel_dark,
            theme.tunnel_bright,
            theme.ring_colour,
            theme.lane_colour,
            theme.glow_colour,
            theme.fog_colour,
            theme.background,
            theme.tunnel_primary,
            theme.tunnel_secondary,
            theme.tunnel_lines,
            theme.glow,
        )

        for colour in colours:

            assert isinstance(
                colour,
                tuple,
            )

            assert len(
                colour
            ) == 3

    # --------------------------------------------------------
    # Angles
    # --------------------------------------------------------

    assert TUNNEL_LANE_COUNT > 0

    assert TUNNEL_LANE_ANGLE > 0

    assert abs(
        shortest_angle_difference(
            350.0,
            10.0,
        )
        - 20.0
    ) < 0.001

    assert abs(
        shortest_angle_difference(
            10.0,
            350.0,
        )
        + 20.0
    ) < 0.001

    for lane in range(
        TUNNEL_LANE_COUNT
    ):

        angle = lane_to_angle(
            lane
        )

        recovered = angle_to_lane(
            angle
        )

        assert abs(
            recovered
            - lane
        ) < 0.001

    # --------------------------------------------------------
    # Endless
    # --------------------------------------------------------

    assert (
        ENDLESS_GENERATE_AHEAD
        > 0
    )

    assert (
        ENDLESS_MAX_OBJECTS
        > 0
    )

    assert (
        ENDLESS_REMOVE_BEHIND
        > 0
    )

    assert (
        calculate_endless_speed(
            0
        )
        > 0
    )

    assert (
        calculate_endless_speed(
            1000
        )
        > 0
    )

    assert (
        calculate_endless_difficulty(
            1000
        )
        >= 0
    )

    # --------------------------------------------------------
    # Leaderboard
    # --------------------------------------------------------

    assert SUPABASE_PROJECT_URL

    assert SUPABASE_PUBLISHABLE_KEY

    assert SUPABASE_SCORES_TABLE

    assert (
        LEADERBOARD_GAME_NAME
        == "tunnel-runner"
    )


validate_config()