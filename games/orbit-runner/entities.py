from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Any, Iterable

import pygame

from config import (
    BLACK,
    BLUE,
    CRASH_SHAKE_DURATION_MS,
    CRASH_SHAKE_STRENGTH,
    CYAN,
    CYLINDER_CENTER_X,
    CYLINDER_CURVE_STRENGTH,
    CYLINDER_FAR_RADIUS,
    CYLINDER_FULL_ROTATION,
    CYLINDER_GLOW_COLOUR,
    CYLINDER_HORIZON_Y,
    CYLINDER_LANE_ANGLE,
    CYLINDER_LANE_COUNT,
    CYLINDER_NEAR_CLIP_DISTANCE,
    CYLINDER_NEAR_RADIUS,
    CYLINDER_PERSPECTIVE_POWER,
    CYLINDER_PLAYER_Y,
    CYLINDER_ROTATION_ACCELERATION,
    CYLINDER_ROTATION_FRICTION,
    CYLINDER_ROTATION_SPEED,
    CYLINDER_VISIBLE_DISTANCE,
    DARK_BLUE,
    DARK_GREY,
    DISTANCE_FOG_END,
    DISTANCE_FOG_START,
    ENABLE_GLOW_EFFECTS,
    ENABLE_PARTICLES,
    ENABLE_SCREEN_SHAKE,
    GAME_HEIGHT,
    GAME_WIDTH,
    GREEN,
    LIGHT_BLUE,
    LIGHT_GREY,
    MAX_PARTICLES,
    MAX_TRAIL_POINTS,
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
    ORANGE,
    PLAYER_COLLISION_DEPTH,
    PLAYER_COLLISION_WIDTH,
    PLAYER_COLOUR,
    PLAYER_HIGHLIGHT_COLOUR,
    PLAYER_SCREEN_HEIGHT,
    PLAYER_SCREEN_WIDTH,
    PLAYER_STARTING_ANGLE,
    PLAYER_TRAIL_COLOUR,
    PLAYER_TRAIL_LENGTH,
    PURPLE,
    RED,
    SHIELD_DURATION_MS,
    SLOW_TIME_DURATION_MS,
    SLOW_TIME_SPEED_MULTIPLIER,
    SCORE_MULTIPLIER_DURATION_MS,
    SPACE_BLACK,
    WHITE,
    YELLOW,
    clamp,
    lane_to_angle,
    normalize_angle,
    shortest_angle_difference,
)

from levels import (
    PatternObstacle,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def colour_lerp(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    """
    Blend between two RGB colours.
    """

    amount = clamp(
        amount,
        0.0,
        1.0,
    )

    return (
        round(
            first[0]
            + (
                second[0]
                - first[0]
            )
            * amount
        ),
        round(
            first[1]
            + (
                second[1]
                - first[1]
            )
            * amount
        ),
        round(
            first[2]
            + (
                second[2]
                - first[2]
            )
            * amount
        ),
    )


def scale_colour(
    colour: tuple[int, int, int],
    brightness: float,
) -> tuple[int, int, int]:
    """
    Multiply an RGB colour by a brightness value.
    """

    brightness = max(
        0.0,
        float(brightness),
    )

    return (
        int(
            clamp(
                colour[0] * brightness,
                0,
                255,
            )
        ),
        int(
            clamp(
                colour[1] * brightness,
                0,
                255,
            )
        ),
        int(
            clamp(
                colour[2] * brightness,
                0,
                255,
            )
        ),
    )


def angular_overlap(
    first_angle: float,
    first_width: float,
    second_angle: float,
    second_width: float,
) -> bool:
    """
    Check whether two angular areas overlap.
    """

    difference = abs(
        shortest_angle_difference(
            first_angle,
            second_angle,
        )
    )

    combined_half_width = (
        first_width
        + second_width
    ) / 2.0

    return (
        difference
        <= combined_half_width
    )


def circular_lane_distance(
    first_lane: float,
    second_lane: float,
) -> float:
    """
    Return the shortest lane distance around the cylinder.
    """

    raw_difference = abs(
        first_lane - second_lane
    )

    return min(
        raw_difference,
        CYLINDER_LANE_COUNT
        - raw_difference,
    )


def angle_to_radians(
    angle: float,
) -> float:
    return math.radians(
        normalize_angle(angle)
    )


# ============================================================
# CYLINDER PROJECTION
# ============================================================

@dataclass(frozen=True)
class ProjectionResult:
    """
    A projected point on the cylinder.
    """

    visible: bool

    x: float
    y: float

    scale: float
    radius: float

    depth_factor: float
    brightness: float

    front_factor: float

    angle: float
    distance: float


class CylinderProjector:
    """
    Converts cylinder world coordinates into screen coordinates.

    World coordinates use:

    angle:
        Position around the cylinder.

    distance:
        Distance ahead of the player.

    The player remains near the bottom of the screen while
    obstacles approach from the horizon.
    """

    def __init__(self):
        self.center_x = float(
            CYLINDER_CENTER_X
        )

        self.horizon_y = float(
            CYLINDER_HORIZON_Y
        )

        self.player_y = float(
            CYLINDER_PLAYER_Y
        )

        self.near_radius = float(
            CYLINDER_NEAR_RADIUS
        )

        self.far_radius = float(
            CYLINDER_FAR_RADIUS
        )

        self.visible_distance = float(
            CYLINDER_VISIBLE_DISTANCE
        )

        self.rotation = 0.0

    def reset(self) -> None:
        self.rotation = 0.0

    def set_rotation(
        self,
        rotation: float,
    ) -> None:
        self.rotation = normalize_angle(
            rotation
        )

    def distance_factor(
        self,
        distance: float,
    ) -> float:
        """
        Return 0 near the player and 1 at the horizon.
        """

        normalized = clamp(
            distance
            / self.visible_distance,
            0.0,
            1.0,
        )

        return (
            normalized
            ** CYLINDER_PERSPECTIVE_POWER
        )

    def radius_at_distance(
        self,
        distance: float,
    ) -> float:
        factor = self.distance_factor(
            distance
        )

        return (
            self.near_radius
            + (
                self.far_radius
                - self.near_radius
            )
            * factor
        )

    def screen_y_at_distance(
        self,
        distance: float,
    ) -> float:
        factor = self.distance_factor(
            distance
        )

        curved_factor = (
            factor
            ** CYLINDER_CURVE_STRENGTH
        )

        return (
            self.player_y
            + (
                self.horizon_y
                - self.player_y
            )
            * curved_factor
        )

    def scale_at_distance(
        self,
        distance: float,
    ) -> float:
        factor = self.distance_factor(
            distance
        )

        return max(
            0.02,
            1.0 - factor,
        )

    def fog_amount(
        self,
        distance: float,
    ) -> float:
        if distance <= DISTANCE_FOG_START:
            return 0.0

        if distance >= DISTANCE_FOG_END:
            return 1.0

        return (
            distance
            - DISTANCE_FOG_START
        ) / (
            DISTANCE_FOG_END
            - DISTANCE_FOG_START
        )

    def project(
        self,
        world_angle: float,
        distance: float,
        radial_height: float = 0.0,
    ) -> ProjectionResult:
        """
        Project one point from cylinder space to the game screen.
        """

        if (
            distance
            < -CYLINDER_NEAR_CLIP_DISTANCE
            or distance
            > self.visible_distance
        ):
            return ProjectionResult(
                visible=False,
                x=0.0,
                y=0.0,
                scale=0.0,
                radius=0.0,
                depth_factor=1.0,
                brightness=0.0,
                front_factor=0.0,
                angle=world_angle,
                distance=distance,
            )

        depth_factor = self.distance_factor(
            max(
                0.0,
                distance,
            )
        )

        radius = self.radius_at_distance(
            max(
                0.0,
                distance,
            )
        )

        scale = self.scale_at_distance(
            max(
                0.0,
                distance,
            )
        )

        screen_y = self.screen_y_at_distance(
            max(
                0.0,
                distance,
            )
        )

        relative_angle = normalize_angle(
            world_angle
            + self.rotation
        )

        radians = angle_to_radians(
            relative_angle
        )

        horizontal_component = math.sin(
            radians
        )

        vertical_component = math.cos(
            radians
        )

        x = (
            self.center_x
            + horizontal_component
            * radius
        )

        surface_y_offset = (
            vertical_component
            * radius
            * 0.18
        )

        height_offset = (
            radial_height
            * 62.0
            * scale
        )

        y = (
            screen_y
            - surface_y_offset
            - height_offset
        )

        front_factor = (
            vertical_component
            + 1.0
        ) / 2.0

        fog = self.fog_amount(
            distance
        )

        brightness = (
            0.38
            + front_factor * 0.62
        ) * (
            1.0 - fog * 0.72
        )

        visible = (
            -radius * 1.25
            <= x - self.center_x
            <= radius * 1.25
        )

        return ProjectionResult(
            visible=visible,
            x=x,
            y=y,
            scale=scale,
            radius=radius,
            depth_factor=depth_factor,
            brightness=brightness,
            front_factor=front_factor,
            angle=relative_angle,
            distance=distance,
        )

    def project_lane(
        self,
        lane: int,
        distance: float,
        radial_height: float = 0.0,
    ) -> ProjectionResult:
        return self.project(
            lane_to_angle(lane),
            distance,
            radial_height,
        )


# ============================================================
# CYLINDER ROTATION CONTROLLER
# ============================================================

class CylinderController:
    """
    Handles smooth cylinder rotation.

    The player appears stable while the cylinder and obstacles
    rotate around them.
    """

    def __init__(self):
        self.rotation = 0.0
        self.rotation_velocity = 0.0

        self.input_direction = 0

        self.enabled = True

    def reset(self) -> None:
        self.rotation = 0.0
        self.rotation_velocity = 0.0
        self.input_direction = 0

    def set_input(
        self,
        direction: int,
    ) -> None:
        self.input_direction = int(
            clamp(
                direction,
                -1,
                1,
            )
        )

    def update(
        self,
        delta_time: float,
    ) -> None:
        if not self.enabled:
            self.rotation_velocity = 0.0
            return

        target_velocity = (
            self.input_direction
            * CYLINDER_ROTATION_SPEED
        )

        acceleration_amount = (
            CYLINDER_ROTATION_ACCELERATION
            * delta_time
        )

        if self.rotation_velocity < target_velocity:
            self.rotation_velocity = min(
                target_velocity,
                self.rotation_velocity
                + acceleration_amount,
            )

        elif self.rotation_velocity > target_velocity:
            self.rotation_velocity = max(
                target_velocity,
                self.rotation_velocity
                - acceleration_amount,
            )

        if self.input_direction == 0:
            friction_amount = (
                CYLINDER_ROTATION_FRICTION
                * 60.0
                * delta_time
            )

            if self.rotation_velocity > 0:
                self.rotation_velocity = max(
                    0.0,
                    self.rotation_velocity
                    - friction_amount,
                )

            elif self.rotation_velocity < 0:
                self.rotation_velocity = min(
                    0.0,
                    self.rotation_velocity
                    + friction_amount,
                )

        self.rotation = normalize_angle(
            self.rotation
            + self.rotation_velocity
            * delta_time
        )

    def player_world_angle(self) -> float:
        """
        The world angle currently under the player.
        """

        return normalize_angle(
            -self.rotation
        )

    def player_lane(self) -> float:
        return (
            self.player_world_angle()
            / CYLINDER_LANE_ANGLE
        ) % CYLINDER_LANE_COUNT


# ============================================================
# PLAYER
# ============================================================

class Runner:
    """
    Player vehicle travelling along the cylinder.
    """

    def __init__(self):
        self.world_angle = PLAYER_STARTING_ANGLE

        self.width = float(
            PLAYER_COLLISION_WIDTH
        )

        self.collision_depth = float(
            PLAYER_COLLISION_DEPTH
        )

        self.screen_position = pygame.Vector2(
            CYLINDER_CENTER_X,
            CYLINDER_PLAYER_Y - 20,
        )

        self.alive = True
        self.finished = False

        self.crashed = False
        self.crash_time = 0

        self.invincible_until = 0

        self.shield_until = 0
        self.slow_time_until = 0
        self.score_multiplier_until = 0

        self.skin = "default"

        self.animation_time = 0.0
        self.lean_amount = 0.0

        self.trail_points: list[
            tuple[float, float, float]
        ] = []

        self.distance = 0.0

    def reset(
        self,
        world_angle: float = PLAYER_STARTING_ANGLE,
    ) -> None:
        self.world_angle = normalize_angle(
            world_angle
        )

        self.alive = True
        self.finished = False

        self.crashed = False
        self.crash_time = 0

        self.invincible_until = 0

        self.shield_until = 0
        self.slow_time_until = 0
        self.score_multiplier_until = 0

        self.animation_time = 0.0
        self.lean_amount = 0.0

        self.trail_points.clear()

        self.distance = 0.0

    def update(
        self,
        delta_time: float,
        current_time: int,
        rotation_velocity: float,
    ) -> None:
        self.animation_time += delta_time

        target_lean = clamp(
            rotation_velocity
            / max(
                1.0,
                CYLINDER_ROTATION_SPEED,
            ),
            -1.0,
            1.0,
        )

        self.lean_amount += (
            target_lean
            - self.lean_amount
        ) * min(
            1.0,
            delta_time * 10.0,
        )

        if not self.alive:
            return

        self.trail_points.append(
            (
                self.screen_position.x,
                self.screen_position.y,
                current_time,
            )
        )

        if len(self.trail_points) > MAX_TRAIL_POINTS:
            del self.trail_points[
                : len(self.trail_points)
                - MAX_TRAIL_POINTS
            ]

    def shield_active(
        self,
        current_time: int,
    ) -> bool:
        return (
            current_time
            < self.shield_until
        )

    def slow_time_active(
        self,
        current_time: int,
    ) -> bool:
        return (
            current_time
            < self.slow_time_until
        )

    def score_multiplier(
        self,
        current_time: int,
    ) -> int:
        if (
            current_time
            < self.score_multiplier_until
        ):
            return 2

        return 1

    def is_invincible(
        self,
        current_time: int,
    ) -> bool:
        return (
            self.shield_active(
                current_time
            )
            or current_time
            < self.invincible_until
        )

    def apply_shield(
        self,
        current_time: int,
    ) -> None:
        self.shield_until = max(
            self.shield_until,
            current_time,
        ) + SHIELD_DURATION_MS

    def apply_slow_time(
        self,
        current_time: int,
    ) -> None:
        self.slow_time_until = max(
            self.slow_time_until,
            current_time,
        ) + SLOW_TIME_DURATION_MS

    def apply_score_multiplier(
        self,
        current_time: int,
    ) -> None:
        self.score_multiplier_until = max(
            self.score_multiplier_until,
            current_time,
        ) + SCORE_MULTIPLIER_DURATION_MS

    def crash(
        self,
        current_time: int,
    ) -> bool:
        if self.is_invincible(
            current_time
        ):
            if self.shield_active(
                current_time
            ):
                self.shield_until = 0

            self.invincible_until = (
                current_time + 800
            )

            return False

        self.alive = False
        self.crashed = True
        self.crash_time = current_time

        return True

    def finish(self) -> None:
        self.finished = True
        self.alive = False

    def collision_angle_width(self) -> float:
        return (
            self.width
            / CYLINDER_LANE_COUNT
        ) * CYLINDER_LANE_ANGLE

    def draw_trail(
        self,
        surface: pygame.Surface,
        current_time: int,
    ) -> None:
        if not self.trail_points:
            return

        recent_points = self.trail_points[
            -PLAYER_TRAIL_LENGTH:
        ]

        for index, point in enumerate(
            recent_points
        ):
            x, y, point_time = point

            age = max(
                0,
                current_time - point_time,
            )

            freshness = max(
                0.0,
                1.0
                - age / 420.0,
            )

            progression = (
                index + 1
            ) / max(
                1,
                len(recent_points),
            )

            alpha = int(
                135
                * freshness
                * progression
            )

            radius = max(
                1,
                round(
                    10
                    * freshness
                    * progression
                ),
            )

            glow = pygame.Surface(
                (
                    radius * 4,
                    radius * 4,
                ),
                pygame.SRCALPHA,
            )

            pygame.draw.circle(
                glow,
                (
                    PLAYER_TRAIL_COLOUR[0],
                    PLAYER_TRAIL_COLOUR[1],
                    PLAYER_TRAIL_COLOUR[2],
                    alpha,
                ),
                (
                    glow.get_width() // 2,
                    glow.get_height() // 2,
                ),
                radius,
            )

            surface.blit(
                glow,
                glow.get_rect(
                    center=(
                        round(x),
                        round(y + 30),
                    )
                ),
            )

    def draw(
        self,
        surface: pygame.Surface,
        current_time: int,
    ) -> None:
        self.draw_trail(
            surface,
            current_time,
        )

        center_x = round(
            self.screen_position.x
        )

        center_y = round(
            self.screen_position.y
        )

        bob = math.sin(
            self.animation_time * 8.0
        ) * 2.0

        center_y += round(bob)

        lean = self.lean_amount * 9.0

        body_points = [
            (
                center_x,
                center_y
                - PLAYER_SCREEN_HEIGHT // 2,
            ),
            (
                center_x
                - PLAYER_SCREEN_WIDTH // 2
                - lean,
                center_y
                + PLAYER_SCREEN_HEIGHT // 3,
            ),
            (
                center_x
                - PLAYER_SCREEN_WIDTH // 5,
                center_y
                + PLAYER_SCREEN_HEIGHT // 5,
            ),
            (
                center_x,
                center_y
                + PLAYER_SCREEN_HEIGHT // 2,
            ),
            (
                center_x
                + PLAYER_SCREEN_WIDTH // 5,
                center_y
                + PLAYER_SCREEN_HEIGHT // 5,
            ),
            (
                center_x
                + PLAYER_SCREEN_WIDTH // 2
                - lean,
                center_y
                + PLAYER_SCREEN_HEIGHT // 3,
            ),
        ]

        shadow_points = [
            (
                x + 4,
                y + 7,
            )
            for x, y in body_points
        ]

        pygame.draw.polygon(
            surface,
            (
                2,
                7,
                18,
            ),
            shadow_points,
        )

        pygame.draw.polygon(
            surface,
            PLAYER_COLOUR,
            body_points,
        )

        pygame.draw.polygon(
            surface,
            PLAYER_HIGHLIGHT_COLOUR,
            body_points,
            width=3,
        )

        cockpit_rect = pygame.Rect(
            center_x - 10,
            center_y - 17,
            20,
            30,
        )

        pygame.draw.ellipse(
            surface,
            DARK_BLUE,
            cockpit_rect,
        )

        pygame.draw.ellipse(
            surface,
            LIGHT_BLUE,
            cockpit_rect,
            width=2,
        )

        engine_flicker = (
            10
            + abs(
                math.sin(
                    self.animation_time * 15.0
                )
            )
            * 12
        )

        engine_points = [
            (
                center_x - 13,
                center_y + 24,
            ),
            (
                center_x - 3,
                center_y
                + 34
                + engine_flicker,
            ),
            (
                center_x + 1,
                center_y + 24,
            ),
        ]

        pygame.draw.polygon(
            surface,
            CYAN,
            engine_points,
        )

        engine_points_right = [
            (
                center_x - 1,
                center_y + 24,
            ),
            (
                center_x + 3,
                center_y
                + 34
                + engine_flicker,
            ),
            (
                center_x + 13,
                center_y + 24,
            ),
        ]

        pygame.draw.polygon(
            surface,
            BLUE,
            engine_points_right,
        )

        if self.shield_active(
            current_time
        ):
            shield_radius = (
                PLAYER_SCREEN_HEIGHT // 2
                + 14
            )

            shield_surface = pygame.Surface(
                (
                    shield_radius * 2 + 8,
                    shield_radius * 2 + 8,
                ),
                pygame.SRCALPHA,
            )

            pulse = (
                80
                + int(
                    abs(
                        math.sin(
                            self.animation_time * 5.0
                        )
                    )
                    * 75
                )
            )

            pygame.draw.circle(
                shield_surface,
                (
                    CYAN[0],
                    CYAN[1],
                    CYAN[2],
                    pulse,
                ),
                (
                    shield_surface.get_width() // 2,
                    shield_surface.get_height() // 2,
                ),
                shield_radius,
                width=3,
            )

            surface.blit(
                shield_surface,
                shield_surface.get_rect(
                    center=(
                        center_x,
                        center_y,
                    )
                ),
            )


# ============================================================
# OBSTACLE
# ============================================================

class CylinderObstacle:
    """
    One obstacle travelling toward the player.
    """

    def __init__(
        self,
        obstacle_type: str,
        world_distance: float,
        lane: int = 0,
        lane_span: int = 1,
        movement_amount: float = 0.0,
        movement_speed: float = 0.0,
        rotation_speed: float = 0.0,
        phase_offset: float = 0.0,
        fake: bool = False,
        metadata: dict[str, object] | None = None,
    ):
        if obstacle_type not in OBSTACLE_DEFINITIONS:
            obstacle_type = OBSTACLE_BLOCK

        self.obstacle_type = obstacle_type
        self.definition = OBSTACLE_DEFINITIONS[
            obstacle_type
        ]

        self.world_distance = float(
            world_distance
        )

        self.starting_distance = float(
            world_distance
        )

        self.starting_lane = int(
            lane
        ) % CYLINDER_LANE_COUNT

        self.current_lane = float(
            self.starting_lane
        )

        self.lane_span = max(
            1,
            int(lane_span),
        )

        self.base_angle = lane_to_angle(
            self.starting_lane
        )

        self.current_angle = self.base_angle

        self.movement_amount = float(
            movement_amount
        )

        self.movement_speed = float(
            movement_speed
            or self.definition.movement_speed
        )

        self.rotation_speed = float(
            rotation_speed
            or self.definition.rotation_speed
        )

        self.phase_offset = float(
            phase_offset
        )

        self.fake = bool(fake)

        self.metadata = dict(
            metadata or {}
        )

        self.active = True
        self.passed = False
        self.hit = False
        self.removed = False

        self.animation_time = 0.0

        self.pulse_amount = 1.0

        self.last_projection: ProjectionResult | None = None

        self.screen_points: list[
            tuple[int, int]
        ] = []

        self.screen_rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self.unique_id = str(
            self.metadata.get(
                "unique_id",
                f"{obstacle_type}-{id(self)}",
            )
        )

    @classmethod
    def from_pattern(
        cls,
        pattern_obstacle: PatternObstacle,
        absolute_distance: float,
    ) -> CylinderObstacle:
        return cls(
            obstacle_type=(
                pattern_obstacle.obstacle_type
            ),
            world_distance=absolute_distance,
            lane=pattern_obstacle.lane,
            lane_span=(
                pattern_obstacle.lane_span
            ),
            movement_amount=(
                pattern_obstacle.movement_amount
            ),
            movement_speed=(
                pattern_obstacle.movement_speed
            ),
            rotation_speed=(
                pattern_obstacle.rotation_speed
            ),
            phase_offset=(
                pattern_obstacle.phase_offset
            ),
            fake=pattern_obstacle.fake,
            metadata=dict(
                pattern_obstacle.metadata
            ),
        )

    @property
    def lethal(self) -> bool:
        return bool(
            self.definition.lethal
        ) and not self.fake

    @property
    def animated(self) -> bool:
        return (
            self.definition.animated
            or self.movement_speed != 0
            or self.rotation_speed != 0
        )

    @property
    def lane_width_degrees(self) -> float:
        definition_width = max(
            0.2,
            float(
                self.definition.lane_width
            ),
        )

        span_width = max(
            definition_width,
            float(self.lane_span),
        )

        return (
            span_width
            * CYLINDER_LANE_ANGLE
        )

    @property
    def collision_depth(self) -> float:
        return max(
            1.0,
            float(
                self.definition.depth
            ),
        )

    @property
    def collision_height(self) -> float:
        return max(
            0.1,
            float(
                self.definition.height
            ),
        )

    def update_animation(
        self,
        delta_time: float,
    ) -> None:
        self.animation_time += delta_time

        phase = (
            self.animation_time
            + self.phase_offset
        )

        if (
            self.obstacle_type
            == OBSTACLE_MOVING_BLOCK
            or self.obstacle_type
            == OBSTACLE_CHASER
        ):
            movement = math.sin(
                phase
                * max(
                    0.1,
                    self.movement_speed,
                )
            ) * self.movement_amount

            self.current_lane = (
                self.starting_lane
                + movement
            ) % CYLINDER_LANE_COUNT

            self.current_angle = normalize_angle(
                self.current_lane
                * CYLINDER_LANE_ANGLE
            )

        elif (
            self.obstacle_type
            == OBSTACLE_ROTATING_WALL
            or self.rotation_speed != 0
        ):
            self.current_angle = normalize_angle(
                self.base_angle
                + phase
                * self.rotation_speed
            )

            self.current_lane = (
                self.current_angle
                / CYLINDER_LANE_ANGLE
            ) % CYLINDER_LANE_COUNT

        else:
            self.current_lane = float(
                self.starting_lane
            )

            self.current_angle = self.base_angle

        if (
            self.obstacle_type
            == OBSTACLE_PULSE_BLOCK
        ):
            self.pulse_amount = (
                0.72
                + (
                    math.sin(
                        phase * 5.0
                    )
                    + 1.0
                )
                * 0.22
            )

        else:
            self.pulse_amount = 1.0

        if (
            self.obstacle_type
            == OBSTACLE_FAKE_GAP
        ):
            reveal_distance = float(
                self.metadata.get(
                    "reveal_distance",
                    32.0,
                )
            )

            self.fake = (
                self.world_distance
                > reveal_distance
            )

    def update(
        self,
        delta_time: float,
        forward_speed: float,
    ) -> None:
        if not self.active:
            return

        self.world_distance -= (
            forward_speed
            * delta_time
        )

        self.update_animation(
            delta_time
        )

        if (
            self.world_distance
            < -20.0
        ):
            self.passed = True
            self.active = False
            self.removed = True

    def lane_angles(
        self,
    ) -> list[float]:
        """
        Return an angle for every lane occupied by the obstacle.
        """

        if self.lane_span <= 1:
            return [
                self.current_angle
            ]

        angles: list[float] = []

        half_span = (
            self.lane_span - 1
        ) / 2.0

        for index in range(
            self.lane_span
        ):
            lane_offset = (
                index - half_span
            )

            angles.append(
                normalize_angle(
                    self.current_angle
                    + lane_offset
                    * CYLINDER_LANE_ANGLE
                )
            )

        return angles

    def collides_with_player(
        self,
        player_world_angle: float,
        current_time: int,
        runner: Runner,
    ) -> bool:
        if (
            not self.active
            or self.hit
            or not self.lethal
            or runner.is_invincible(
                current_time
            )
        ):
            return False

        distance_overlap = (
            -runner.collision_depth
            <= self.world_distance
            <= self.collision_depth
        )

        if not distance_overlap:
            return False

        player_angle_width = (
            runner.collision_angle_width()
        )

        for obstacle_angle in self.lane_angles():
            if angular_overlap(
                player_world_angle,
                player_angle_width,
                obstacle_angle,
                CYLINDER_LANE_ANGLE * 0.72,
            ):
                self.hit = True
                return True

        return False

    def reached_finish_line(
        self,
    ) -> bool:
        return (
            self.obstacle_type
            == OBSTACLE_FINISH_LINE
            and self.world_distance <= 0
        )

    def draw_block(
        self,
        surface: pygame.Surface,
        projector: CylinderProjector,
        projection: ProjectionResult,
        angle: float,
    ) -> None:
        if not projection.visible:
            return

        base_width = (
            72.0
            * self.definition.lane_width
            * projection.scale
        )

        base_height = (
            86.0
            * self.definition.height
            * projection.scale
            * self.pulse_amount
        )

        width = max(
            2,
            round(base_width),
        )

        height = max(
            2,
            round(base_height),
        )

        x = round(
            projection.x
            - width / 2
        )

        y = round(
            projection.y
            - height
        )

        rect = pygame.Rect(
            x,
            y,
            width,
            height,
        )

        fog_colour = colour_lerp(
            self.definition.base_colour,
            SPACE_BLACK,
            projector.fog_amount(
                self.world_distance
            ),
        )

        fill_colour = scale_colour(
            fog_colour,
            projection.brightness,
        )

        highlight_colour = scale_colour(
            self.definition.highlight_colour,
            min(
                1.35,
                projection.brightness + 0.28,
            ),
        )

        if self.fake:
            fill_colour = scale_colour(
                fill_colour,
                0.42,
            )

            highlight_colour = scale_colour(
                highlight_colour,
                0.58,
            )

        shadow_rect = rect.move(
            max(
                1,
                round(
                    7 * projection.scale
                ),
            ),
            max(
                1,
                round(
                    8 * projection.scale
                ),
            ),
        )

        pygame.draw.rect(
            surface,
            BLACK,
            shadow_rect,
            border_radius=max(
                1,
                round(
                    7 * projection.scale
                ),
            ),
        )

        pygame.draw.rect(
            surface,
            fill_colour,
            rect,
            border_radius=max(
                1,
                round(
                    7 * projection.scale
                ),
            ),
        )

        border_width = max(
            1,
            round(
                3 * projection.scale
            ),
        )

        pygame.draw.rect(
            surface,
            highlight_colour,
            rect,
            width=border_width,
            border_radius=max(
                1,
                round(
                    7 * projection.scale
                ),
            ),
        )

        top_height = max(
            1,
            round(
                height * 0.18
            ),
        )

        top_rect = pygame.Rect(
            rect.left + border_width,
            rect.top + border_width,
            max(
                1,
                rect.width
                - border_width * 2,
            ),
            top_height,
        )

        pygame.draw.rect(
            surface,
            scale_colour(
                highlight_colour,
                1.08,
            ),
            top_rect,
            border_radius=max(
                1,
                round(
                    4 * projection.scale
                ),
            ),
        )

        if (
            ENABLE_GLOW_EFFECTS
            and projection.scale > 0.08
        ):
            glow_padding = max(
                2,
                round(
                    12
                    * projection.scale
                ),
            )

            glow_surface = pygame.Surface(
                (
                    rect.width
                    + glow_padding * 2,
                    rect.height
                    + glow_padding * 2,
                ),
                pygame.SRCALPHA,
            )

            glow_rect = pygame.Rect(
                glow_padding,
                glow_padding,
                rect.width,
                rect.height,
            )

            pygame.draw.rect(
                glow_surface,
                (
                    highlight_colour[0],
                    highlight_colour[1],
                    highlight_colour[2],
                    45,
                ),
                glow_rect,
                width=max(
                    1,
                    border_width,
                ),
                border_radius=max(
                    1,
                    round(
                        8 * projection.scale
                    ),
                ),
            )

            surface.blit(
                glow_surface,
                (
                    rect.left - glow_padding,
                    rect.top - glow_padding,
                ),
            )

        self.screen_rect = rect

    def draw_spike(
        self,
        surface: pygame.Surface,
        projection: ProjectionResult,
    ) -> None:
        width = max(
            3,
            round(
                60
                * projection.scale
            ),
        )

        height = max(
            5,
            round(
                115
                * projection.scale
            ),
        )

        points = [
            (
                round(projection.x),
                round(
                    projection.y - height
                ),
            ),
            (
                round(
                    projection.x
                    - width / 2
                ),
                round(projection.y),
            ),
            (
                round(
                    projection.x
                    + width / 2
                ),
                round(projection.y),
            ),
        ]

        fill_colour = scale_colour(
            self.definition.base_colour,
            projection.brightness,
        )

        highlight_colour = scale_colour(
            self.definition.highlight_colour,
            projection.brightness + 0.25,
        )

        pygame.draw.polygon(
            surface,
            fill_colour,
            points,
        )

        pygame.draw.polygon(
            surface,
            highlight_colour,
            points,
            width=max(
                1,
                round(
                    2
                    * projection.scale
                ),
            ),
        )

        self.screen_rect = pygame.Rect(
            round(
                projection.x
                - width / 2
            ),
            round(
                projection.y - height
            ),
            width,
            height,
        )

    def draw_laser(
        self,
        surface: pygame.Surface,
        projector: CylinderProjector,
    ) -> None:
        start_projection = projector.project(
            self.current_angle
            - self.lane_width_degrees / 2,
            self.world_distance,
            radial_height=0.45,
        )

        end_projection = projector.project(
            self.current_angle
            + self.lane_width_degrees / 2,
            self.world_distance,
            radial_height=0.45,
        )

        if (
            not start_projection.visible
            and not end_projection.visible
        ):
            return

        thickness = max(
            1,
            round(
                10
                * max(
                    start_projection.scale,
                    end_projection.scale,
                )
            ),
        )

        pygame.draw.line(
            surface,
            scale_colour(
                self.definition.base_colour,
                (
                    start_projection.brightness
                    + end_projection.brightness
                ) / 2,
            ),
            (
                round(start_projection.x),
                round(start_projection.y),
            ),
            (
                round(end_projection.x),
                round(end_projection.y),
            ),
            thickness,
        )

        pygame.draw.line(
            surface,
            WHITE,
            (
                round(start_projection.x),
                round(start_projection.y),
            ),
            (
                round(end_projection.x),
                round(end_projection.y),
            ),
            max(
                1,
                thickness // 3,
            ),
        )

        self.screen_rect = pygame.Rect(
            min(
                round(start_projection.x),
                round(end_projection.x),
            ),
            min(
                round(start_projection.y),
                round(end_projection.y),
            )
            - thickness,
            abs(
                round(end_projection.x)
                - round(start_projection.x)
            )
            + thickness,
            abs(
                round(end_projection.y)
                - round(start_projection.y)
            )
            + thickness * 2,
        )

    def draw_finish_line(
        self,
        surface: pygame.Surface,
        projector: CylinderProjector,
    ) -> None:
        points: list[
            tuple[int, int]
        ] = []

        segments = max(
            12,
            CYLINDER_LANE_COUNT * 2,
        )

        for index in range(
            segments + 1
        ):
            angle = (
                index
                / segments
                * CYLINDER_FULL_ROTATION
            )

            projection = projector.project(
                angle,
                self.world_distance,
                radial_height=0.04,
            )

            if projection.visible:
                points.append(
                    (
                        round(projection.x),
                        round(projection.y),
                    )
                )

        if len(points) >= 2:
            pygame.draw.lines(
                surface,
                GREEN,
                False,
                points,
                width=max(
                    1,
                    round(
                        8
                        * projector.scale_at_distance(
                            max(
                                0.0,
                                self.world_distance,
                            )
                        )
                    ),
                ),
            )

    def draw(
        self,
        surface: pygame.Surface,
        projector: CylinderProjector,
    ) -> None:
        if not self.active:
            return

        if (
            self.obstacle_type
            == OBSTACLE_FINISH_LINE
        ):
            self.draw_finish_line(
                surface,
                projector,
            )
            return

        if (
            self.obstacle_type
            == OBSTACLE_LASER
        ):
            self.draw_laser(
                surface,
                projector,
            )
            return

        self.screen_points.clear()

        for angle in self.lane_angles():
            projection = projector.project(
                angle,
                self.world_distance,
                radial_height=0.02,
            )

            self.last_projection = projection

            if not projection.visible:
                continue

            if (
                self.obstacle_type
                == OBSTACLE_SPIKE
            ):
                self.draw_spike(
                    surface,
                    projection,
                )

            else:
                self.draw_block(
                    surface,
                    projector,
                    projection,
                    angle,
                )

            self.screen_points.append(
                (
                    round(projection.x),
                    round(projection.y),
                )
            )


# ============================================================
# COLLECTIBLES
# ============================================================

COLLECTIBLE_TYPES = (
    "energy",
    "shield",
    "slow_time",
    "score_multiplier",
)


COLLECTIBLE_COLOURS: dict[
    str,
    tuple[int, int, int]
] = {
    "energy": YELLOW,
    "shield": CYAN,
    "slow_time": PURPLE,
    "score_multiplier": GREEN,
}


COLLECTIBLE_SYMBOLS: dict[
    str,
    str
] = {
    "energy": "E",
    "shield": "S",
    "slow_time": "T",
    "score_multiplier": "2X",
}


class Collectible:
    """
    A collectible placed on the cylinder.
    """

    def __init__(
        self,
        collectible_type: str,
        world_distance: float,
        lane: int,
        value: int = 1,
    ):
        if collectible_type not in COLLECTIBLE_TYPES:
            collectible_type = "energy"

        self.collectible_type = collectible_type

        self.world_distance = float(
            world_distance
        )

        self.lane = int(
            lane
        ) % CYLINDER_LANE_COUNT

        self.world_angle = lane_to_angle(
            self.lane
        )

        self.value = max(
            1,
            int(value),
        )

        self.active = True
        self.collected = False

        self.animation_time = random.random() * 10.0

        self.screen_rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

    def update(
        self,
        delta_time: float,
        forward_speed: float,
    ) -> None:
        if not self.active:
            return

        self.animation_time += delta_time

        self.world_distance -= (
            forward_speed
            * delta_time
        )

        if self.world_distance < -15:
            self.active = False

    def collides_with_player(
        self,
        player_world_angle: float,
    ) -> bool:
        if (
            not self.active
            or self.collected
        ):
            return False

        if not (
            -PLAYER_COLLISION_DEPTH
            <= self.world_distance
            <= 5.0
        ):
            return False

        return angular_overlap(
            player_world_angle,
            CYLINDER_LANE_ANGLE * 0.72,
            self.world_angle,
            CYLINDER_LANE_ANGLE * 0.72,
        )

    def apply(
        self,
        runner: Runner,
        current_time: int,
    ) -> dict[str, int | str]:
        self.collected = True
        self.active = False

        result: dict[
            str,
            int | str
        ] = {
            "type": self.collectible_type,
            "value": self.value,
        }

        if (
            self.collectible_type
            == "shield"
        ):
            runner.apply_shield(
                current_time
            )

        elif (
            self.collectible_type
            == "slow_time"
        ):
            runner.apply_slow_time(
                current_time
            )

        elif (
            self.collectible_type
            == "score_multiplier"
        ):
            runner.apply_score_multiplier(
                current_time
            )

        return result

    def draw(
        self,
        surface: pygame.Surface,
        projector: CylinderProjector,
        font: pygame.font.Font | None = None,
    ) -> None:
        if not self.active:
            return

        hover_height = (
            0.22
            + math.sin(
                self.animation_time * 4.0
            )
            * 0.08
        )

        projection = projector.project(
            self.world_angle,
            self.world_distance,
            radial_height=hover_height,
        )

        if not projection.visible:
            return

        radius = max(
            2,
            round(
                20
                * projection.scale
            ),
        )

        colour = COLLECTIBLE_COLOURS[
            self.collectible_type
        ]

        glow_radius = radius * 2

        glow_surface = pygame.Surface(
            (
                glow_radius * 2,
                glow_radius * 2,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            glow_surface,
            (
                colour[0],
                colour[1],
                colour[2],
                55,
            ),
            (
                glow_radius,
                glow_radius,
            ),
            glow_radius,
        )

        surface.blit(
            glow_surface,
            glow_surface.get_rect(
                center=(
                    round(projection.x),
                    round(projection.y),
                )
            ),
        )

        pygame.draw.circle(
            surface,
            scale_colour(
                colour,
                projection.brightness + 0.22,
            ),
            (
                round(projection.x),
                round(projection.y),
            ),
            radius,
        )

        pygame.draw.circle(
            surface,
            WHITE,
            (
                round(projection.x),
                round(projection.y),
            ),
            radius,
            width=max(
                1,
                round(
                    2 * projection.scale
                ),
            ),
        )

        if (
            font is not None
            and radius >= 7
        ):
            symbol = COLLECTIBLE_SYMBOLS[
                self.collectible_type
            ]

            image = font.render(
                symbol,
                True,
                BLACK,
            )

            if image.get_width() > radius * 1.5:
                scale = (
                    radius * 1.5
                    / image.get_width()
                )

                image = pygame.transform.smoothscale(
                    image,
                    (
                        max(
                            1,
                            round(
                                image.get_width()
                                * scale
                            ),
                        ),
                        max(
                            1,
                            round(
                                image.get_height()
                                * scale
                            ),
                        ),
                    ),
                )

            surface.blit(
                image,
                image.get_rect(
                    center=(
                        round(projection.x),
                        round(projection.y),
                    )
                ),
            )

        self.screen_rect = pygame.Rect(
            round(
                projection.x - radius
            ),
            round(
                projection.y - radius
            ),
            radius * 2,
            radius * 2,
        )


# ============================================================
# PARTICLES
# ============================================================

class Particle:
    """
    One screen-space particle.
    """

    def __init__(
        self,
        position: pygame.Vector2
        | tuple[float, float],
        velocity: pygame.Vector2
        | tuple[float, float],
        colour: tuple[int, int, int],
        lifetime: float,
        radius: float,
        gravity: float = 0.0,
        drag: float = 0.0,
        glow: bool = False,
    ):
        self.position = pygame.Vector2(
            position
        )

        self.velocity = pygame.Vector2(
            velocity
        )

        self.colour = colour

        self.lifetime = max(
            0.01,
            float(lifetime),
        )

        self.remaining = self.lifetime

        self.radius = max(
            0.5,
            float(radius),
        )

        self.gravity = float(
            gravity
        )

        self.drag = max(
            0.0,
            float(drag),
        )

        self.glow = bool(glow)

        self.active = True

    def update(
        self,
        delta_time: float,
    ) -> None:
        if not self.active:
            return

        self.remaining -= delta_time

        if self.remaining <= 0:
            self.active = False
            return

        self.velocity.y += (
            self.gravity
            * delta_time
        )

        if self.drag > 0:
            drag_factor = max(
                0.0,
                1.0
                - self.drag * delta_time
            )

            self.velocity *= drag_factor

        self.position += (
            self.velocity
            * delta_time
        )

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        if not self.active:
            return

        life_ratio = clamp(
            self.remaining
            / self.lifetime,
            0.0,
            1.0,
        )

        radius = max(
            1,
            round(
                self.radius
                * life_ratio
            ),
        )

        colour = scale_colour(
            self.colour,
            0.45
            + life_ratio * 0.75,
        )

        if self.glow:
            glow_radius = radius * 3

            glow_surface = pygame.Surface(
                (
                    glow_radius * 2,
                    glow_radius * 2,
                ),
                pygame.SRCALPHA,
            )

            pygame.draw.circle(
                glow_surface,
                (
                    colour[0],
                    colour[1],
                    colour[2],
                    round(
                        70 * life_ratio
                    ),
                ),
                (
                    glow_radius,
                    glow_radius,
                ),
                glow_radius,
            )

            surface.blit(
                glow_surface,
                glow_surface.get_rect(
                    center=(
                        round(
                            self.position.x
                        ),
                        round(
                            self.position.y
                        ),
                    )
                ),
            )

        pygame.draw.circle(
            surface,
            colour,
            (
                round(
                    self.position.x
                ),
                round(
                    self.position.y
                ),
            ),
            radius,
        )


class ParticleSystem:
    """
    Manages visual particles and effects.
    """

    def __init__(self):
        self.particles: list[
            Particle
        ] = []

    def clear(self) -> None:
        self.particles.clear()

    def add(
        self,
        particle: Particle,
    ) -> None:
        if not ENABLE_PARTICLES:
            return

        self.particles.append(
            particle
        )

        if len(self.particles) > MAX_PARTICLES:
            del self.particles[
                : len(self.particles)
                - MAX_PARTICLES
            ]

    def create_crash(
        self,
        position: pygame.Vector2
        | tuple[float, float],
        amount: int = 55,
    ) -> None:
        colours = (
            PLAYER_COLOUR,
            CYAN,
            ORANGE,
            YELLOW,
            WHITE,
        )

        for _ in range(amount):
            angle = random.uniform(
                0,
                math.tau,
            )

            speed = random.uniform(
                100,
                440,
            )

            velocity = pygame.Vector2(
                math.cos(angle),
                math.sin(angle),
            ) * speed

            self.add(
                Particle(
                    position=position,
                    velocity=velocity,
                    colour=random.choice(
                        colours
                    ),
                    lifetime=random.uniform(
                        0.35,
                        1.1,
                    ),
                    radius=random.uniform(
                        2.0,
                        7.0,
                    ),
                    gravity=180.0,
                    drag=1.6,
                    glow=True,
                )
            )

    def create_collect(
        self,
        position: pygame.Vector2
        | tuple[float, float],
        colour: tuple[int, int, int],
        amount: int = 18,
    ) -> None:
        for _ in range(amount):
            angle = random.uniform(
                0,
                math.tau,
            )

            speed = random.uniform(
                45,
                180,
            )

            velocity = pygame.Vector2(
                math.cos(angle),
                math.sin(angle),
            ) * speed

            self.add(
                Particle(
                    position=position,
                    velocity=velocity,
                    colour=colour,
                    lifetime=random.uniform(
                        0.28,
                        0.7,
                    ),
                    radius=random.uniform(
                        1.5,
                        4.0,
                    ),
                    drag=2.4,
                    glow=True,
                )
            )

    def create_speed_trail(
        self,
        position: pygame.Vector2
        | tuple[float, float],
        rotation_velocity: float,
    ) -> None:
        if random.random() > 0.55:
            return

        horizontal_push = clamp(
            rotation_velocity
            / 3.5,
            -80,
            80,
        )

        velocity = pygame.Vector2(
            -horizontal_push
            + random.uniform(
                -18,
                18,
            ),
            random.uniform(
                85,
                180,
            ),
        )

        self.add(
            Particle(
                position=position,
                velocity=velocity,
                colour=random.choice(
                    (
                        PLAYER_TRAIL_COLOUR,
                        CYAN,
                        BLUE,
                    )
                ),
                lifetime=random.uniform(
                    0.18,
                    0.42,
                ),
                radius=random.uniform(
                    1.5,
                    3.5,
                ),
                drag=2.0,
                glow=True,
            )
        )

    def update(
        self,
        delta_time: float,
    ) -> None:
        for particle in self.particles[:]:
            particle.update(
                delta_time
            )

            if not particle.active:
                self.particles.remove(
                    particle
                )

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        for particle in self.particles:
            particle.draw(
                surface
            )


# ============================================================
# SCREEN SHAKE
# ============================================================

class ScreenShake:
    """
    Small camera shake controller used during crashes.
    """

    def __init__(self):
        self.strength = 0.0
        self.duration_ms = 0
        self.start_time = 0

        self.offset = pygame.Vector2()

    def clear(self) -> None:
        self.strength = 0.0
        self.duration_ms = 0
        self.start_time = 0
        self.offset.update(
            0,
            0,
        )

    def trigger(
        self,
        current_time: int,
        strength: float = CRASH_SHAKE_STRENGTH,
        duration_ms: int = CRASH_SHAKE_DURATION_MS,
    ) -> None:
        if not ENABLE_SCREEN_SHAKE:
            return

        self.start_time = int(
            current_time
        )

        self.strength = max(
            0.0,
            float(strength),
        )

        self.duration_ms = max(
            1,
            int(duration_ms),
        )

    def update(
        self,
        current_time: int,
    ) -> None:
        if self.duration_ms <= 0:
            self.offset.update(
                0,
                0,
            )
            return

        elapsed = (
            current_time
            - self.start_time
        )

        if elapsed >= self.duration_ms:
            self.clear()
            return

        remaining = (
            1.0
            - elapsed
            / self.duration_ms
        )

        current_strength = (
            self.strength
            * remaining
        )

        self.offset.update(
            random.uniform(
                -current_strength,
                current_strength,
            ),
            random.uniform(
                -current_strength,
                current_strength,
            ),
        )


# ============================================================
# GAMEPLAY WORLD
# ============================================================

class GameplayWorld:
    """
    Complete entity container used by Levels and Endless Mode.

    It owns:
    - the runner
    - cylinder rotation
    - obstacles
    - collectibles
    - particles
    - collisions
    - finish-line detection
    """

    def __init__(self):
        self.projector = CylinderProjector()
        self.cylinder = CylinderController()
        self.runner = Runner()

        self.obstacles: list[
            CylinderObstacle
        ] = []

        self.collectibles: list[
            Collectible
        ] = []

        self.particles = ParticleSystem()
        self.screen_shake = ScreenShake()

        self.forward_speed = 0.0
        self.distance = 0.0

        self.finished = False
        self.crashed = False

        self.energy_collected = 0
        self.powerups_collected = 0

        self.obstacles_passed = 0

        self.last_collision: (
            CylinderObstacle
            | None
        ) = None

    def reset(
        self,
        starting_speed: float,
        starting_angle: float = PLAYER_STARTING_ANGLE,
    ) -> None:
        self.projector.reset()
        self.cylinder.reset()

        self.runner.reset(
            starting_angle
        )

        self.obstacles.clear()
        self.collectibles.clear()

        self.particles.clear()
        self.screen_shake.clear()

        self.forward_speed = max(
            0.0,
            float(starting_speed),
        )

        self.distance = 0.0

        self.finished = False
        self.crashed = False

        self.energy_collected = 0
        self.powerups_collected = 0

        self.obstacles_passed = 0

        self.last_collision = None

    def add_obstacle(
        self,
        obstacle: CylinderObstacle,
    ) -> None:
        self.obstacles.append(
            obstacle
        )

    def add_pattern_obstacle(
        self,
        pattern_obstacle: PatternObstacle,
        absolute_distance: float,
    ) -> CylinderObstacle:
        obstacle_entity = (
            CylinderObstacle.from_pattern(
                pattern_obstacle,
                absolute_distance,
            )
        )

        self.add_obstacle(
            obstacle_entity
        )

        return obstacle_entity

    def add_collectible(
        self,
        collectible: Collectible,
    ) -> None:
        self.collectibles.append(
            collectible
        )

    def set_rotation_input(
        self,
        direction: int,
    ) -> None:
        self.cylinder.set_input(
            direction
        )

    def effective_speed(
        self,
        current_time: int,
    ) -> float:
        if self.runner.slow_time_active(
            current_time
        ):
            return (
                self.forward_speed
                * SLOW_TIME_SPEED_MULTIPLIER
            )

        return self.forward_speed

    def update(
        self,
        delta_time: float,
        current_time: int,
    ) -> list[
        dict[str, Any]
    ]:
        """
        Update all gameplay entities.

        Returns gameplay events for main.py.
        """

        events: list[
            dict[str, Any]
        ] = []

        self.screen_shake.update(
            current_time
        )

        if (
            self.crashed
            or self.finished
        ):
            self.particles.update(
                delta_time
            )

            return events

        self.cylinder.update(
            delta_time
        )

        self.projector.set_rotation(
            self.cylinder.rotation
        )

        self.runner.world_angle = (
            self.cylinder.player_world_angle()
        )

        self.runner.update(
            delta_time,
            current_time,
            self.cylinder.rotation_velocity,
        )

        active_speed = self.effective_speed(
            current_time
        )

        travelled = (
            active_speed
            * delta_time
        )

        self.distance += travelled
        self.runner.distance = self.distance

        for obstacle in self.obstacles[:]:
            was_active = obstacle.active

            obstacle.update(
                delta_time,
                active_speed,
            )

            if (
                was_active
                and obstacle.passed
            ):
                self.obstacles_passed += 1

                events.append(
                    {
                        "type": "obstacle_passed",
                        "obstacle": obstacle,
                    }
                )

            if obstacle.reached_finish_line():
                self.finished = True
                self.runner.finish()

                events.append(
                    {
                        "type": "finish",
                        "obstacle": obstacle,
                    }
                )

                break

            if obstacle.collides_with_player(
                self.runner.world_angle,
                current_time,
                self.runner,
            ):
                self.last_collision = obstacle

                crashed = self.runner.crash(
                    current_time
                )

                if crashed:
                    self.crashed = True

                    self.particles.create_crash(
                        self.runner.screen_position
                    )

                    self.screen_shake.trigger(
                        current_time
                    )

                    events.append(
                        {
                            "type": "crash",
                            "obstacle": obstacle,
                        }
                    )

                    break

                events.append(
                    {
                        "type": "shield_hit",
                        "obstacle": obstacle,
                    }
                )

            if obstacle.removed:
                self.obstacles.remove(
                    obstacle
                )

        for collectible in self.collectibles[:]:
            collectible.update(
                delta_time,
                active_speed,
            )

            if collectible.collides_with_player(
                self.runner.world_angle
            ):
                result = collectible.apply(
                    self.runner,
                    current_time,
                )

                colour = COLLECTIBLE_COLOURS[
                    collectible.collectible_type
                ]

                projection = self.projector.project(
                    collectible.world_angle,
                    collectible.world_distance,
                    radial_height=0.2,
                )

                self.particles.create_collect(
                    (
                        projection.x,
                        projection.y,
                    ),
                    colour,
                )

                if (
                    collectible.collectible_type
                    == "energy"
                ):
                    self.energy_collected += (
                        collectible.value
                    )

                else:
                    self.powerups_collected += 1

                events.append(
                    {
                        "type": "collectible",
                        "collectible": collectible,
                        "result": result,
                    }
                )

            if not collectible.active:
                self.collectibles.remove(
                    collectible
                )

        self.particles.create_speed_trail(
            (
                self.runner.screen_position.x,
                self.runner.screen_position.y
                + 26,
            ),
            self.cylinder.rotation_velocity,
        )

        self.particles.update(
            delta_time
        )

        return events

    def sorted_drawables(
        self,
    ) -> list[
        CylinderObstacle
        | Collectible
    ]:
        """
        Draw distant objects first.
        """

        drawables: list[
            CylinderObstacle
            | Collectible
        ] = []

        drawables.extend(
            obstacle
            for obstacle in self.obstacles
            if obstacle.active
        )

        drawables.extend(
            collectible
            for collectible in self.collectibles
            if collectible.active
        )

        drawables.sort(
            key=lambda entity: (
                entity.world_distance
            ),
            reverse=True,
        )

        return drawables

    def draw_entities(
        self,
        surface: pygame.Surface,
        collectible_font: (
            pygame.font.Font
            | None
        ) = None,
        current_time: int = 0,
    ) -> None:
        for entity in self.sorted_drawables():
            if isinstance(
                entity,
                CylinderObstacle,
            ):
                entity.draw(
                    surface,
                    self.projector,
                )

            else:
                entity.draw(
                    surface,
                    self.projector,
                    collectible_font,
                )

        self.runner.draw(
            surface,
            current_time,
        )

        self.particles.draw(
            surface
        )


# ============================================================
# ENDLESS OBSTACLE GENERATION SUPPORT
# ============================================================

@dataclass
class EndlessSection:
    """
    One procedurally generated Endless Mode section.
    """

    start_distance: float
    length: float
    difficulty: float

    safe_lane: int

    obstacles: list[
        CylinderObstacle
    ] = field(
        default_factory=list
    )

    collectibles: list[
        Collectible
    ] = field(
        default_factory=list
    )

    pattern_name: str = "Unknown"

    completed: bool = False


class EndlessObstacleFactory:
    """
    Creates fair random obstacle sections for Endless Mode.

    The final generation manager will live in main.py or a future
    generator module, but every obstacle-building tool is ready here.
    """

    def __init__(
        self,
        seed: int | None = None,
    ):
        self.random = random.Random(
            seed
        )

        self.last_safe_lane = 0
        self.last_pattern_name = ""

        self.consecutive_hard_patterns = 0

    def reset(
        self,
        seed: int | None = None,
    ) -> None:
        if seed is not None:
            self.random.seed(
                seed
            )

        self.last_safe_lane = self.random.randrange(
            CYLINDER_LANE_COUNT
        )

        self.last_pattern_name = ""
        self.consecutive_hard_patterns = 0

    def choose_safe_lane(
        self,
        maximum_change: int = 3,
    ) -> int:
        change = self.random.randint(
            -maximum_change,
            maximum_change,
        )

        self.last_safe_lane = (
            self.last_safe_lane
            + change
        ) % CYLINDER_LANE_COUNT

        return self.last_safe_lane

    def create_single_barriers(
        self,
        start_distance: float,
        difficulty: float,
    ) -> EndlessSection:
        safe_lane = self.choose_safe_lane(
            4
        )

        obstacle_count = int(
            clamp(
                2
                + difficulty * 0.22,
                2,
                7,
            )
        )

        obstacles: list[
            CylinderObstacle
        ] = []

        spacing = max(
            8.0,
            17.0
            - difficulty * 0.28,
        )

        for index in range(
            obstacle_count
        ):
            blocked_lane = (
                safe_lane
                + self.random.choice(
                    [
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                    ]
                )
            ) % CYLINDER_LANE_COUNT

            obstacles.append(
                CylinderObstacle(
                    obstacle_type=(
                        OBSTACLE_BLOCK
                    ),
                    world_distance=(
                        start_distance
                        + 8
                        + index * spacing
                    ),
                    lane=blocked_lane,
                    lane_span=self.random.choice(
                        [1, 1, 2]
                    ),
                )
            )

            safe_lane = (
                safe_lane
                + self.random.choice(
                    [-2, -1, 1, 2]
                )
            ) % CYLINDER_LANE_COUNT

        length = (
            20.0
            + obstacle_count * spacing
        )

        return EndlessSection(
            start_distance=start_distance,
            length=length,
            difficulty=difficulty,
            safe_lane=self.last_safe_lane,
            obstacles=obstacles,
            pattern_name="Single Barriers",
        )

    def create_gap_walls(
        self,
        start_distance: float,
        difficulty: float,
    ) -> EndlessSection:
        row_count = int(
            clamp(
                2
                + difficulty * 0.16,
                2,
                7,
            )
        )

        gap_width = (
            3
            if difficulty < 4
            else 2
            if difficulty < 11
            else 1
        )

        row_spacing = max(
            8.0,
            18.0
            - difficulty * 0.32,
        )

        safe_lane = self.choose_safe_lane(
            2
        )

        obstacles: list[
            CylinderObstacle
        ] = []

        for row in range(
            row_count
        ):
            safe_lane = (
                safe_lane
                + self.random.choice(
                    [-2, -1, 0, 1, 2]
                )
            ) % CYLINDER_LANE_COUNT

            safe_lanes = {
                (
                    safe_lane + offset
                ) % CYLINDER_LANE_COUNT
                for offset in range(
                    gap_width
                )
            }

            row_distance = (
                start_distance
                + 10
                + row * row_spacing
            )

            for lane in range(
                CYLINDER_LANE_COUNT
            ):
                if lane in safe_lanes:
                    continue

                obstacles.append(
                    CylinderObstacle(
                        obstacle_type=(
                            OBSTACLE_WALL_GAP
                        ),
                        world_distance=(
                            row_distance
                        ),
                        lane=lane,
                    )
                )

        self.last_safe_lane = safe_lane

        length = (
            24.0
            + row_count * row_spacing
        )

        return EndlessSection(
            start_distance=start_distance,
            length=length,
            difficulty=difficulty,
            safe_lane=safe_lane,
            obstacles=obstacles,
            pattern_name="Gap Walls",
        )

    def create_moving_section(
        self,
        start_distance: float,
        difficulty: float,
    ) -> EndlessSection:
        obstacle_count = int(
            clamp(
                2
                + difficulty * 0.17,
                2,
                6,
            )
        )

        spacing = max(
            9.0,
            17.0
            - difficulty * 0.25,
        )

        safe_lane = self.choose_safe_lane(
            3
        )

        obstacles: list[
            CylinderObstacle
        ] = []

        for index in range(
            obstacle_count
        ):
            lane = (
                safe_lane
                + 5
                + index * 3
            ) % CYLINDER_LANE_COUNT

            obstacles.append(
                CylinderObstacle(
                    obstacle_type=(
                        OBSTACLE_MOVING_BLOCK
                    ),
                    world_distance=(
                        start_distance
                        + 10
                        + index * spacing
                    ),
                    lane=lane,
                    movement_amount=min(
                        5.0,
                        1.5
                        + difficulty * 0.18,
                    ),
                    movement_speed=min(
                        2.3,
                        0.75
                        + difficulty * 0.06,
                    ),
                    phase_offset=(
                        index * 0.8
                    ),
                )
            )

        length = (
            22.0
            + obstacle_count * spacing
        )

        return EndlessSection(
            start_distance=start_distance,
            length=length,
            difficulty=difficulty,
            safe_lane=safe_lane,
            obstacles=obstacles,
            pattern_name="Moving Barriers",
        )

    def create_spiral_section(
        self,
        start_distance: float,
        difficulty: float,
    ) -> EndlessSection:
        step_count = int(
            clamp(
                5
                + difficulty * 0.22,
                5,
                12,
            )
        )

        spacing = max(
            7.0,
            13.0
            - difficulty * 0.22,
        )

        direction = self.random.choice(
            [-1, 1]
        )

        lane = self.choose_safe_lane(
            2
        )

        obstacles: list[
            CylinderObstacle
        ] = []

        for index in range(
            step_count
        ):
            blocked_lane = (
                lane + 6
            ) % CYLINDER_LANE_COUNT

            obstacles.append(
                CylinderObstacle(
                    obstacle_type=(
                        OBSTACLE_TALL_BLOCK
                    ),
                    world_distance=(
                        start_distance
                        + 8
                        + index * spacing
                    ),
                    lane=blocked_lane,
                    lane_span=2,
                )
            )

            lane = (
                lane + direction
            ) % CYLINDER_LANE_COUNT

        self.last_safe_lane = lane

        length = (
            18.0
            + step_count * spacing
        )

        return EndlessSection(
            start_distance=start_distance,
            length=length,
            difficulty=difficulty,
            safe_lane=lane,
            obstacles=obstacles,
            pattern_name="Spiral",
        )

    def create_random_section(
        self,
        start_distance: float,
        difficulty: float,
        allow_moving: bool = True,
        allow_rotating: bool = True,
        allow_fake_gaps: bool = True,
        allow_chasers: bool = True,
    ) -> EndlessSection:
        """
        Choose and build one fair Endless Mode section.
        """

        builders = [
            self.create_single_barriers,
            self.create_gap_walls,
            self.create_spiral_section,
        ]

        if (
            allow_moving
            and difficulty >= 3.5
        ):
            builders.append(
                self.create_moving_section
            )

        builder = self.random.choice(
            builders
        )

        section = builder(
            start_distance,
            difficulty,
        )

        self.last_pattern_name = (
            section.pattern_name
        )

        if difficulty >= 5:
            collectible_chance = min(
                0.34,
                0.08
                + difficulty * 0.012,
            )

            if (
                self.random.random()
                < collectible_chance
            ):
                collectible_type = (
                    self.random.choice(
                        COLLECTIBLE_TYPES
                    )
                )

                collectible_lane = (
                    section.safe_lane
                )

                collectible_distance = (
                    start_distance
                    + section.length * 0.62
                )

                section.collectibles.append(
                    Collectible(
                        collectible_type,
                        collectible_distance,
                        collectible_lane,
                    )
                )

        return section