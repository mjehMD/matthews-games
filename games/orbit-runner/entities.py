from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Iterable

import pygame

from config import (
    BLACK, BLUE, CYAN, GAME_HEIGHT, GAME_WIDTH, GREEN, LANE_ANGLE, NEAR_CLIP,
    OBSTACLE_BAR, OBSTACLE_CROSS, OBSTACLE_DOUBLE_GATE, OBSTACLE_FAN,
    OBSTACLE_FINISH, OBSTACLE_GATE, OBSTACLE_PULSE, OBSTACLE_SHUTTER,
    OBSTACLE_SLIDER, OBSTACLE_ZIGZAG, ORANGE, PERSPECTIVE_POWER,
    PLAYER_ANGULAR_ACCELERATION, PLAYER_ANGULAR_FRICTION,
    PLAYER_ANGULAR_SPEED, PLAYER_COLLISION_HALF_WIDTH, PLAYER_START_ANGLE,
    PURPLE, RED, TUNNEL_CENTER_X, TUNNEL_CENTER_Y, TUNNEL_FAR_RADIUS,
    TUNNEL_NEAR_RADIUS, VISIBLE_DISTANCE, WHITE, YELLOW, clamp, colour_lerp,
    lerp, normalize_angle, shortest_angle_difference,
)


@dataclass(frozen=True)
class Projection:
    distance: float
    factor: float
    radius: float
    scale: float
    visible: bool


class TunnelProjector:
    def project_distance(self, distance: float) -> Projection:
        visible = -NEAR_CLIP <= distance <= VISIBLE_DISTANCE
        normalized = clamp(max(0.0, distance) / VISIBLE_DISTANCE, 0.0, 1.0)
        factor = normalized ** PERSPECTIVE_POWER
        radius = lerp(TUNNEL_NEAR_RADIUS, TUNNEL_FAR_RADIUS, factor)
        scale = max(0.01, 1.0 - factor)
        return Projection(distance, factor, radius, scale, visible)

    @staticmethod
    def point(angle: float, radius: float) -> tuple[int, int]:
        radians = math.radians(angle)
        return (
            round(TUNNEL_CENTER_X + math.cos(radians) * radius),
            round(TUNNEL_CENTER_Y + math.sin(radians) * radius),
        )

    def arc_points(
        self,
        start_angle: float,
        end_angle: float,
        radius: float,
        steps: int = 10,
    ) -> list[tuple[int, int]]:
        if end_angle < start_angle:
            end_angle += 360.0
        return [
            self.point(lerp(start_angle, end_angle, index / steps), radius)
            for index in range(steps + 1)
        ]


class PlayerController:
    def __init__(self) -> None:
        self.angle = PLAYER_START_ANGLE
        self.velocity = 0.0
        self.input_direction = 0

    def reset(self) -> None:
        self.angle = PLAYER_START_ANGLE
        self.velocity = 0.0
        self.input_direction = 0

    def set_input(self, direction: int) -> None:
        self.input_direction = max(-1, min(1, int(direction)))

    def update(self, dt: float) -> None:
        target = self.input_direction * PLAYER_ANGULAR_SPEED
        change = PLAYER_ANGULAR_ACCELERATION * dt

        if self.velocity < target:
            self.velocity = min(target, self.velocity + change)
        elif self.velocity > target:
            self.velocity = max(target, self.velocity - change)

        if self.input_direction == 0:
            friction = PLAYER_ANGULAR_FRICTION * 60.0 * dt
            if self.velocity > 0:
                self.velocity = max(0.0, self.velocity - friction)
            elif self.velocity < 0:
                self.velocity = min(0.0, self.velocity + friction)

        self.angle = normalize_angle(self.angle + self.velocity * dt)


@dataclass
class TunnelObstacle:
    kind: str
    distance: float
    opening_angle: float = PLAYER_START_ANGLE
    opening_width: float = 70.0
    rotation_speed: float = 0.0
    movement_amplitude: float = 0.0
    movement_speed: float = 0.0
    phase: float = 0.0
    colour: tuple[int, int, int] = RED
    secondary_colour: tuple[int, int, int] = ORANGE
    thickness: float = 14.0
    arms: int = 2
    metadata: dict[str, object] = field(default_factory=dict)
    active: bool = True
    passed: bool = False
    hit: bool = False
    animation_time: float = 0.0

    @property
    def lethal(self) -> bool:
        return self.kind != OBSTACLE_FINISH

    def current_opening_angle(self) -> float:
        angle = self.opening_angle + self.rotation_speed * self.animation_time
        if self.movement_amplitude:
            angle += math.sin(
                self.animation_time * max(0.1, self.movement_speed) + self.phase
            ) * self.movement_amplitude
        return normalize_angle(angle)

    def current_opening_width(self) -> float:
        if self.kind == OBSTACLE_SHUTTER:
            pulse = (math.sin(self.animation_time * 2.8 + self.phase) + 1.0) / 2.0
            return max(22.0, self.opening_width * (0.45 + pulse * 0.55))
        if self.kind == OBSTACLE_PULSE:
            pulse = (math.sin(self.animation_time * 4.5 + self.phase) + 1.0) / 2.0
            return max(18.0, self.opening_width * (0.55 + pulse * 0.45))
        return self.opening_width

    def update(self, dt: float, forward_speed: float) -> None:
        if not self.active:
            return
        self.animation_time += dt
        self.distance -= forward_speed * dt
        if self.distance < -14.0:
            self.active = False
            self.passed = True

    def _inside_opening(self, player_angle: float, center: float, width: float) -> bool:
        return abs(shortest_angle_difference(center, player_angle)) <= max(
            0.0,
            width / 2.0 - PLAYER_COLLISION_HALF_WIDTH,
        )

    def is_safe(self, player_angle: float) -> bool:
        center = self.current_opening_angle()
        width = self.current_opening_width()

        if self.kind in (OBSTACLE_GATE, OBSTACLE_SHUTTER, OBSTACLE_SLIDER, OBSTACLE_PULSE, OBSTACLE_ZIGZAG):
            return self._inside_opening(player_angle, center, width)

        if self.kind == OBSTACLE_DOUBLE_GATE:
            return (
                self._inside_opening(player_angle, center, width)
                or self._inside_opening(player_angle, normalize_angle(center + 180.0), width)
            )

        if self.kind in (OBSTACLE_BAR, OBSTACLE_CROSS, OBSTACLE_FAN):
            arm_count = max(1, self.arms)
            arm_width = self.thickness
            base = center
            for arm in range(arm_count):
                arm_angle = normalize_angle(base + arm * (360.0 / arm_count))
                difference = abs(shortest_angle_difference(arm_angle, player_angle))
                if difference <= arm_width / 2.0 + PLAYER_COLLISION_HALF_WIDTH:
                    return False
            return True

        if self.kind == OBSTACLE_FINISH:
            return True

        return False

    def collides(self, player_angle: float) -> bool:
        if not self.active or self.hit or not self.lethal:
            return False
        depth = float(self.metadata.get("collision_depth", 4.0))
        if -1.0 <= self.distance <= depth and not self.is_safe(player_angle):
            self.hit = True
            return True
        return False

    def reached_finish(self) -> bool:
        return self.kind == OBSTACLE_FINISH and self.distance <= 0.0

    def draw(self, surface: pygame.Surface, projector: TunnelProjector) -> None:
        projection = projector.project_distance(self.distance)
        if not projection.visible:
            return

        radius = projection.radius
        alpha_factor = clamp(1.0 - projection.factor * 0.72, 0.25, 1.0)
        colour = tuple(round(channel * alpha_factor) for channel in self.colour)
        secondary = tuple(round(channel * alpha_factor) for channel in self.secondary_colour)
        line_width = max(2, round(self.thickness * projection.scale))

        if self.kind == OBSTACLE_FINISH:
            pygame.draw.circle(surface, GREEN, (TUNNEL_CENTER_X, TUNNEL_CENTER_Y), round(radius), max(2, line_width))
            return

        if self.kind in (OBSTACLE_GATE, OBSTACLE_SHUTTER, OBSTACLE_SLIDER, OBSTACLE_PULSE, OBSTACLE_ZIGZAG, OBSTACLE_DOUBLE_GATE):
            center = self.current_opening_angle()
            width = self.current_opening_width()
            openings = [(center, width)]
            if self.kind == OBSTACLE_DOUBLE_GATE:
                openings.append((normalize_angle(center + 180.0), width))

            blocked = self._blocked_arc_segments(openings)
            for start, end in blocked:
                points = projector.arc_points(start, end, radius, max(4, round((end - start) / 8)))
                if len(points) >= 2:
                    pygame.draw.lines(surface, colour, False, points, line_width)
                    inner_radius = max(1.0, radius - line_width * 1.7)
                    inner_points = projector.arc_points(start, end, inner_radius, max(4, round((end - start) / 8)))
                    pygame.draw.lines(surface, secondary, False, inner_points, max(1, line_width // 3))
            return

        if self.kind in (OBSTACLE_BAR, OBSTACLE_CROSS, OBSTACLE_FAN):
            arm_count = max(1, self.arms)
            center = self.current_opening_angle()
            inner = max(0.0, radius * 0.08)
            for arm in range(arm_count):
                angle = center + arm * 360.0 / arm_count
                start = projector.point(angle, inner)
                end = projector.point(angle, radius)
                pygame.draw.line(surface, colour, start, end, line_width)
                pygame.draw.circle(surface, secondary, end, max(2, line_width // 2))
            pygame.draw.circle(surface, WHITE, (TUNNEL_CENTER_X, TUNNEL_CENTER_Y), max(3, line_width // 2))

    @staticmethod
    def _blocked_arc_segments(openings: list[tuple[float, float]]) -> list[tuple[float, float]]:
        intervals: list[tuple[float, float]] = []
        for center, width in openings:
            start = normalize_angle(center - width / 2.0)
            end = normalize_angle(center + width / 2.0)
            if start <= end:
                intervals.append((start, end))
            else:
                intervals.append((start, 360.0))
                intervals.append((0.0, end))

        intervals.sort()
        merged: list[list[float]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)

        blocked: list[tuple[float, float]] = []
        cursor = 0.0
        for start, end in merged:
            if start > cursor:
                blocked.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < 360.0:
            blocked.append((cursor, 360.0))
        return blocked


@dataclass
class Particle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    colour: tuple[int, int, int]
    lifetime: float
    radius: float
    remaining: float

    @classmethod
    def create(cls, position, velocity, colour, lifetime, radius):
        return cls(pygame.Vector2(position), pygame.Vector2(velocity), colour, lifetime, radius, lifetime)

    def update(self, dt: float) -> None:
        self.remaining -= dt
        self.position += self.velocity * dt
        self.velocity *= max(0.0, 1.0 - 1.8 * dt)

    @property
    def active(self) -> bool:
        return self.remaining > 0.0

    def draw(self, surface: pygame.Surface) -> None:
        ratio = clamp(self.remaining / self.lifetime, 0.0, 1.0)
        pygame.draw.circle(
            surface,
            tuple(round(channel * ratio) for channel in self.colour),
            (round(self.position.x), round(self.position.y)),
            max(1, round(self.radius * ratio)),
        )


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def clear(self) -> None:
        self.particles.clear()

    def crash(self, amount: int = 80) -> None:
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 460)
            self.particles.append(Particle.create(
                (TUNNEL_CENTER_X, TUNNEL_CENTER_Y),
                (math.cos(angle) * speed, math.sin(angle) * speed),
                random.choice((CYAN, BLUE, ORANGE, YELLOW, WHITE)),
                random.uniform(0.35, 1.1),
                random.uniform(2.0, 7.0),
            ))

    def speed_spark(self, player_angle: float, intensity: float) -> None:
        if random.random() > clamp(intensity, 0.05, 0.75):
            return
        radians = math.radians(player_angle)
        start = pygame.Vector2(
            TUNNEL_CENTER_X + math.cos(radians) * (TUNNEL_NEAR_RADIUS * 0.72),
            TUNNEL_CENTER_Y + math.sin(radians) * (TUNNEL_NEAR_RADIUS * 0.72),
        )
        inward = pygame.Vector2(TUNNEL_CENTER_X, TUNNEL_CENTER_Y) - start
        if inward.length_squared():
            inward.scale_to_length(random.uniform(80, 170))
        self.particles.append(Particle.create(start, inward, CYAN, random.uniform(0.2, 0.5), random.uniform(1.5, 3.5)))

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)
        self.particles = [particle for particle in self.particles if particle.active][-450:]

    def draw(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)


class TunnelWorld:
    def __init__(self) -> None:
        self.projector = TunnelProjector()
        self.player = PlayerController()
        self.obstacles: list[TunnelObstacle] = []
        self.particles = ParticleSystem()
        self.distance = 0.0
        self.speed = 0.0
        self.crashed = False
        self.finished = False
        self.passed_obstacles = 0

    def reset(self, speed: float) -> None:
        self.player.reset()
        self.obstacles.clear()
        self.particles.clear()
        self.distance = 0.0
        self.speed = speed
        self.crashed = False
        self.finished = False
        self.passed_obstacles = 0

    def add_obstacle(self, obstacle: TunnelObstacle) -> None:
        self.obstacles.append(obstacle)

    def extend(self, obstacles: Iterable[TunnelObstacle]) -> None:
        self.obstacles.extend(obstacles)

    def update(self, dt: float) -> list[str]:
        events: list[str] = []
        if self.crashed or self.finished:
            self.particles.update(dt)
            return events

        self.player.update(dt)
        travelled = self.speed * dt
        self.distance += travelled

        for obstacle in self.obstacles:
            was_active = obstacle.active
            obstacle.update(dt, self.speed)
            if was_active and obstacle.passed:
                self.passed_obstacles += 1
                events.append("passed")

            if obstacle.reached_finish():
                self.finished = True
                events.append("finish")
                break

            if obstacle.collides(self.player.angle):
                self.crashed = True
                self.particles.crash()
                events.append("crash")
                break

        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.active]
        self.particles.speed_spark(self.player.angle, self.speed / 120.0)
        self.particles.update(dt)
        return events

    def draw_obstacles(self, surface: pygame.Surface) -> None:
        for obstacle in sorted(self.obstacles, key=lambda item: item.distance, reverse=True):
            obstacle.draw(surface, self.projector)
        self.particles.draw(surface)
