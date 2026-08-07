from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Callable

from config import (
    CAMPAIGN_LEVELS, CYAN, GREEN, LANE_ANGLE, OBSTACLE_BAR, OBSTACLE_CROSS,
    OBSTACLE_DOUBLE_GATE, OBSTACLE_FAN, OBSTACLE_FINISH, OBSTACLE_GATE,
    OBSTACLE_PULSE, OBSTACLE_SHUTTER, OBSTACLE_SLIDER, OBSTACLE_ZIGZAG,
    ORANGE, PINK, PURPLE, RED, TUNNEL_THEMES, WHITE, YELLOW, clamp,
    normalize_angle,
)
from entities import TunnelObstacle


@dataclass(frozen=True)
class LevelDefinition:
    number: int
    name: str
    description: str
    theme: str
    length: float
    start_speed: float
    max_speed: float
    acceleration: float
    obstacle_gap: float
    difficulty: int
    seed: int
    obstacles: tuple[TunnelObstacle, ...]


LEVEL_NAMES = (
    "First Light", "Open Road", "Single Shift", "Turning Point", "Warmup Trial",
    "Second Current", "Twin Gates", "Moving Window", "Crossing Lines", "Velocity One",
    "Blue Spiral", "Broken Circle", "Swing Gate", "Double Choice", "Pressure Ring",
    "Rotating Core", "Fast Split", "Narrow Orbit", "Sliding Sector", "Velocity Two",
    "Solar Entry", "Three Blades", "Closing Window", "False Rhythm", "Heat Line",
    "Pulse Sector", "Fan Chamber", "Shutter Run", "Zigzag Core", "Velocity Three",
    "Plasma Entry", "Cross Storm", "Rapid Slider", "Tight Double", "No Rest",
    "Moving Cross", "Pulse Maze", "Fast Shutter", "Spiral Storm", "Velocity Four",
    "Reactor Entry", "Blade Field", "Closing Spiral", "Redline", "Core Collapse",
    "Void Gate", "No Safe Rhythm", "Maximum Velocity", "Final Approach", "Orbit Master",
)

LEVEL_DESCRIPTIONS = tuple(
    "Learn the tunnel and survive the obstacle sequence."
    if index < 5 else
    "React to faster moving openings and rotating hazards."
    if index < 20 else
    "Combine precise movement with high speed and narrow gaps."
    if index < 40 else
    "Survive an extreme course using every skill you learned."
    for index in range(CAMPAIGN_LEVELS)
)


def gate(distance: float, angle: float, width: float, *, speed: float = 0.0, kind: str = OBSTACLE_GATE, colour=RED, movement=0.0, movement_speed=0.0, phase=0.0) -> TunnelObstacle:
    return TunnelObstacle(
        kind=kind,
        distance=distance,
        opening_angle=normalize_angle(angle),
        opening_width=width,
        rotation_speed=speed,
        movement_amplitude=movement,
        movement_speed=movement_speed,
        phase=phase,
        colour=colour,
        secondary_colour=WHITE,
        thickness=18.0,
    )


def blade(distance: float, angle: float, *, arms: int = 2, speed: float = 55.0, thickness: float = 22.0, colour=ORANGE, phase=0.0, kind: str = OBSTACLE_BAR) -> TunnelObstacle:
    return TunnelObstacle(
        kind=kind,
        distance=distance,
        opening_angle=normalize_angle(angle),
        rotation_speed=speed,
        phase=phase,
        colour=colour,
        secondary_colour=YELLOW,
        thickness=thickness,
        arms=arms,
    )


def finish(distance: float) -> TunnelObstacle:
    return TunnelObstacle(kind=OBSTACLE_FINISH, distance=distance, colour=GREEN)


def clone_obstacle(source: TunnelObstacle) -> TunnelObstacle:
    return TunnelObstacle(
        kind=source.kind,
        distance=source.distance,
        opening_angle=source.opening_angle,
        opening_width=source.opening_width,
        rotation_speed=source.rotation_speed,
        movement_amplitude=source.movement_amplitude,
        movement_speed=source.movement_speed,
        phase=source.phase,
        colour=source.colour,
        secondary_colour=source.secondary_colour,
        thickness=source.thickness,
        arms=source.arms,
        metadata=dict(source.metadata),
    )


def build_level(number: int) -> LevelDefinition:
    rng = random.Random(901_337 + number * 17_311)
    tier = (number - 1) // 10
    within = (number - 1) % 10

    theme = ("neon", "solar", "plasma", "reactor", "void")[tier]
    difficulty = number
    start_speed = 23.0 + tier * 7.5 + within * 0.72
    max_speed = start_speed + 5.0 + tier * 3.0 + within * 0.4
    acceleration = 0.004 + number * 0.00018
    obstacle_gap = max(9.0, 27.0 - number * 0.31)
    target_length = 260.0 + number * 23.0 + tier * 55.0

    obstacles: list[TunnelObstacle] = []
    distance = 55.0
    safe_angle = 270.0
    pattern_index = 0

    while distance < target_length - 35.0:
        safe_angle = normalize_angle(safe_angle + rng.choice((-75, -50, -35, 35, 50, 75)))
        unlock = min(9, 1 + number // 5)
        choice = rng.randrange(unlock)

        if choice <= 1:
            width = max(36.0, 100.0 - number * 1.0)
            obstacles.append(gate(distance, safe_angle, width, colour=RED))
        elif choice == 2:
            width = max(32.0, 88.0 - number * 0.8)
            obstacles.append(gate(distance, safe_angle, width, kind=OBSTACLE_DOUBLE_GATE, colour=PURPLE))
        elif choice == 3:
            obstacles.append(blade(distance, safe_angle + 90, arms=2, speed=35 + number * 1.1, thickness=18 + tier * 2, colour=ORANGE))
        elif choice == 4:
            obstacles.append(blade(distance, safe_angle, arms=4, speed=(-1 if pattern_index % 2 else 1) * (30 + number), thickness=14 + tier * 2, colour=PINK, kind=OBSTACLE_CROSS))
        elif choice == 5:
            width = max(30.0, 82.0 - number * 0.7)
            obstacles.append(gate(distance, safe_angle, width, kind=OBSTACLE_SLIDER, colour=CYAN, movement=min(80.0, 25 + number), movement_speed=0.8 + number * 0.025, phase=pattern_index * 0.7))
        elif choice == 6:
            width = max(28.0, 76.0 - number * 0.6)
            obstacles.append(gate(distance, safe_angle, width, kind=OBSTACLE_SHUTTER, colour=YELLOW, speed=(-1 if pattern_index % 2 else 1) * (12 + number * 0.7), phase=pattern_index))
        elif choice == 7:
            obstacles.append(blade(distance, safe_angle, arms=min(7, 3 + tier), speed=26 + number * 0.9, thickness=11 + tier * 1.5, colour=PURPLE, kind=OBSTACLE_FAN))
        else:
            width = max(25.0, 68.0 - number * 0.45)
            obstacles.append(gate(distance, safe_angle, width, kind=OBSTACLE_PULSE if pattern_index % 2 else OBSTACLE_ZIGZAG, colour=WHITE, speed=(number * 0.65), movement=20 + tier * 10, movement_speed=1.2 + tier * 0.25, phase=pattern_index * 0.5))

        pattern_index += 1
        distance += obstacle_gap + rng.uniform(-2.5, 4.5)

        # Milestone levels contain short dense finales.
        if number % 10 == 0 and target_length - 180 < distance < target_length - 45:
            for finale in range(4 + tier):
                safe_angle = normalize_angle(safe_angle + (55 if finale % 2 == 0 else -70))
                distance += max(7.5, obstacle_gap * 0.72)
                if finale % 2:
                    obstacles.append(blade(distance, safe_angle, arms=4 + min(2, tier), speed=60 + number, thickness=13 + tier, colour=WHITE, kind=OBSTACLE_FAN))
                else:
                    obstacles.append(gate(distance, safe_angle, max(25.0, 62 - tier * 6), kind=OBSTACLE_SHUTTER, colour=RED, speed=20 + number))
            break

    finish_distance = max(target_length, distance + 28.0)
    obstacles.append(finish(finish_distance))

    return LevelDefinition(
        number=number,
        name=LEVEL_NAMES[number - 1],
        description=LEVEL_DESCRIPTIONS[number - 1],
        theme=theme,
        length=finish_distance,
        start_speed=start_speed,
        max_speed=max_speed,
        acceleration=acceleration,
        obstacle_gap=obstacle_gap,
        difficulty=difficulty,
        seed=901_337 + number * 17_311,
        obstacles=tuple(obstacles),
    )


CAMPAIGN = tuple(build_level(number) for number in range(1, CAMPAIGN_LEVELS + 1))
LEVEL_MAP = {level.number: level for level in CAMPAIGN}


def get_level(number: int) -> LevelDefinition:
    if number not in LEVEL_MAP:
        raise ValueError(f"Unknown level: {number}")
    return LEVEL_MAP[number]


def instantiate_level(number: int) -> list[TunnelObstacle]:
    return [clone_obstacle(obstacle) for obstacle in get_level(number).obstacles]


class EndlessGenerator:
    def __init__(self) -> None:
        self.random = random.Random()
        self.next_distance = 75.0
        self.safe_angle = 270.0
        self.pattern_count = 0

    def reset(self, seed: int | None = None) -> None:
        self.random.seed(seed)
        self.next_distance = 75.0
        self.safe_angle = 270.0
        self.pattern_count = 0

    def difficulty(self, travelled: float) -> float:
        return clamp(1.0 + travelled / 145.0, 1.0, 30.0)

    def gap(self, travelled: float) -> float:
        return clamp(30.0 - travelled / 180.0, 8.5, 30.0)

    def generate_section(self, travelled: float) -> list[TunnelObstacle]:
        difficulty = self.difficulty(travelled)
        gap = self.gap(travelled)
        unlocked = min(9, 2 + int(difficulty // 2.8))
        section_count = min(8, 2 + int(difficulty // 4.0))
        result: list[TunnelObstacle] = []

        for index in range(section_count):
            self.safe_angle = normalize_angle(
                self.safe_angle + self.random.choice((-80, -55, -35, 35, 55, 80))
            )
            choice = self.random.randrange(unlocked)
            distance = self.next_distance + index * gap
            width = clamp(94.0 - difficulty * 2.0, 25.0, 94.0)

            if choice <= 1:
                result.append(gate(distance, self.safe_angle, width, colour=RED))
            elif choice == 2:
                result.append(gate(distance, self.safe_angle, width * 0.9, kind=OBSTACLE_DOUBLE_GATE, colour=PURPLE))
            elif choice == 3:
                result.append(blade(distance, self.safe_angle + 90, arms=2, speed=40 + difficulty * 4, thickness=18, colour=ORANGE))
            elif choice == 4:
                result.append(gate(distance, self.safe_angle, width * 0.88, kind=OBSTACLE_SLIDER, colour=CYAN, movement=min(85, 25 + difficulty * 3), movement_speed=0.8 + difficulty * 0.05, phase=self.pattern_count))
            elif choice == 5:
                result.append(gate(distance, self.safe_angle, width * 0.82, kind=OBSTACLE_SHUTTER, colour=YELLOW, speed=18 + difficulty * 2, phase=index))
            elif choice == 6:
                result.append(blade(distance, self.safe_angle, arms=min(7, 3 + int(difficulty // 7)), speed=30 + difficulty * 3, thickness=13, colour=PINK, kind=OBSTACLE_FAN))
            elif choice == 7:
                result.append(blade(distance, self.safe_angle, arms=4, speed=(-1 if index % 2 else 1) * (35 + difficulty * 3), thickness=14, colour=WHITE, kind=OBSTACLE_CROSS))
            else:
                result.append(gate(distance, self.safe_angle, width * 0.78, kind=OBSTACLE_PULSE, colour=WHITE, speed=difficulty * 2, movement=20 + difficulty * 2, movement_speed=1.0 + difficulty * 0.06, phase=index))

        self.next_distance += section_count * gap + gap * 0.9
        self.pattern_count += 1
        return result
