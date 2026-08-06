from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Final, Iterable

from config import (
    ALL_PATTERN_TYPES,
    CYLINDER_LANE_COUNT,
    FIRST_UNLOCKED_LEVEL,
    LEVEL_COUNTDOWN_SECONDS,
    LEVEL_FINISH_LINE_DISTANCE,
    LEVEL_TIERS,
    MODE_LEVELS,
    OBSTACLE_BLOCK,
    OBSTACLE_CHASER,
    OBSTACLE_DEFINITIONS,
    OBSTACLE_DOUBLE_GAP,
    OBSTACLE_FAKE_GAP,
    OBSTACLE_FINISH_LINE,
    OBSTACLE_LASER,
    OBSTACLE_MOVING_BLOCK,
    OBSTACLE_NARROW_GATE,
    OBSTACLE_PULSE_BLOCK,
    OBSTACLE_ROTATING_WALL,
    OBSTACLE_SPIKE,
    OBSTACLE_TALL_BLOCK,
    OBSTACLE_WALL_GAP,
    OBSTACLE_WIDE_BLOCK,
    PATTERN_BOSS_SECTION,
    PATTERN_DOUBLE,
    PATTERN_GAUNTLET,
    PATTERN_MOVING,
    PATTERN_ROTATING,
    PATTERN_SINGLE,
    PATTERN_SLALOM,
    PATTERN_SPIRAL,
    PATTERN_TRIPLE,
    PATTERN_WALL,
    PATTERN_ZIGZAG,
    TOTAL_LEVELS,
    calculate_level_length,
    calculate_level_speed,
    clamp,
    get_level_tier,
    lane_to_angle,
)


# ============================================================
# LEVEL DATA CLASSES
# ============================================================

@dataclass(frozen=True)
class PatternObstacle:
    """
    One obstacle inside a level pattern.

    distance_offset:
        Distance from the start of the pattern.

    lane:
        Cylinder lane where the obstacle begins.

    lane_span:
        Number of lanes occupied.

    movement_amount:
        Number of lanes the obstacle may move through.

    movement_speed:
        Movement speed measured in lanes per second.

    rotation_speed:
        Angular movement in degrees per second.

    phase_offset:
        Animation starting phase.

    fake:
        Used for deceptive obstacles and visual decoys.
    """

    obstacle_type: str

    distance_offset: float
    lane: int

    lane_span: int = 1

    movement_amount: float = 0.0
    movement_speed: float = 0.0

    rotation_speed: float = 0.0
    phase_offset: float = 0.0

    fake: bool = False

    metadata: dict[str, object] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class LevelPattern:
    """
    A reusable obstacle formation.
    """

    pattern_type: str
    name: str

    start_distance: float
    length: float

    obstacles: tuple[PatternObstacle, ...]

    safe_lanes: tuple[int, ...] = ()

    difficulty: float = 1.0

    repeat_count: int = 1
    repeat_spacing: float = 0.0

    rotate_each_repeat: int = 0
    mirror_each_repeat: bool = False

    warning_text: str = ""

    metadata: dict[str, object] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class LevelDefinition:
    """
    Complete data for one campaign level.
    """

    number: int
    name: str
    description: str

    tier_name: str

    length: float

    starting_speed: float
    maximum_speed: float

    acceleration: float

    patterns: tuple[LevelPattern, ...]

    countdown_seconds: int = LEVEL_COUNTDOWN_SECONDS

    background_theme: str = "neon_blue"
    cylinder_theme: str = "neon_blue"

    music_track: str = "gameplay_theme.ogg"

    allow_powerups: bool = True

    recommended_difficulty: int = 1

    medal_distances: tuple[float, float, float] = (
        0.0,
        0.0,
        0.0,
    )

    metadata: dict[str, object] = field(
        default_factory=dict
    )


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_lane(lane: int) -> int:
    """
    Keep a lane inside the cylinder lane range.
    """

    return lane % CYLINDER_LANE_COUNT


def normalize_lane_span(
    lane_span: int,
) -> int:
    """
    Keep an obstacle width within sensible limits.
    """

    return int(
        clamp(
            lane_span,
            1,
            CYLINDER_LANE_COUNT - 1,
        )
    )


def obstacle(
    obstacle_type: str,
    distance_offset: float,
    lane: int,
    lane_span: int = 1,
    movement_amount: float = 0.0,
    movement_speed: float = 0.0,
    rotation_speed: float = 0.0,
    phase_offset: float = 0.0,
    fake: bool = False,
    **metadata: object,
) -> PatternObstacle:
    """
    Convenient constructor for pattern obstacles.
    """

    if obstacle_type not in OBSTACLE_DEFINITIONS:
        obstacle_type = OBSTACLE_BLOCK

    return PatternObstacle(
        obstacle_type=obstacle_type,
        distance_offset=max(
            0.0,
            float(distance_offset),
        ),
        lane=normalize_lane(lane),
        lane_span=normalize_lane_span(
            lane_span
        ),
        movement_amount=float(
            movement_amount
        ),
        movement_speed=float(
            movement_speed
        ),
        rotation_speed=float(
            rotation_speed
        ),
        phase_offset=float(
            phase_offset
        ),
        fake=bool(fake),
        metadata=dict(metadata),
    )


def pattern(
    pattern_type: str,
    name: str,
    start_distance: float,
    length: float,
    obstacles: Iterable[PatternObstacle],
    safe_lanes: Iterable[int] = (),
    difficulty: float = 1.0,
    repeat_count: int = 1,
    repeat_spacing: float = 0.0,
    rotate_each_repeat: int = 0,
    mirror_each_repeat: bool = False,
    warning_text: str = "",
    **metadata: object,
) -> LevelPattern:
    """
    Convenient constructor for level patterns.
    """

    cleaned_type = (
        pattern_type
        if pattern_type in ALL_PATTERN_TYPES
        else PATTERN_SINGLE
    )

    cleaned_safe_lanes = tuple(
        normalize_lane(lane)
        for lane in safe_lanes
    )

    return LevelPattern(
        pattern_type=cleaned_type,
        name=str(name),
        start_distance=max(
            0.0,
            float(start_distance),
        ),
        length=max(
            1.0,
            float(length),
        ),
        obstacles=tuple(obstacles),
        safe_lanes=cleaned_safe_lanes,
        difficulty=max(
            0.1,
            float(difficulty),
        ),
        repeat_count=max(
            1,
            int(repeat_count),
        ),
        repeat_spacing=max(
            0.0,
            float(repeat_spacing),
        ),
        rotate_each_repeat=int(
            rotate_each_repeat
        ),
        mirror_each_repeat=bool(
            mirror_each_repeat
        ),
        warning_text=str(
            warning_text
        ),
        metadata=dict(metadata),
    )


def occupied_lanes(
    pattern_obstacle: PatternObstacle,
) -> set[int]:
    """
    Return all lanes occupied by an obstacle.
    """

    return {
        normalize_lane(
            pattern_obstacle.lane + offset
        )
        for offset in range(
            pattern_obstacle.lane_span
        )
    }


def free_lanes_at_offset(
    obstacles: Iterable[PatternObstacle],
    distance_offset: float,
    tolerance: float = 2.5,
) -> set[int]:
    """
    Return lanes that are not occupied near a distance.
    """

    blocked: set[int] = set()

    for item in obstacles:
        if abs(
            item.distance_offset
            - distance_offset
        ) > tolerance:
            continue

        blocked.update(
            occupied_lanes(item)
        )

    return (
        set(range(CYLINDER_LANE_COUNT))
        - blocked
    )


def pattern_has_possible_path(
    level_pattern: LevelPattern,
) -> bool:
    """
    Basic safety test.

    Each obstacle row must leave at least one lane open.
    More advanced path prediction will later live in the
    level generator and collision engine.
    """

    offsets = sorted(
        {
            round(
                item.distance_offset,
                2,
            )
            for item in level_pattern.obstacles
        }
    )

    for offset in offsets:
        if not free_lanes_at_offset(
            level_pattern.obstacles,
            offset,
        ):
            return False

    return True


def validate_pattern(
    level_pattern: LevelPattern,
) -> None:
    """
    Raise an error for an invalid level pattern.
    """

    if level_pattern.length <= 0:
        raise ValueError(
            f"{level_pattern.name} has no length."
        )

    if not level_pattern.obstacles:
        return

    if not pattern_has_possible_path(
        level_pattern
    ):
        raise ValueError(
            f"{level_pattern.name} blocks every lane."
        )


# ============================================================
# REUSABLE PATTERN BUILDERS
# ============================================================

def build_single_pattern(
    start_distance: float,
    lane: int,
    obstacle_type: str = OBSTACLE_BLOCK,
    difficulty: float = 1.0,
) -> LevelPattern:
    return pattern(
        pattern_type=PATTERN_SINGLE,
        name="Single Barrier",
        start_distance=start_distance,
        length=18.0,
        obstacles=(
            obstacle(
                obstacle_type,
                8.0,
                lane,
            ),
        ),
        difficulty=difficulty,
    )


def build_double_pattern(
    start_distance: float,
    first_lane: int,
    separation: int = 4,
    obstacle_type: str = OBSTACLE_BLOCK,
    difficulty: float = 1.0,
) -> LevelPattern:
    second_lane = normalize_lane(
        first_lane + separation
    )

    return pattern(
        pattern_type=PATTERN_DOUBLE,
        name="Double Barrier",
        start_distance=start_distance,
        length=20.0,
        obstacles=(
            obstacle(
                obstacle_type,
                8.0,
                first_lane,
            ),

            obstacle(
                obstacle_type,
                8.0,
                second_lane,
            ),
        ),
        difficulty=difficulty,
    )


def build_triple_pattern(
    start_distance: float,
    first_lane: int,
    spacing: int = 3,
    obstacle_type: str = OBSTACLE_BLOCK,
    difficulty: float = 1.0,
) -> LevelPattern:
    return pattern(
        pattern_type=PATTERN_TRIPLE,
        name="Triple Barrier",
        start_distance=start_distance,
        length=22.0,
        obstacles=(
            obstacle(
                obstacle_type,
                9.0,
                first_lane,
            ),

            obstacle(
                obstacle_type,
                9.0,
                first_lane + spacing,
            ),

            obstacle(
                obstacle_type,
                9.0,
                first_lane + spacing * 2,
            ),
        ),
        difficulty=difficulty,
    )


def build_wall_pattern(
    start_distance: float,
    safe_lane: int,
    gap_width: int = 2,
    obstacle_type: str = OBSTACLE_WALL_GAP,
    difficulty: float = 1.0,
) -> LevelPattern:
    safe_lane = normalize_lane(
        safe_lane
    )

    gap_width = max(
        1,
        min(
            4,
            int(gap_width),
        ),
    )

    safe_lanes = {
        normalize_lane(
            safe_lane + offset
        )
        for offset in range(gap_width)
    }

    obstacles: list[PatternObstacle] = []

    for lane in range(CYLINDER_LANE_COUNT):
        if lane in safe_lanes:
            continue

        obstacles.append(
            obstacle(
                obstacle_type,
                10.0,
                lane,
            )
        )

    return pattern(
        pattern_type=PATTERN_WALL,
        name="Gap Wall",
        start_distance=start_distance,
        length=24.0,
        obstacles=obstacles,
        safe_lanes=safe_lanes,
        difficulty=difficulty,
        warning_text="Find the opening",
    )


def build_zigzag_pattern(
    start_distance: float,
    starting_lane: int,
    steps: int = 5,
    lane_step: int = 2,
    obstacle_type: str = OBSTACLE_BLOCK,
    spacing: float = 11.0,
    difficulty: float = 1.0,
) -> LevelPattern:
    obstacles: list[PatternObstacle] = []

    lane = normalize_lane(
        starting_lane
    )

    direction = 1

    for index in range(steps):
        blocked_lane = normalize_lane(
            lane + 6
        )

        obstacles.append(
            obstacle(
                obstacle_type,
                8.0 + index * spacing,
                blocked_lane,
                lane_span=3,
            )
        )

        lane = normalize_lane(
            lane
            + lane_step * direction
        )

        direction *= -1

    return pattern(
        pattern_type=PATTERN_ZIGZAG,
        name="Zigzag",
        start_distance=start_distance,
        length=(
            18.0
            + max(
                0,
                steps - 1,
            )
            * spacing
        ),
        obstacles=obstacles,
        difficulty=difficulty,
    )


def build_slalom_pattern(
    start_distance: float,
    starting_lane: int,
    steps: int = 6,
    spacing: float = 10.0,
    difficulty: float = 1.0,
) -> LevelPattern:
    obstacles: list[PatternObstacle] = []

    for index in range(steps):
        lane = normalize_lane(
            starting_lane
            + (
                4
                if index % 2 == 0
                else -4
            )
        )

        obstacles.append(
            obstacle(
                OBSTACLE_WIDE_BLOCK,
                8.0 + index * spacing,
                lane,
                lane_span=2,
            )
        )

    return pattern(
        pattern_type=PATTERN_SLALOM,
        name="Slalom",
        start_distance=start_distance,
        length=(
            18.0
            + max(
                0,
                steps - 1,
            )
            * spacing
        ),
        obstacles=obstacles,
        difficulty=difficulty,
    )


def build_spiral_pattern(
    start_distance: float,
    starting_lane: int,
    steps: int = 9,
    lane_step: int = 1,
    spacing: float = 8.0,
    obstacle_type: str = OBSTACLE_TALL_BLOCK,
    difficulty: float = 1.0,
) -> LevelPattern:
    obstacles: list[PatternObstacle] = []

    for index in range(steps):
        lane = normalize_lane(
            starting_lane
            + index * lane_step
        )

        obstacles.append(
            obstacle(
                obstacle_type,
                8.0 + index * spacing,
                lane,
                lane_span=2,
            )
        )

    return pattern(
        pattern_type=PATTERN_SPIRAL,
        name="Spiral",
        start_distance=start_distance,
        length=(
            18.0
            + max(
                0,
                steps - 1,
            )
            * spacing
        ),
        obstacles=obstacles,
        difficulty=difficulty,
    )


def build_moving_pattern(
    start_distance: float,
    starting_lane: int,
    obstacle_count: int = 3,
    spacing: float = 13.0,
    movement_amount: float = 3.0,
    movement_speed: float = 1.0,
    difficulty: float = 1.0,
) -> LevelPattern:
    obstacles: list[PatternObstacle] = []

    for index in range(obstacle_count):
        obstacles.append(
            obstacle(
                OBSTACLE_MOVING_BLOCK,
                9.0 + index * spacing,
                starting_lane + index * 4,
                movement_amount=movement_amount,
                movement_speed=movement_speed,
                phase_offset=index * 0.8,
            )
        )

    return pattern(
        pattern_type=PATTERN_MOVING,
        name="Moving Barriers",
        start_distance=start_distance,
        length=(
            20.0
            + max(
                0,
                obstacle_count - 1,
            )
            * spacing
        ),
        obstacles=obstacles,
        difficulty=difficulty,
        warning_text="Moving barriers",
    )


def build_rotating_pattern(
    start_distance: float,
    starting_lane: int,
    obstacle_count: int = 4,
    spacing: float = 12.0,
    rotation_speed: float = 42.0,
    difficulty: float = 1.0,
) -> LevelPattern:
    obstacles: list[PatternObstacle] = []

    for index in range(obstacle_count):
        obstacles.append(
            obstacle(
                OBSTACLE_ROTATING_WALL,
                10.0 + index * spacing,
                starting_lane + index * 3,
                lane_span=5,
                rotation_speed=(
                    rotation_speed
                    if index % 2 == 0
                    else -rotation_speed
                ),
                phase_offset=index * 0.65,
            )
        )

    return pattern(
        pattern_type=PATTERN_ROTATING,
        name="Rotating Walls",
        start_distance=start_distance,
        length=(
            22.0
            + max(
                0,
                obstacle_count - 1,
            )
            * spacing
        ),
        obstacles=obstacles,
        difficulty=difficulty,
        warning_text="Rotating walls ahead",
    )


def build_gauntlet_pattern(
    start_distance: float,
    starting_lane: int,
    difficulty: float = 1.0,
) -> LevelPattern:
    obstacles = (
        obstacle(
            OBSTACLE_WIDE_BLOCK,
            8.0,
            starting_lane,
            lane_span=2,
        ),

        obstacle(
            OBSTACLE_SPIKE,
            18.0,
            starting_lane + 4,
        ),

        obstacle(
            OBSTACLE_MOVING_BLOCK,
            29.0,
            starting_lane + 8,
            movement_amount=3.0,
            movement_speed=1.2,
        ),

        obstacle(
            OBSTACLE_TALL_BLOCK,
            40.0,
            starting_lane + 2,
            lane_span=2,
        ),

        obstacle(
            OBSTACLE_PULSE_BLOCK,
            51.0,
            starting_lane + 6,
            lane_span=2,
        ),

        obstacle(
            OBSTACLE_LASER,
            62.0,
            starting_lane + 10,
            lane_span=3,
        ),
    )

    return pattern(
        pattern_type=PATTERN_GAUNTLET,
        name="Gauntlet",
        start_distance=start_distance,
        length=78.0,
        obstacles=obstacles,
        difficulty=difficulty,
        warning_text="Gauntlet section",
    )


def build_boss_pattern(
    start_distance: float,
    level_number: int,
) -> LevelPattern:
    """
    Create a large milestone pattern for levels ending in 0
    and for Level 50.
    """

    boss_stage = max(
        1,
        level_number // 10,
    )

    obstacles: list[PatternObstacle] = []

    row_spacing = max(
        7.5,
        12.5 - boss_stage * 0.8,
    )

    row_count = 6 + boss_stage * 2

    safe_lane = normalize_lane(
        level_number
    )

    for row in range(row_count):
        distance_offset = (
            10.0 + row * row_spacing
        )

        safe_lane = normalize_lane(
            safe_lane
            + (
                2
                if row % 2 == 0
                else -3
            )
        )

        safe_width = (
            2
            if boss_stage < 4
            else 1
        )

        safe_lanes = {
            normalize_lane(
                safe_lane + offset
            )
            for offset in range(
                safe_width
            )
        }

        for lane in range(
            CYLINDER_LANE_COUNT
        ):
            if lane in safe_lanes:
                continue

            obstacle_type = (
                OBSTACLE_ROTATING_WALL
                if boss_stage >= 4
                and row % 3 == 0
                else OBSTACLE_FAKE_GAP
                if boss_stage >= 5
                and row % 4 == 0
                else OBSTACLE_BLOCK
            )

            obstacles.append(
                obstacle(
                    obstacle_type,
                    distance_offset,
                    lane,
                    rotation_speed=(
                        34.0
                        if obstacle_type
                        == OBSTACLE_ROTATING_WALL
                        else 0.0
                    ),
                    fake=(
                        obstacle_type
                        == OBSTACLE_FAKE_GAP
                    ),
                )
            )

    return pattern(
        pattern_type=PATTERN_BOSS_SECTION,
        name=f"Boss Course {boss_stage}",
        start_distance=start_distance,
        length=(
            24.0
            + row_count * row_spacing
        ),
        obstacles=obstacles,
        difficulty=(
            2.0
            + boss_stage * 0.8
        ),
        warning_text="FINAL COURSE",
        boss_stage=boss_stage,
    )


# ============================================================
# PROCEDURAL CAMPAIGN LEVEL BUILDER
# ============================================================

LEVEL_NAMES: Final[tuple[str, ...]] = (
    "First Rotation",
    "Opening Lane",
    "Two Sides",
    "Wide Turn",
    "First Test",

    "Faster Ground",
    "Tower Line",
    "Moving Target",
    "Broken Path",
    "Velocity Check",

    "Cross Current",
    "Double Opening",
    "Sharp Turn",
    "Long Spiral",
    "Pressure Line",

    "Rotating Sector",
    "Split Decision",
    "Narrow Escape",
    "Moving Maze",
    "Orbital Trial",

    "Rapid Slalom",
    "Energy Spikes",
    "Twisting Route",
    "False Safety",
    "Momentum",

    "Pulse Sector",
    "Double Spiral",
    "Moving Walls",
    "No Rest",
    "Core Trial",

    "High Velocity",
    "Laser Entry",
    "Closing Gaps",
    "False Horizon",
    "Tracking Line",

    "Reaction Test",
    "Rotation Storm",
    "Laser Grid",
    "Narrow Orbit",
    "Gravity Trial",

    "Extreme Entry",
    "Tracking Storm",
    "Pulse Maze",
    "Broken Orbit",
    "Velocity Collapse",

    "Spiral Gauntlet",
    "No Safe Side",
    "Maximum Rotation",
    "Final Approach",
    "Orbit Master",
)


LEVEL_DESCRIPTIONS: Final[
    tuple[str, ...]
] = (
    "Learn to rotate around the cylinder.",
    "Avoid a basic line of barriers.",
    "Choose between two safe routes.",
    "Practice moving across several lanes.",
    "Complete your first full obstacle course.",

    "The cylinder begins moving faster.",
    "Tall barriers narrow your view.",
    "Moving obstacles enter the course.",
    "Safe lanes change more quickly.",
    "Survive the first speed trial.",

    "Obstacles begin combining into patterns.",
    "Two openings may not stay safe.",
    "React to sudden direction changes.",
    "Follow a winding spiral route.",
    "Spacing becomes less forgiving.",

    "Rotating walls enter the course.",
    "Choose the correct split quickly.",
    "Pass through narrow openings.",
    "Moving barriers create a maze.",
    "Finish the second major trial.",

    "Slalom sections become faster.",
    "Energy spikes punish slow reactions.",
    "Spiral patterns change direction.",
    "Some openings are deceptive.",
    "Maintain control at higher speed.",

    "Pulse barriers change over time.",
    "Two spiral routes overlap.",
    "Walls move around the cylinder.",
    "Long sections leave little recovery time.",
    "Complete the third major trial.",

    "High speed becomes the normal pace.",
    "Laser gates enter the course.",
    "Openings close as you approach.",
    "Visual tricks hide the real route.",
    "Tracking obstacles react to movement.",

    "Fast reactions are required.",
    "Rotating obstacles appear together.",
    "Navigate a dense laser grid.",
    "Safe lanes are extremely narrow.",
    "Complete the fourth major trial.",

    "The extreme campaign begins.",
    "Tracking barriers attack in groups.",
    "Pulse obstacles form a moving maze.",
    "The cylinder route becomes unpredictable.",
    "Speed and density approach their limits.",

    "Survive a continuous spiral gauntlet.",
    "Every side of the cylinder is dangerous.",
    "Rotate precisely at maximum speed.",
    "Face every obstacle type together.",
    "Complete the final impossible course.",
)


def level_seed(
    level_number: int,
) -> int:
    """
    Return a stable seed for a campaign level.
    """

    return (
        82_451
        + level_number * 91_127
    )


def available_obstacle_types(
    level_number: int,
) -> list[str]:
    """
    Return obstacle types unlocked for a campaign level.
    """

    available: list[str] = []

    for obstacle_type, definition in (
        OBSTACLE_DEFINITIONS.items()
    ):
        if (
            obstacle_type
            == OBSTACLE_FINISH_LINE
        ):
            continue

        if (
            definition.minimum_level
            <= level_number
        ):
            available.append(
                obstacle_type
            )

    if not available:
        available.append(
            OBSTACLE_BLOCK
        )

    return available


def choose_pattern_builder(
    level_number: int,
    complexity: int,
    rng: random.Random,
):
    """
    Choose a suitable pattern builder.
    """

    choices = [
        build_single_pattern,
        build_double_pattern,
    ]

    if complexity >= 2:
        choices.extend(
            [
                build_triple_pattern,
                build_wall_pattern,
            ]
        )

    if complexity >= 3:
        choices.extend(
            [
                build_zigzag_pattern,
                build_slalom_pattern,
            ]
        )

    if complexity >= 4:
        choices.append(
            build_spiral_pattern
        )

    if complexity >= 5:
        choices.append(
            build_moving_pattern
        )

    if complexity >= 6:
        choices.append(
            build_rotating_pattern
        )

    if complexity >= 7:
        choices.append(
            build_gauntlet_pattern
        )

    return rng.choice(choices)


def build_generated_pattern(
    level_number: int,
    start_distance: float,
    pattern_index: int,
    rng: random.Random,
) -> LevelPattern:
    """
    Build one deterministic campaign pattern.
    """

    tier = get_level_tier(
        level_number
    )

    complexity = tier.pattern_complexity

    builder = choose_pattern_builder(
        level_number,
        complexity,
        rng,
    )

    starting_lane = rng.randrange(
        CYLINDER_LANE_COUNT
    )

    difficulty = (
        1.0
        + level_number * 0.075
        + pattern_index * 0.04
    )

    available_types = (
        available_obstacle_types(
            level_number
        )
    )

    ordinary_types = [
        obstacle_type
        for obstacle_type in available_types
        if obstacle_type
        in {
            OBSTACLE_BLOCK,
            OBSTACLE_WIDE_BLOCK,
            OBSTACLE_TALL_BLOCK,
            OBSTACLE_SPIKE,
        }
    ]

    obstacle_type = (
        rng.choice(ordinary_types)
        if ordinary_types
        else OBSTACLE_BLOCK
    )

    if builder is build_single_pattern:
        return build_single_pattern(
            start_distance,
            starting_lane,
            obstacle_type=obstacle_type,
            difficulty=difficulty,
        )

    if builder is build_double_pattern:
        return build_double_pattern(
            start_distance,
            starting_lane,
            separation=rng.choice(
                [3, 4, 5]
            ),
            obstacle_type=obstacle_type,
            difficulty=difficulty,
        )

    if builder is build_triple_pattern:
        return build_triple_pattern(
            start_distance,
            starting_lane,
            spacing=rng.choice(
                [2, 3, 4]
            ),
            obstacle_type=obstacle_type,
            difficulty=difficulty,
        )

    if builder is build_wall_pattern:
        gap_width = (
            3
            if level_number <= 8
            else 2
            if level_number <= 30
            else 1
        )

        return build_wall_pattern(
            start_distance,
            starting_lane,
            gap_width=gap_width,
            difficulty=difficulty,
        )

    if builder is build_zigzag_pattern:
        return build_zigzag_pattern(
            start_distance,
            starting_lane,
            steps=min(
                8,
                4 + complexity,
            ),
            lane_step=rng.choice(
                [1, 2, 3]
            ),
            spacing=max(
                7.0,
                12.0
                - level_number * 0.07,
            ),
            obstacle_type=obstacle_type,
            difficulty=difficulty,
        )

    if builder is build_slalom_pattern:
        return build_slalom_pattern(
            start_distance,
            starting_lane,
            steps=min(
                10,
                5 + complexity,
            ),
            spacing=max(
                7.0,
                11.0
                - level_number * 0.06,
            ),
            difficulty=difficulty,
        )

    if builder is build_spiral_pattern:
        return build_spiral_pattern(
            start_distance,
            starting_lane,
            steps=min(
                13,
                7 + complexity,
            ),
            lane_step=rng.choice(
                [-2, -1, 1, 2]
            ),
            spacing=max(
                6.5,
                10.0
                - level_number * 0.04,
            ),
            obstacle_type=obstacle_type,
            difficulty=difficulty,
        )

    if builder is build_moving_pattern:
        return build_moving_pattern(
            start_distance,
            starting_lane,
            obstacle_count=min(
                7,
                3 + complexity // 2,
            ),
            spacing=max(
                8.0,
                13.0
                - level_number * 0.05,
            ),
            movement_amount=min(
                5.0,
                2.0
                + level_number / 16.0,
            ),
            movement_speed=min(
                2.0,
                0.75
                + level_number / 55.0,
            ),
            difficulty=difficulty,
        )

    if builder is build_rotating_pattern:
        return build_rotating_pattern(
            start_distance,
            starting_lane,
            obstacle_count=min(
                7,
                3 + complexity // 2,
            ),
            spacing=max(
                8.0,
                13.0
                - level_number * 0.05,
            ),
            rotation_speed=min(
                90.0,
                34.0
                + level_number * 0.9,
            ),
            difficulty=difficulty,
        )

    return build_gauntlet_pattern(
        start_distance,
        starting_lane,
        difficulty=difficulty,
    )


def calculate_pattern_count(
    level_number: int,
    level_length: float,
) -> int:
    """
    Calculate how many sections belong in a level.
    """

    tier = get_level_tier(
        level_number
    )

    approximate_count = int(
        level_length
        / max(
            55.0,
            tier.obstacle_gap * 2.1,
        )
    )

    return max(
        4,
        min(
            24,
            approximate_count,
        ),
    )


def calculate_level_acceleration(
    level_number: int,
) -> float:
    """
    Calculate speed increase within a level.
    """

    return (
        0.0025
        + level_number * 0.00018
    )


def calculate_level_max_speed(
    level_number: int,
    starting_speed: float,
) -> float:
    """
    Calculate maximum speed reached in a level.
    """

    tier = get_level_tier(
        level_number
    )

    return max(
        starting_speed,
        tier.maximum_speed,
    )


def calculate_medal_distances(
    level_length: float,
) -> tuple[float, float, float]:
    """
    Distances used by future medal and progress displays.
    """

    return (
        level_length * 0.55,
        level_length * 0.78,
        level_length,
    )


def build_campaign_level(
    level_number: int,
) -> LevelDefinition:
    """
    Create one deterministic campaign level.
    """

    if not (
        1
        <= level_number
        <= TOTAL_LEVELS
    ):
        raise ValueError(
            f"Level must be between 1 and {TOTAL_LEVELS}."
        )

    rng = random.Random(
        level_seed(level_number)
    )

    tier = get_level_tier(
        level_number
    )

    level_length = calculate_level_length(
        level_number
    )

    starting_speed = calculate_level_speed(
        level_number
    )

    maximum_speed = calculate_level_max_speed(
        level_number,
        starting_speed,
    )

    pattern_count = calculate_pattern_count(
        level_number,
        level_length,
    )

    patterns: list[LevelPattern] = []

    current_distance = 42.0

    maximum_pattern_end = (
        level_length
        - LEVEL_FINISH_LINE_DISTANCE
        - 35.0
    )

    for pattern_index in range(
        pattern_count
    ):
        if current_distance >= maximum_pattern_end:
            break

        if (
            level_number % 10 == 0
            and pattern_index
            == pattern_count - 1
        ):
            level_pattern = build_boss_pattern(
                current_distance,
                level_number,
            )

        else:
            level_pattern = build_generated_pattern(
                level_number,
                current_distance,
                pattern_index,
                rng,
            )

        validate_pattern(
            level_pattern
        )

        patterns.append(
            level_pattern
        )

        spacing_variation = rng.uniform(
            -2.5,
            4.5,
        )

        current_distance += (
            level_pattern.length
            + max(
                7.0,
                tier.obstacle_gap
                + spacing_variation,
            )
        )

    finish_pattern = pattern(
        pattern_type=PATTERN_WALL,
        name="Finish Line",
        start_distance=max(
            1.0,
            level_length
            - LEVEL_FINISH_LINE_DISTANCE,
        ),
        length=LEVEL_FINISH_LINE_DISTANCE,
        obstacles=(
            obstacle(
                OBSTACLE_FINISH_LINE,
                1.0,
                0,
                lane_span=(
                    CYLINDER_LANE_COUNT - 1
                ),
            ),
        ),
        safe_lanes=range(
            CYLINDER_LANE_COUNT
        ),
        difficulty=0.0,
    )

    patterns.append(
        finish_pattern
    )

    background_theme = (
        "neon_blue"
        if level_number <= 10
        else "solar_orange"
        if level_number <= 20
        else "plasma_purple"
        if level_number <= 30
        else "reactor_red"
        if level_number <= 40
        else "void_white"
    )

    cylinder_theme = (
        "neon_blue"
        if level_number <= 10
        else "electric_green"
        if level_number <= 20
        else "plasma_purple"
        if level_number <= 30
        else "warning_red"
        if level_number <= 40
        else "final_core"
    )

    music_track = (
        "gameplay_theme.ogg"
        if level_number <= 30
        else "extreme_theme.ogg"
    )

    return LevelDefinition(
        number=level_number,
        name=LEVEL_NAMES[
            level_number - 1
        ],
        description=LEVEL_DESCRIPTIONS[
            level_number - 1
        ],
        tier_name=tier.name,
        length=level_length,
        starting_speed=starting_speed,
        maximum_speed=maximum_speed,
        acceleration=calculate_level_acceleration(
            level_number
        ),
        patterns=tuple(patterns),
        background_theme=background_theme,
        cylinder_theme=cylinder_theme,
        music_track=music_track,
        allow_powerups=True,
        recommended_difficulty=(
            tier.pattern_complexity
        ),
        medal_distances=(
            calculate_medal_distances(
                level_length
            )
        ),
        metadata={
            "game_mode": MODE_LEVELS,
            "seed": level_seed(
                level_number
            ),
            "pattern_count": len(
                patterns
            ),
            "is_milestone": (
                level_number % 5 == 0
            ),
            "is_boss_level": (
                level_number % 10 == 0
            ),
            "first_unlocked": (
                level_number
                == FIRST_UNLOCKED_LEVEL
            ),
        },
    )


# ============================================================
# COMPLETE 50-LEVEL CAMPAIGN
# ============================================================

CAMPAIGN_LEVELS: Final[
    tuple[LevelDefinition, ...]
] = tuple(
    build_campaign_level(
        level_number
    )
    for level_number in range(
        1,
        TOTAL_LEVELS + 1,
    )
)


CAMPAIGN_LEVEL_MAP: Final[
    dict[int, LevelDefinition]
] = {
    level.number: level
    for level in CAMPAIGN_LEVELS
}


# ============================================================
# CAMPAIGN ACCESS HELPERS
# ============================================================

def get_level(
    level_number: int,
) -> LevelDefinition:
    """
    Return one campaign level.
    """

    try:
        return CAMPAIGN_LEVEL_MAP[
            int(level_number)
        ]

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Unknown campaign level: {level_number}"
        ) from error


def get_next_level(
    level_number: int,
) -> LevelDefinition | None:
    """
    Return the following campaign level.
    """

    next_number = int(
        level_number
    ) + 1

    return CAMPAIGN_LEVEL_MAP.get(
        next_number
    )


def get_previous_level(
    level_number: int,
) -> LevelDefinition | None:
    """
    Return the previous campaign level.
    """

    previous_number = int(
        level_number
    ) - 1

    return CAMPAIGN_LEVEL_MAP.get(
        previous_number
    )


def get_unlocked_levels(
    highest_unlocked_level: int,
) -> tuple[LevelDefinition, ...]:
    """
    Return campaign levels currently available to a player.
    """

    cleaned_highest = int(
        clamp(
            highest_unlocked_level,
            FIRST_UNLOCKED_LEVEL,
            TOTAL_LEVELS,
        )
    )

    return tuple(
        level
        for level in CAMPAIGN_LEVELS
        if level.number
        <= cleaned_highest
    )


def is_level_unlocked(
    level_number: int,
    highest_unlocked_level: int,
) -> bool:
    """
    Check whether a campaign level is unlocked.
    """

    return (
        FIRST_UNLOCKED_LEVEL
        <= level_number
        <= min(
            TOTAL_LEVELS,
            highest_unlocked_level,
        )
    )


def unlock_level_after_completion(
    completed_level: int,
    highest_unlocked_level: int,
) -> int:
    """
    Calculate the new highest unlocked level.
    """

    if completed_level < 1:
        return max(
            FIRST_UNLOCKED_LEVEL,
            highest_unlocked_level,
        )

    return min(
        TOTAL_LEVELS,
        max(
            highest_unlocked_level,
            completed_level + 1,
        ),
    )


def level_completion_percentage(
    distance_metres: float,
    level_number: int,
) -> float:
    """
    Return a level completion percentage.
    """

    level = get_level(
        level_number
    )

    if level.length <= 0:
        return 100.0

    return clamp(
        (
            distance_metres
            / level.length
        )
        * 100.0,
        0.0,
        100.0,
    )


def obstacle_world_angle(
    pattern_obstacle: PatternObstacle,
) -> float:
    """
    Convert an obstacle lane to its starting world angle.
    """

    return lane_to_angle(
        pattern_obstacle.lane
    )


def expanded_pattern_obstacles(
    level_pattern: LevelPattern,
) -> tuple[PatternObstacle, ...]:
    """
    Expand repeated pattern data into individual obstacles.
    """

    expanded: list[PatternObstacle] = []

    for repeat_index in range(
        level_pattern.repeat_count
    ):
        distance_shift = (
            repeat_index
            * level_pattern.repeat_spacing
        )

        rotation_shift = (
            repeat_index
            * level_pattern.rotate_each_repeat
        )

        mirror = (
            level_pattern.mirror_each_repeat
            and repeat_index % 2 == 1
        )

        for source in level_pattern.obstacles:
            lane = source.lane

            if mirror:
                lane = normalize_lane(
                    -lane
                )

            lane = normalize_lane(
                lane + rotation_shift
            )

            expanded.append(
                PatternObstacle(
                    obstacle_type=source.obstacle_type,
                    distance_offset=(
                        source.distance_offset
                        + distance_shift
                    ),
                    lane=lane,
                    lane_span=source.lane_span,
                    movement_amount=(
                        source.movement_amount
                    ),
                    movement_speed=(
                        source.movement_speed
                    ),
                    rotation_speed=(
                        source.rotation_speed
                    ),
                    phase_offset=(
                        source.phase_offset
                        + repeat_index * 0.45
                    ),
                    fake=source.fake,
                    metadata=dict(
                        source.metadata
                    ),
                )
            )

    return tuple(expanded)


def all_level_obstacles(
    level_number: int,
) -> tuple[
    tuple[float, PatternObstacle],
    ...
]:
    """
    Return every obstacle with its absolute level distance.
    """

    level = get_level(
        level_number
    )

    placed: list[
        tuple[float, PatternObstacle]
    ] = []

    for level_pattern in level.patterns:
        for item in expanded_pattern_obstacles(
            level_pattern
        ):
            absolute_distance = (
                level_pattern.start_distance
                + item.distance_offset
            )

            placed.append(
                (
                    absolute_distance,
                    item,
                )
            )

    placed.sort(
        key=lambda pair: pair[0]
    )

    return tuple(placed)


def validate_campaign() -> None:
    """
    Validate all campaign data during development.
    """

    if len(CAMPAIGN_LEVELS) != TOTAL_LEVELS:
        raise ValueError(
            "Campaign does not contain "
            f"{TOTAL_LEVELS} levels."
        )

    for expected_number, level in enumerate(
        CAMPAIGN_LEVELS,
        start=1,
    ):
        if level.number != expected_number:
            raise ValueError(
                "Campaign level numbering is invalid."
            )

        if level.length <= 0:
            raise ValueError(
                f"Level {level.number} has no length."
            )

        if not level.patterns:
            raise ValueError(
                f"Level {level.number} has no patterns."
            )

        for level_pattern in level.patterns:
            validate_pattern(
                level_pattern
            )


# Validate the complete campaign when this module loads.
validate_campaign()