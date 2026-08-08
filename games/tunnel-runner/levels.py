from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

from config import (
    CAMPAIGN_BASE_SPEED,
    CAMPAIGN_MAX_SPEED,
    ENDLESS_GENERATE_AHEAD,
    ENDLESS_MAX_OBJECTS,
    ENDLESS_REMOVE_BEHIND,
    FIRST_UNLOCKED_LEVEL,
    MODE_ENDLESS,
    MODE_LEVELS,
    OBSTACLE_BLADE,
    OBSTACLE_CLOSING_WALL,
    OBSTACLE_DIAMOND,
    OBSTACLE_DOUBLE_BLADE,
    OBSTACLE_DOUBLE_BAR,
    OBSTACLE_DOUBLE_TRIANGLE,
    OBSTACLE_FINISH,
    OBSTACLE_GAP_WALL,
    OBSTACLE_MOVING_GAP,
    OBSTACLE_RING_GAP,
    OBSTACLE_ROTATING_BAR,
    OBSTACLE_ROTATING_CROSS,
    OBSTACLE_ROTATING_WEDGE,
    OBSTACLE_SLIDING_WALL,
    OBSTACLE_SPINNER,
    OBSTACLE_TRIANGLE,
    OBSTACLE_TRIPLE_BLADE,
    OBSTACLE_WALL,
    OBSTACLE_WEDGE,
    ORANGE,
    PINK,
    RED,
    TOTAL_LEVELS,
    TUNNEL_VISIBLE_LENGTH,
    WHITE,
    YELLOW,
    calculate_endless_gap,
    calculate_endless_speed,
    calculate_level_length,
    calculate_level_speed,
    clamp,
    get_difficulty_tier,
)

from obstacles import (
    OBSTACLE_CROSS,
    ObstacleManager,
    TunnelObstacle,
    create_obstacle,
    create_random_endless_obstacle,
    make_blades,
    make_closing_wall,
    make_finish,
    make_gap_wall,
    make_moving_gap,
    make_rotating_bar,
    make_rotating_cross,
    make_spinner,
)


# ============================================================
# TUNNEL RUNNER
# LEVEL SYSTEM
# VERSION 0.1.0
# ============================================================
#
# This file controls:
#
# - all 50 campaign levels
# - level names
# - level lengths
# - level speeds
# - difficulty progression
# - hand-designed early levels
# - obstacle sequences
# - milestone levels
# - Level 50
# - Endless generation
#
# Important design rule:
#
# The campaign should feel DESIGNED.
#
# We do NOT want every level to simply generate random objects.
#
# Levels 1-10 are strongly hand-authored.
#
# Later levels use structured pattern libraries, but still use
# deterministic seeds so they always produce the same course.
#
# Endless Mode is procedural.
#
# ============================================================


# ============================================================
# LEVEL DEFINITION
# ============================================================

@dataclass(frozen=True)
class LevelDefinition:
    number: int

    name: str

    description: str

    length: float

    speed: float

    maximum_speed: float

    theme_name: str

    difficulty_name: str

    seed: int

    obstacle_density: float

    milestone: bool = False

    finale: bool = False

    metadata: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )


# ============================================================
# GENERATED LEVEL
# ============================================================

@dataclass
class GeneratedLevel:
    definition: LevelDefinition

    obstacles: list[
        TunnelObstacle
    ]

    starting_angle: float = 0.0


# ============================================================
# LEVEL NAMES
# ============================================================

LEVEL_NAMES = (
    "First Run",
    "Choose a Side",
    "Long Turn",
    "Quick Change",
    "First Challenge",

    "Moving Forward",
    "Spin Zone",
    "Double Trouble",
    "Reaction Time",
    "Trial One",

    "Crossfire",
    "Triangle Tunnel",
    "Watch the Gap",
    "Rotating Danger",
    "Speed Test",

    "Blade Runner",
    "Changing Paths",
    "No Easy Route",
    "Closing In",
    "Trial Two",

    "Pressure",
    "The Spinner",
    "Moving Target",
    "Sharp Turns",
    "No Rest",

    "Double Blades",
    "Cross Current",
    "Narrow Escape",
    "Unstable Tunnel",
    "Trial Three",

    "High Velocity",
    "Rotating Walls",
    "Tunnel Storm",
    "Split Second",
    "Maximum Focus",

    "Triple Threat",
    "Moving Maze",
    "Extreme Reaction",
    "Red Line",
    "Trial Four",

    "Into the Void",
    "White Tunnel",
    "Unstable Core",
    "Almost Impossible",
    "Chaos Begins",

    "Chaos Runner",
    "Final Spin",
    "No Safe Side",
    "Last Approach",
    "Tunnel Master",
)


# ============================================================
# LEVEL DESCRIPTIONS
# ============================================================

LEVEL_DESCRIPTIONS = (
    "Learn to move around the tunnel and pass your first openings.",
    "Move between openings on opposite sides of the tunnel.",
    "Follow larger changes around the tunnel.",
    "React to openings that change direction quickly.",
    "Combine everything from the first four levels.",

    "The tunnel starts moving faster.",
    "Meet your first rotating obstacles.",
    "Multiple barriers begin appearing together.",
    "You have less time to react.",
    "Complete your first major trial.",

    "Cross obstacles block much of the tunnel.",
    "Triangle hazards are introduced.",
    "Openings become smaller.",
    "Rotating obstacles become more common.",
    "Handle your first serious speed increase.",

    "Blade obstacles enter the tunnel.",
    "Routes change more often.",
    "Simple obstacles begin combining.",
    "Closing openings are introduced.",
    "Complete the second major trial.",

    "Obstacle spacing becomes tighter.",
    "Fast spinners enter the course.",
    "Moving gaps force you to track the opening.",
    "Direction changes become much sharper.",
    "Recovery time begins disappearing.",

    "Double blades block more of the tunnel.",
    "Rotating crosses appear in combinations.",
    "Safe openings become narrower.",
    "The tunnel constantly changes.",
    "Complete the third major trial.",

    "High speed becomes normal.",
    "Rotating walls and bars dominate the course.",
    "Survive a dense sequence of mixed hazards.",
    "You have only moments to choose a path.",
    "Stay focused through almost nonstop obstacles.",

    "Triple blades are introduced.",
    "Moving hazards combine into a maze.",
    "Reaction time becomes extremely short.",
    "The tunnel enters the extreme difficulty tier.",
    "Complete the fourth major trial.",

    "Enter the final ten levels.",
    "Bright tunnel sections hide difficult obstacles.",
    "Almost every hazard now moves.",
    "Only skilled reactions will get you through.",
    "Chaos patterns begin appearing.",

    "Survive a brutal combination course.",
    "Rotating obstacles reach extreme speeds.",
    "Openings become dangerously narrow.",
    "Face nearly every obstacle type.",
    "Complete the hardest level in Tunnel Runner.",
)


# ============================================================
# LEVEL SEED
# ============================================================

def level_seed(
    level_number: int,
) -> int:
    return (
        912_781
        + int(
            level_number
        )
        * 104_729
    )


# ============================================================
# LEVEL DEFINITION
# ============================================================

def get_level_definition(
    level_number: int,
) -> LevelDefinition:
    if not (
        1
        <= level_number
        <= TOTAL_LEVELS
    ):
        raise ValueError(
            f"Level must be between 1 and {TOTAL_LEVELS}."
        )

    tier = get_difficulty_tier(
        level_number
    )

    speed = calculate_level_speed(
        level_number
    )

    maximum_speed = clamp(
        speed
        + 8.0
        + level_number
        * 0.13,
        speed,
        CAMPAIGN_MAX_SPEED,
    )

    return LevelDefinition(
        number=level_number,

        name=LEVEL_NAMES[
            level_number - 1
        ],

        description=LEVEL_DESCRIPTIONS[
            level_number - 1
        ],

        length=calculate_level_length(
            level_number
        ),

        speed=speed,

        maximum_speed=maximum_speed,

        theme_name=(
            tier.colour_theme
        ),

        difficulty_name=(
            tier.name
        ),

        seed=level_seed(
            level_number
        ),

        obstacle_density=(
            tier.obstacle_density
        ),

        milestone=(
            level_number
            % 10
            == 0
        ),

        finale=(
            level_number
            == TOTAL_LEVELS
        ),

        metadata={
            "mode": MODE_LEVELS,

            "tier": (
                tier.name
            ),
        },
    )


# ============================================================
# CAMPAIGN DEFINITIONS
# ============================================================

CAMPAIGN_LEVELS = tuple(
    get_level_definition(
        level_number
    )
    for level_number in range(
        1,
        TOTAL_LEVELS + 1,
    )
)


CAMPAIGN_LEVEL_MAP = {
    level.number: level
    for level in CAMPAIGN_LEVELS
}


def get_level(
    level_number: int,
) -> LevelDefinition:
    try:
        return CAMPAIGN_LEVEL_MAP[
            int(
                level_number
            )
        ]

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Unknown level: {level_number}"
        ) from error


def get_next_level(
    level_number: int,
) -> LevelDefinition | None:
    return CAMPAIGN_LEVEL_MAP.get(
        int(
            level_number
        )
        + 1
    )


def get_previous_level(
    level_number: int,
) -> LevelDefinition | None:
    return CAMPAIGN_LEVEL_MAP.get(
        int(
            level_number
        )
        - 1
    )


# ============================================================
# PROGRESSION HELPERS
# ============================================================

def is_level_unlocked(
    level_number: int,
    highest_unlocked_level: int,
) -> bool:
    return (
        FIRST_UNLOCKED_LEVEL
        <= level_number
        <= highest_unlocked_level
    )


def unlock_after_completion(
    level_number: int,
    current_highest: int,
) -> int:
    return min(
        TOTAL_LEVELS,
        max(
            current_highest,
            level_number + 1,
        ),
    )


# ============================================================
# OBSTACLE SEQUENCE ITEM
# ============================================================

@dataclass(frozen=True)
class SequenceItem:
    distance: float

    obstacle_type: str

    angle: float = 0.0

    safe_width: float = 90.0

    rotation_speed: float = 0.0

    movement_speed: float = 0.0

    movement_amount: float = 0.0

    colour: tuple[
        int,
        int,
        int,
    ] = RED


# ============================================================
# CREATE FROM SEQUENCE
# ============================================================

def sequence_to_obstacles(
    items: tuple[
        SequenceItem,
        ...,
    ],
) -> list[
    TunnelObstacle
]:
    obstacles: list[
        TunnelObstacle
    ] = []

    for item in items:
        obstacles.append(
            create_obstacle(
                item.obstacle_type,

                z=item.distance,

                angle=item.angle,

                safe_width=(
                    item.safe_width
                ),

                rotation_speed=(
                    item.rotation_speed
                ),

                movement_speed=(
                    item.movement_speed
                ),

                movement_amount=(
                    item.movement_amount
                ),

                primary_colour=(
                    item.colour
                ),

                secondary_colour=(
                    ORANGE
                    if item.colour
                    == RED
                    else YELLOW
                ),
            )
        )

    return obstacles


# ============================================================
# LEVEL 1
# ============================================================

def build_level_1(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    """
    A proper introduction.

    The player starts at angle 0.

    Nothing rotates.

    The first opening is directly in front of the player.
    """

    sequence = (
        SequenceItem(
            85.0,
            OBSTACLE_GAP_WALL,
            0.0,
            125.0,
        ),

        SequenceItem(
            145.0,
            OBSTACLE_GAP_WALL,
            35.0,
            120.0,
        ),

        SequenceItem(
            205.0,
            OBSTACLE_GAP_WALL,
            -40.0,
            115.0,
        ),

        SequenceItem(
            265.0,
            OBSTACLE_GAP_WALL,
            55.0,
            110.0,
        ),

        SequenceItem(
            325.0,
            OBSTACLE_GAP_WALL,
            -65.0,
            105.0,
        ),
    )

    return sequence_to_obstacles(
        sequence
    )


# ============================================================
# LEVEL 2
# ============================================================

def build_level_2(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    sequence = (
        SequenceItem(
            75.0,
            OBSTACLE_GAP_WALL,
            0.0,
            110.0,
        ),

        SequenceItem(
            125.0,
            OBSTACLE_GAP_WALL,
            70.0,
            105.0,
        ),

        SequenceItem(
            180.0,
            OBSTACLE_GAP_WALL,
            -70.0,
            105.0,
        ),

        SequenceItem(
            235.0,
            OBSTACLE_GAP_WALL,
            115.0,
            100.0,
        ),

        SequenceItem(
            290.0,
            OBSTACLE_GAP_WALL,
            -115.0,
            100.0,
        ),

        SequenceItem(
            345.0,
            OBSTACLE_GAP_WALL,
            0.0,
            95.0,
        ),
    )

    return sequence_to_obstacles(
        sequence
    )


# ============================================================
# LEVEL 3
# ============================================================

def build_level_3(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    sequence = (
        SequenceItem(
            70.0,
            OBSTACLE_GAP_WALL,
            0.0,
            105.0,
        ),

        SequenceItem(
            115.0,
            OBSTACLE_GAP_WALL,
            90.0,
            100.0,
        ),

        SequenceItem(
            160.0,
            OBSTACLE_GAP_WALL,
            180.0,
            100.0,
        ),

        SequenceItem(
            205.0,
            OBSTACLE_GAP_WALL,
            270.0,
            95.0,
        ),

        SequenceItem(
            250.0,
            OBSTACLE_GAP_WALL,
            45.0,
            95.0,
        ),

        SequenceItem(
            295.0,
            OBSTACLE_GAP_WALL,
            135.0,
            90.0,
        ),

        SequenceItem(
            340.0,
            OBSTACLE_GAP_WALL,
            225.0,
            90.0,
        ),
    )

    return sequence_to_obstacles(
        sequence
    )


# ============================================================
# LEVEL 4
# ============================================================

def build_level_4(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    sequence = (
        SequenceItem(
            65.0,
            OBSTACLE_GAP_WALL,
            0.0,
            100.0,
        ),

        SequenceItem(
            105.0,
            OBSTACLE_GAP_WALL,
            80.0,
            95.0,
        ),

        SequenceItem(
            145.0,
            OBSTACLE_GAP_WALL,
            -80.0,
            95.0,
        ),

        SequenceItem(
            185.0,
            OBSTACLE_GAP_WALL,
            130.0,
            90.0,
        ),

        SequenceItem(
            225.0,
            OBSTACLE_GAP_WALL,
            -130.0,
            90.0,
        ),

        SequenceItem(
            265.0,
            OBSTACLE_GAP_WALL,
            180.0,
            88.0,
        ),

        SequenceItem(
            305.0,
            OBSTACLE_GAP_WALL,
            70.0,
            85.0,
        ),

        SequenceItem(
            345.0,
            OBSTACLE_GAP_WALL,
            -50.0,
            85.0,
        ),
    )

    return sequence_to_obstacles(
        sequence
    )


# ============================================================
# LEVEL 5
# ============================================================

def build_level_5(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    sequence = (
        SequenceItem(
            60.0,
            OBSTACLE_GAP_WALL,
            0.0,
            95.0,
        ),

        SequenceItem(
            100.0,
            OBSTACLE_GAP_WALL,
            95.0,
            90.0,
        ),

        SequenceItem(
            140.0,
            OBSTACLE_GAP_WALL,
            -95.0,
            90.0,
        ),

        SequenceItem(
            180.0,
            OBSTACLE_GAP_WALL,
            160.0,
            85.0,
        ),

        SequenceItem(
            220.0,
            OBSTACLE_GAP_WALL,
            -160.0,
            85.0,
        ),

        SequenceItem(
            260.0,
            OBSTACLE_GAP_WALL,
            60.0,
            82.0,
        ),

        SequenceItem(
            300.0,
            OBSTACLE_GAP_WALL,
            -60.0,
            82.0,
        ),

        SequenceItem(
            340.0,
            OBSTACLE_GAP_WALL,
            180.0,
            80.0,
        ),
    )

    return sequence_to_obstacles(
        sequence
    )


# ============================================================
# LEVEL 6
# ============================================================

def build_level_6(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    obstacles = build_level_5(
        definition
    )

    obstacles.append(
        make_rotating_bar(
            390.0,

            angle=0.0,

            rotation_speed=32.0,
        )
    )

    return obstacles


# ============================================================
# LEVEL 7
# ============================================================

def build_level_7(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    return [
        make_gap_wall(
            60.0,
            angle=0.0,
            safe_width=90.0,
        ),

        make_rotating_bar(
            115.0,
            angle=0.0,
            rotation_speed=28.0,
        ),

        make_gap_wall(
            170.0,
            angle=85.0,
            safe_width=88.0,
        ),

        make_rotating_bar(
            225.0,
            angle=90.0,
            rotation_speed=-32.0,
        ),

        make_gap_wall(
            280.0,
            angle=-85.0,
            safe_width=84.0,
        ),

        make_rotating_bar(
            335.0,
            angle=45.0,
            rotation_speed=36.0,
        ),
    ]


# ============================================================
# LEVEL 8
# ============================================================

def build_level_8(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    return [
        make_gap_wall(
            55.0,
            angle=0.0,
            safe_width=88.0,
        ),

        create_obstacle(
            OBSTACLE_DOUBLE_BAR,

            z=105.0,

            angle=0.0,

            safe_width=50.0,

            rotation_speed=25.0,
        ),

        make_gap_wall(
            155.0,
            angle=100.0,
            safe_width=82.0,
        ),

        create_obstacle(
            OBSTACLE_DOUBLE_BAR,

            z=205.0,

            angle=45.0,

            safe_width=48.0,

            rotation_speed=-28.0,
        ),

        make_gap_wall(
            255.0,
            angle=-110.0,
            safe_width=80.0,
        ),

        create_obstacle(
            OBSTACLE_DOUBLE_BAR,

            z=305.0,

            angle=90.0,

            safe_width=46.0,

            rotation_speed=32.0,
        ),
    ]


# ============================================================
# LEVEL 9
# ============================================================

def build_level_9(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    return [
        make_gap_wall(
            50.0,
            angle=0.0,
            safe_width=82.0,
        ),

        make_gap_wall(
            92.0,
            angle=100.0,
            safe_width=80.0,
        ),

        make_rotating_bar(
            134.0,
            angle=20.0,
            rotation_speed=36.0,
        ),

        make_gap_wall(
            176.0,
            angle=-120.0,
            safe_width=78.0,
        ),

        make_rotating_bar(
            218.0,
            angle=90.0,
            rotation_speed=-40.0,
        ),

        make_gap_wall(
            260.0,
            angle=150.0,
            safe_width=75.0,
        ),

        make_rotating_bar(
            302.0,
            angle=45.0,
            rotation_speed=42.0,
        ),

        make_gap_wall(
            344.0,
            angle=-40.0,
            safe_width=72.0,
        ),
    ]


# ============================================================
# LEVEL 10
# ============================================================

def build_level_10(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    return [
        make_gap_wall(
            48.0,
            angle=0.0,
            safe_width=80.0,
        ),

        make_rotating_bar(
            90.0,
            angle=0.0,
            rotation_speed=40.0,
        ),

        make_gap_wall(
            132.0,
            angle=100.0,
            safe_width=74.0,
        ),

        create_obstacle(
            OBSTACLE_DOUBLE_BAR,

            z=174.0,

            angle=45.0,

            safe_width=45.0,

            rotation_speed=-35.0,
        ),

        make_gap_wall(
            216.0,
            angle=-110.0,
            safe_width=70.0,
        ),

        make_rotating_cross(
            258.0,

            angle=0.0,

            rotation_speed=30.0,
        ),

        make_gap_wall(
            300.0,
            angle=160.0,
            safe_width=68.0,
        ),

        make_rotating_cross(
            342.0,

            angle=45.0,

            rotation_speed=-34.0,
        ),

        make_gap_wall(
            384.0,
            angle=-60.0,
            safe_width=65.0,
        ),
    ]


# ============================================================
# PATTERN HELPERS
# ============================================================

def append_gap_sequence(
    obstacles: list[
        TunnelObstacle
    ],
    *,
    start_z: float,
    count: int,
    spacing: float,
    start_angle: float,
    angle_change: float,
    safe_width: float,
) -> float:
    z = start_z

    angle = start_angle

    for _ in range(
        count
    ):
        obstacles.append(
            make_gap_wall(
                z,

                angle=angle,

                safe_width=(
                    safe_width
                ),
            )
        )

        z += spacing

        angle = (
            angle
            + angle_change
        ) % 360.0

    return z


def append_zigzag(
    obstacles: list[
        TunnelObstacle
    ],
    *,
    start_z: float,
    count: int,
    spacing: float,
    angle_one: float,
    angle_two: float,
    safe_width: float,
) -> float:
    z = start_z

    for index in range(
        count
    ):
        angle = (
            angle_one
            if index % 2 == 0
            else angle_two
        )

        obstacles.append(
            make_gap_wall(
                z,

                angle=angle,

                safe_width=safe_width,
            )
        )

        z += spacing

    return z


def append_rotating_bars(
    obstacles: list[
        TunnelObstacle
    ],
    *,
    start_z: float,
    count: int,
    spacing: float,
    speed: float,
) -> float:
    z = start_z

    for index in range(
        count
    ):
        obstacles.append(
            make_rotating_bar(
                z,

                angle=(
                    index
                    * 45.0
                ),

                rotation_speed=(
                    speed
                    if index % 2 == 0
                    else -speed
                ),
            )
        )

        z += spacing

    return z


def append_crosses(
    obstacles: list[
        TunnelObstacle
    ],
    *,
    start_z: float,
    count: int,
    spacing: float,
    speed: float,
) -> float:
    z = start_z

    for index in range(
        count
    ):
        obstacles.append(
            make_rotating_cross(
                z,

                angle=(
                    index
                    * 25.0
                ),

                rotation_speed=(
                    speed
                    if index % 2 == 0
                    else -speed
                ),
            )
        )

        z += spacing

    return z


def append_blade_sequence(
    obstacles: list[
        TunnelObstacle
    ],
    *,
    start_z: float,
    count: int,
    spacing: float,
    blade_count: int,
    speed: float,
) -> float:
    z = start_z

    for index in range(
        count
    ):
        obstacles.append(
            make_blades(
                z,

                count=blade_count,

                angle=(
                    index
                    * 35.0
                ),

                rotation_speed=(
                    speed
                    if index % 2 == 0
                    else -speed
                ),
            )
        )

        z += spacing

    return z


# ============================================================
# LEVEL 11+
# ============================================================

def generate_structured_campaign(
    level_number: int,
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    rng = random.Random(
        definition.seed
    )

    obstacles: list[
        TunnelObstacle
    ] = []

    level_length = (
        definition.length
    )

    tier = get_difficulty_tier(
        level_number
    )

    z = 55.0

    safe_width = clamp(
        tier.minimum_safe_angle
        + 22.0,
        tier.minimum_safe_angle,
        100.0,
    )

    spacing = clamp(
        48.0
        / max(
            0.65,
            definition.obstacle_density,
        ),
        22.0,
        50.0,
    )

    previous_angle = 0.0

    hard_pattern_count = 0

    while (
        z
        < level_length
        - 65.0
    ):
        progress = (
            z
            / level_length
        )

        difficulty = (
            level_number
            / 10.0
            + progress
        )

        available: list[
            str
        ] = [
            OBSTACLE_GAP_WALL,
            OBSTACLE_GAP_WALL,
        ]

        if level_number >= 11:
            available.append(
                OBSTACLE_CROSS
            )

        if level_number >= 12:
            available.append(
                OBSTACLE_TRIANGLE
            )

        if level_number >= 14:
            available.append(
                OBSTACLE_ROTATING_BAR
            )

        if level_number >= 16:
            available.append(
                OBSTACLE_BLADE
            )

        if level_number >= 18:
            available.append(
                OBSTACLE_DOUBLE_BAR
            )

        if level_number >= 19:
            available.append(
                OBSTACLE_CLOSING_WALL
            )

        if level_number >= 22:
            available.append(
                OBSTACLE_SPINNER
            )

        if level_number >= 23:
            available.append(
                OBSTACLE_MOVING_GAP
            )

        if level_number >= 26:
            available.append(
                OBSTACLE_DOUBLE_BLADE
            )

        if level_number >= 31:
            available.append(
                OBSTACLE_ROTATING_CROSS
            )

        if level_number >= 33:
            available.append(
                OBSTACLE_DOUBLE_TRIANGLE
            )

        if level_number >= 36:
            available.append(
                OBSTACLE_TRIPLE_BLADE
            )

        if level_number >= 41:
            available.append(
                OBSTACLE_ROTATING_WEDGE
            )

        obstacle_type = rng.choice(
            available
        )

        hard_types = (
            OBSTACLE_SPINNER,
            OBSTACLE_DOUBLE_BLADE,
            OBSTACLE_TRIPLE_BLADE,
            OBSTACLE_ROTATING_CROSS,
            OBSTACLE_CLOSING_WALL,
            OBSTACLE_MOVING_GAP,
        )

        if obstacle_type in hard_types:
            hard_pattern_count += 1

        else:
            hard_pattern_count = 0

        if hard_pattern_count >= 3:
            obstacle_type = (
                OBSTACLE_GAP_WALL
            )

            hard_pattern_count = 0

        maximum_angle_change = clamp(
            70.0
            + level_number
            * 2.2,
            70.0,
            165.0,
        )

        angle = (
            previous_angle
            + rng.uniform(
                -maximum_angle_change,
                maximum_angle_change,
            )
        ) % 360.0

        current_safe_width = clamp(
            safe_width
            - progress
            * 8.0,
            tier.minimum_safe_angle,
            110.0,
        )

        rotation_speed = 0.0

        movement_speed = 0.0

        movement_amount = 0.0

        if obstacle_type in (
            OBSTACLE_ROTATING_BAR,
            OBSTACLE_DOUBLE_BAR,
            OBSTACLE_ROTATING_CROSS,
            OBSTACLE_SPINNER,
            OBSTACLE_DOUBLE_BLADE,
            OBSTACLE_TRIPLE_BLADE,
            OBSTACLE_ROTATING_WEDGE,
        ):
            rotation_speed = (
                rng.choice(
                    (
                        -1.0,
                        1.0,
                    )
                )
                * clamp(
                    25.0
                    + level_number
                    * 1.6,
                    25.0,
                    110.0,
                )
            )

        if (
            obstacle_type
            == OBSTACLE_MOVING_GAP
        ):
            movement_speed = clamp(
                0.65
                + level_number
                * 0.022,
                0.65,
                1.75,
            )

            movement_amount = clamp(
                40.0
                + level_number
                * 1.3,
                40.0,
                105.0,
            )

        if (
            obstacle_type
            == OBSTACLE_CLOSING_WALL
        ):
            movement_speed = clamp(
                0.7
                + level_number
                * 0.018,
                0.7,
                1.65,
            )

        obstacles.append(
            create_obstacle(
                obstacle_type,

                z=z,

                angle=angle,

                safe_width=(
                    current_safe_width
                ),

                rotation_speed=(
                    rotation_speed
                ),

                movement_speed=(
                    movement_speed
                ),

                movement_amount=(
                    movement_amount
                ),

                phase=rng.uniform(
                    0.0,
                    math.tau,
                ),

                primary_colour=(
                    rng.choice(
                        (
                            RED,
                            ORANGE,
                            PINK,
                        )
                    )
                ),
            )
        )

        previous_angle = angle

        spacing_variation = (
            rng.uniform(
                0.88,
                1.12,
            )
        )

        z += (
            spacing
            * spacing_variation
        )

    return obstacles


# ============================================================
# MILESTONE LEVEL OVERRIDES
# ============================================================

def add_milestone_finale(
    level_number: int,
    definition: LevelDefinition,
    obstacles: list[
        TunnelObstacle
    ],
) -> None:
    finale_start = (
        definition.length
        - 220.0
    )

    if level_number == 10:
        append_crosses(
            obstacles,

            start_z=finale_start,

            count=4,

            spacing=46.0,

            speed=36.0,
        )

    elif level_number == 20:
        append_blade_sequence(
            obstacles,

            start_z=finale_start,

            count=5,

            spacing=40.0,

            blade_count=1,

            speed=48.0,
        )

    elif level_number == 30:
        z = finale_start

        for index in range(
            5
        ):
            obstacles.append(
                make_spinner(
                    z,

                    angle=(
                        index
                        * 35.0
                    ),

                    rotation_speed=(
                        55.0
                        if index % 2 == 0
                        else -55.0
                    ),
                )
            )

            z += 37.0

    elif level_number == 40:
        z = finale_start

        for index in range(
            6
        ):
            obstacles.append(
                make_blades(
                    z,

                    count=(
                        2
                        if index % 2 == 0
                        else 3
                    ),

                    angle=(
                        index
                        * 25.0
                    ),

                    rotation_speed=(
                        70.0
                        if index % 2 == 0
                        else -70.0
                    ),
                )
            )

            z += 32.0


# ============================================================
# LEVEL 50
# ============================================================

def build_level_50(
    definition: LevelDefinition,
) -> list[
    TunnelObstacle
]:
    """
    Hand-constructed final section combined with a structured
    opening course.
    """

    obstacles = (
        generate_structured_campaign(
            50,
            definition,
        )
    )

    finale_start = (
        definition.length
        - 340.0
    )

    finale = [
        make_spinner(
            finale_start,

            angle=0.0,

            rotation_speed=82.0,
        ),

        make_gap_wall(
            finale_start + 38.0,

            angle=120.0,

            safe_width=42.0,
        ),

        make_blades(
            finale_start + 76.0,

            count=3,

            angle=20.0,

            rotation_speed=-92.0,
        ),

        make_moving_gap(
            finale_start + 114.0,

            angle=230.0,

            safe_width=40.0,

            movement_amount=92.0,

            movement_speed=1.5,
        ),

        make_rotating_cross(
            finale_start + 152.0,

            angle=45.0,

            rotation_speed=98.0,
        ),

        make_closing_wall(
            finale_start + 190.0,

            angle=320.0,

            safe_width=58.0,

            movement_speed=1.55,
        ),

        make_blades(
            finale_start + 228.0,

            count=3,

            angle=90.0,

            rotation_speed=105.0,
        ),

        make_spinner(
            finale_start + 266.0,

            angle=15.0,

            rotation_speed=-108.0,
        ),
    ]

    obstacles.extend(
        finale
    )

    return obstacles


# ============================================================
# GENERATE CAMPAIGN LEVEL
# ============================================================

def generate_campaign_level(
    level_number: int,
) -> GeneratedLevel:
    definition = get_level(
        level_number
    )

    if level_number == 1:
        obstacles = build_level_1(
            definition
        )

    elif level_number == 2:
        obstacles = build_level_2(
            definition
        )

    elif level_number == 3:
        obstacles = build_level_3(
            definition
        )

    elif level_number == 4:
        obstacles = build_level_4(
            definition
        )

    elif level_number == 5:
        obstacles = build_level_5(
            definition
        )

    elif level_number == 6:
        obstacles = build_level_6(
            definition
        )

    elif level_number == 7:
        obstacles = build_level_7(
            definition
        )

    elif level_number == 8:
        obstacles = build_level_8(
            definition
        )

    elif level_number == 9:
        obstacles = build_level_9(
            definition
        )

    elif level_number == 10:
        obstacles = build_level_10(
            definition
        )

    elif level_number == 50:
        obstacles = build_level_50(
            definition
        )

    else:
        obstacles = (
            generate_structured_campaign(
                level_number,
                definition,
            )
        )

    if (
        level_number
        in (
            20,
            30,
            40,
        )
    ):
        add_milestone_finale(
            level_number,
            definition,
            obstacles,
        )

    # Remove anything accidentally beyond the finish.
    obstacles = [
        obstacle
        for obstacle
        in obstacles
        if (
            obstacle.z
            < definition.length
            - 15.0
        )
    ]

    obstacles.append(
        make_finish(
            definition.length
        )
    )

    obstacles.sort(
        key=lambda obstacle: (
            obstacle.z
        )
    )

    return GeneratedLevel(
        definition=definition,

        obstacles=obstacles,

        starting_angle=0.0,
    )


# ============================================================
# LOAD LEVEL INTO MANAGER
# ============================================================

def load_campaign_into_manager(
    manager: ObstacleManager,
    level_number: int,
) -> GeneratedLevel:
    generated = (
        generate_campaign_level(
            level_number
        )
    )

    manager.clear()

    manager.extend(
        generated.obstacles
    )

    return generated


# ============================================================
# CAMPAIGN SPEED
# ============================================================

def campaign_speed_at_distance(
    level_number: int,
    distance: float,
) -> float:
    definition = get_level(
        level_number
    )

    progress = clamp(
        distance
        / max(
            1.0,
            definition.length
        ),
        0.0,
        1.0,
    )

    # Campaign speed increases only a little inside a level.
    #
    # Difficulty should mainly come from layouts, not simply
    # endlessly increasing speed.

    speed = (
        definition.speed
        + (
            definition.maximum_speed
            - definition.speed
        )
        * progress
        * 0.30
    )

    return clamp(
        speed,
        definition.speed,
        definition.maximum_speed,
    )


# ============================================================
# ENDLESS GENERATOR
# ============================================================

@dataclass
class EndlessGeneratorState:
    seed: int | None = None

    next_z: float = 75.0

    previous_angle: float = 0.0

    generated_count: int = 0

    last_obstacle_type: str = ""

    consecutive_hard: int = 0


class EndlessGenerator:
    def __init__(
        self,
        seed: int | None = None,
    ):
        self.random = random.Random(
            seed
        )

        self.state = (
            EndlessGeneratorState(
                seed=seed
            )
        )

        self.reset(
            seed
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        seed: int | None = None,
    ) -> None:
        if seed is not None:
            self.random.seed(
                seed
            )

        self.state = (
            EndlessGeneratorState(
                seed=seed,

                next_z=75.0,

                previous_angle=0.0,

                generated_count=0,

                last_obstacle_type="",

                consecutive_hard=0,
            )
        )

    # ========================================================
    # DIFFICULTY
    # ========================================================

    def difficulty(
        self,
        distance: float,
    ) -> float:
        return clamp(
            distance
            / 500.0,
            0.0,
            12.0,
        )

    # ========================================================
    # GENERATE NEXT
    # ========================================================

    def generate_next(
        self,
    ) -> TunnelObstacle:
        difficulty = self.difficulty(
            self.state.next_z
        )

        obstacle = (
            create_random_endless_obstacle(
                z=self.state.next_z,

                difficulty=difficulty,

                previous_angle=(
                    self.state.previous_angle
                ),

                rng=self.random,
            )
        )

        hard_types = (
            OBSTACLE_SPINNER,
            OBSTACLE_DOUBLE_BLADE,
            OBSTACLE_TRIPLE_BLADE,
            OBSTACLE_ROTATING_CROSS,
            OBSTACLE_MOVING_GAP,
            OBSTACLE_CLOSING_WALL,
        )

        if (
            obstacle.obstacle_type
            in hard_types
        ):
            self.state.consecutive_hard += 1

        else:
            self.state.consecutive_hard = 0

        if (
            self.state.consecutive_hard
            >= 3
        ):
            obstacle = make_gap_wall(
                self.state.next_z,

                angle=(
                    self.state.previous_angle
                ),

                safe_width=clamp(
                    92.0
                    - difficulty
                    * 3.0,
                    48.0,
                    92.0,
                ),
            )

            self.state.consecutive_hard = 0

        self.state.previous_angle = (
            obstacle.angle
        )

        self.state.last_obstacle_type = (
            obstacle.obstacle_type
        )

        self.state.generated_count += 1

        gap = calculate_endless_gap(
            self.state.next_z
        )

        gap *= self.random.uniform(
            0.90,
            1.12,
        )

        self.state.next_z += (
            gap
        )

        return obstacle

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        manager: ObstacleManager,
        camera_z: float,
    ) -> None:
        target_z = (
            camera_z
            + ENDLESS_GENERATE_AHEAD
        )

        while (
            self.state.next_z
            < target_z
            and len(
                manager.obstacles
            )
            < ENDLESS_MAX_OBJECTS
        ):
            manager.add(
                self.generate_next()
            )

        manager.remove_behind(
            camera_z,

            margin=(
                ENDLESS_REMOVE_BEHIND
            ),
        )


# ============================================================
# PREPARE ENDLESS
# ============================================================

def prepare_endless(
    manager: ObstacleManager,
    generator: EndlessGenerator,
) -> None:
    manager.clear()

    generator.reset()

    # Start with several simple obstacles.
    manager.add(
        make_gap_wall(
            80.0,

            angle=0.0,

            safe_width=110.0,
        )
    )

    manager.add(
        make_gap_wall(
            125.0,

            angle=50.0,

            safe_width=105.0,
        )
    )

    manager.add(
        make_gap_wall(
            170.0,

            angle=-55.0,

            safe_width=100.0,
        )
    )

    generator.state.next_z = (
        215.0
    )

    generator.state.previous_angle = (
        -55.0
    )


# ============================================================
# ENDLESS SPEED
# ============================================================

def endless_speed_at_distance(
    distance: float,
) -> float:
    return calculate_endless_speed(
        distance
    )


# ============================================================
# LEVEL COMPLETION
# ============================================================

def level_completion_percentage(
    level_number: int,
    distance: float,
) -> float:
    definition = get_level(
        level_number
    )

    return clamp(
        (
            distance
            / max(
                1.0,
                definition.length
            )
        )
        * 100.0,
        0.0,
        100.0,
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_level_definitions(
) -> None:
    if len(
        LEVEL_NAMES
    ) != TOTAL_LEVELS:
        raise ValueError(
            "LEVEL_NAMES does not contain 50 levels."
        )

    if len(
        LEVEL_DESCRIPTIONS
    ) != TOTAL_LEVELS:
        raise ValueError(
            "LEVEL_DESCRIPTIONS does not contain 50 levels."
        )

    if len(
        CAMPAIGN_LEVELS
    ) != TOTAL_LEVELS:
        raise ValueError(
            "Campaign level count is incorrect."
        )

    for (
        expected,
        definition,
    ) in enumerate(
        CAMPAIGN_LEVELS,
        start=1,
    ):
        if (
            definition.number
            != expected
        ):
            raise ValueError(
                "Campaign numbering is invalid."
            )

        if definition.length <= 0:
            raise ValueError(
                f"Level {expected} has invalid length."
            )

        if definition.speed <= 0:
            raise ValueError(
                f"Level {expected} has invalid speed."
            )


def validate_generated_levels(
) -> None:
    """
    Generate all 50 levels now.

    That way a broken obstacle definition is found immediately
    instead of when the player eventually reaches that level.
    """

    for level_number in range(
        1,
        TOTAL_LEVELS + 1,
    ):
        generated = (
            generate_campaign_level(
                level_number
            )
        )

        if not (
            generated.obstacles
        ):
            raise ValueError(
                f"Level {level_number} has no obstacles."
            )

        finish = (
            generated.obstacles[-1]
        )

        if (
            finish.obstacle_type
            != OBSTACLE_FINISH
        ):
            raise ValueError(
                f"Level {level_number} does not end with a finish."
            )

        previous_z = -1.0

        for obstacle in (
            generated.obstacles
        ):
            if obstacle.z < previous_z:
                raise ValueError(
                    f"Level {level_number} obstacle ordering failed."
                )

            previous_z = (
                obstacle.z
            )


validate_level_definitions()
validate_generated_levels()