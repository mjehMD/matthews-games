from __future__ import annotations

import math

import pygame

from config import (
    ARMOR_BLUE,
    BLACK,
    CYAN,
    DARK_GREY,
    DARK_GREEN,
    ENEMY_TYPES,
    HEALTH_GREEN,
    MAP_LEFT,
    MAP_TOP,
    PATH_TILES,
    RED,
    TILE_SIZE,
    TOWER_TYPES,
    WHITE,
    YELLOW,
)


# ============================================================
# GENERAL VISUAL COLOURS
# ============================================================

METAL_DARK = (36, 42, 39)
METAL_MID = (72, 82, 74)
METAL_LIGHT = (125, 137, 123)

MILITARY_GREEN = (57, 83, 52)
MILITARY_LIGHT = (91, 118, 76)
MILITARY_DARK = (35, 54, 34)

WINDOW_BLUE = (98, 174, 195)
WINDOW_DARK = (35, 83, 101)

GROUND_SHADOW = (14, 18, 15)
TRACK_DARK = (28, 31, 29)

MUZZLE_YELLOW = (255, 225, 93)
MUZZLE_ORANGE = (255, 139, 45)

SUPPLY_BROWN = (117, 84, 51)
SUPPLY_LIGHT = (165, 124, 72)

INTEL_PURPLE = (91, 61, 121)
INTEL_LIGHT = (155, 110, 187)

FACTORY_GREY = (82, 91, 83)
FACTORY_LIGHT = (128, 137, 126)

HELIPAD_GREY = (70, 79, 76)
HELIPAD_EDGE = (177, 188, 181)

FRIENDLY_GREEN = (61, 112, 57)
FRIENDLY_LIGHT = (100, 153, 83)


# ============================================================
# DRAWING HELPERS
# ============================================================

def draw_rotated_polygon(
    surface: pygame.Surface,
    points: list[tuple[float, float]],
    center: tuple[int, int],
    angle: float,
    colour: tuple[int, int, int],
) -> None:
    """
    Draw a polygon rotated around its local origin.
    """

    cosine = math.cos(angle)
    sine = math.sin(angle)

    rotated_points: list[tuple[int, int]] = []

    for point_x, point_y in points:
        rotated_x = point_x * cosine - point_y * sine
        rotated_y = point_x * sine + point_y * cosine

        rotated_points.append(
            (
                round(center[0] + rotated_x),
                round(center[1] + rotated_y),
            )
        )

    pygame.draw.polygon(
        surface,
        colour,
        rotated_points,
    )


def draw_shadow(
    surface: pygame.Surface,
    center: tuple[int, int],
    width: int,
    height: int,
) -> None:
    shadow_surface = pygame.Surface(
        (width + 10, height + 10),
        pygame.SRCALPHA,
    )

    pygame.draw.ellipse(
        shadow_surface,
        (0, 0, 0, 80),
        shadow_surface.get_rect(),
    )

    surface.blit(
        shadow_surface,
        (
            center[0] - shadow_surface.get_width() // 2,
            center[1] - shadow_surface.get_height() // 2 + 8,
        ),
    )


def draw_muzzle_flash(
    surface: pygame.Surface,
    position: tuple[int, int],
    direction: pygame.Vector2,
    size: int = 8,
) -> None:
    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)

    direction = direction.normalize()

    tip = pygame.Vector2(position)
    side = pygame.Vector2(-direction.y, direction.x)

    outer_points = [
        tip + direction * size,
        tip - direction * (size * 0.35) + side * (size * 0.45),
        tip - direction * (size * 0.15),
        tip - direction * (size * 0.35) - side * (size * 0.45),
    ]

    inner_points = [
        tip + direction * (size * 0.65),
        tip - direction * (size * 0.15) + side * (size * 0.25),
        tip - direction * (size * 0.05),
        tip - direction * (size * 0.15) - side * (size * 0.25),
    ]

    pygame.draw.polygon(
        surface,
        MUZZLE_ORANGE,
        [
            (round(point.x), round(point.y))
            for point in outer_points
        ],
    )

    pygame.draw.polygon(
        surface,
        MUZZLE_YELLOW,
        [
            (round(point.x), round(point.y))
            for point in inner_points
        ],
    )


# ============================================================
# PATH
# ============================================================

def tile_center(tile: tuple[int, int]) -> pygame.Vector2:
    column, row = tile

    return pygame.Vector2(
        MAP_LEFT + column * TILE_SIZE + TILE_SIZE // 2,
        MAP_TOP + row * TILE_SIZE + TILE_SIZE // 2,
    )


PATH_POINTS = [
    tile_center(tile)
    for tile in PATH_TILES
]


# ============================================================
# ENEMY
# ============================================================

class Enemy:
    def __init__(
        self,
        enemy_type: str,
        wave: int,
        health_multiplier: float,
        speed_multiplier: float,
        reward_multiplier: float,
    ):
        data = ENEMY_TYPES[enemy_type]

        self.enemy_type = enemy_type
        self.name = str(data["name"])
        self.wave = max(1, int(wave))

        health_scale = (
            1.0
            + max(0, wave - 1) * 0.085
        )

        speed_scale = (
            1.0
            + min(
                0.55,
                max(0, wave - 1) * 0.011,
            )
        )

        self.max_health = float(
            data["health"]
            * health_multiplier
            * health_scale
        )

        self.health = self.max_health
        self.armor = float(
            data.get("armor", 0)
        )

        self.base_speed = float(
            data["speed"]
            * speed_multiplier
            * speed_scale
        )

        self.current_speed = self.base_speed

        self.reward = max(
            1,
            int(
                data["reward"]
                * reward_multiplier
            ),
        )

        self.base_damage = max(
            1,
            int(data["base_damage"]),
        )

        self.colour = data["colour"]
        self.size = int(data["size"])

        self.position = pygame.Vector2(
            PATH_POINTS[0]
        )

        self.path_index = 1

        self.dead = False
        self.reached_base = False

        self.slow_multiplier = 1.0
        self.slow_until = 0

        self.damage_flash_until = 0
        self.last_direction = pygame.Vector2(1, 0)

        self.animation_offset = (
            id(self) % 1000
        )

    def apply_slow(
        self,
        multiplier: float,
        duration_ms: int,
        current_time: int,
    ) -> None:
        multiplier = max(
            0.2,
            min(1.0, multiplier),
        )

        self.slow_multiplier = min(
            self.slow_multiplier,
            multiplier,
        )

        self.slow_until = max(
            self.slow_until,
            current_time + duration_ms,
        )

    def update(
        self,
        time_scale: float,
        current_time: int,
    ) -> None:
        if self.dead or self.reached_base:
            return

        if current_time >= self.slow_until:
            self.slow_multiplier = 1.0

        self.current_speed = (
            self.base_speed
            * self.slow_multiplier
        )

        if self.path_index >= len(PATH_POINTS):
            self.reached_base = True
            return

        target = PATH_POINTS[
            self.path_index
        ]

        direction = target - self.position
        distance = direction.length()

        movement = (
            self.current_speed
            * time_scale
        )

        if distance <= movement:
            self.position = pygame.Vector2(target)
            self.path_index += 1

            if self.path_index >= len(PATH_POINTS):
                self.reached_base = True

        elif distance > 0:
            normalized = direction.normalize()

            self.last_direction = normalized

            self.position += (
                normalized
                * movement
            )

    def take_damage(
        self,
        raw_damage: float,
        armor_piercing: float = 0,
    ) -> float:
        effective_armor = max(
            0.0,
            self.armor - armor_piercing,
        )

        actual_damage = max(
            1.0,
            raw_damage - effective_armor,
        )

        self.health -= actual_damage

        self.damage_flash_until = (
            pygame.time.get_ticks()
            + 80
        )

        if self.health <= 0:
            self.health = 0
            self.dead = True

        return actual_damage

    def progress_value(self) -> float:
        progress = float(
            self.path_index
        )

        if (
            0
            < self.path_index
            < len(PATH_POINTS)
        ):
            previous = PATH_POINTS[
                self.path_index - 1
            ]

            next_point = PATH_POINTS[
                self.path_index
            ]

            segment_length = (
                previous.distance_to(
                    next_point
                )
            )

            if segment_length > 0:
                progress += min(
                    1.0,
                    previous.distance_to(
                        self.position
                    )
                    / segment_length,
                )

        return progress

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        center = (
            round(self.position.x),
            round(self.position.y),
        )

        current_time = pygame.time.get_ticks()

        colour = (
            WHITE
            if current_time
            < self.damage_flash_until
            else self.colour
        )

        if self.enemy_type in (
            "jeep",
            "tank",
            "boss",
        ):
            self.draw_vehicle(
                surface,
                center,
                colour,
            )
        else:
            self.draw_soldier(
                surface,
                center,
                colour,
                current_time,
            )

        self.draw_health_bars(
            surface,
            center,
        )

        if self.slow_multiplier < 1.0:
            pulse = (
                3
                + int(
                    math.sin(
                        current_time / 100
                    )
                    * 2
                )
            )

            pygame.draw.circle(
                surface,
                CYAN,
                center,
                self.size + 6 + pulse,
                width=2,
            )


    def draw_soldier(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        colour: tuple[int, int, int],
        current_time: int,
    ) -> None:
        draw_shadow(
            surface,
            center,
            self.size * 2,
            self.size,
        )

        bob = int(
            math.sin(
                (
                    current_time
                    + self.animation_offset
                )
                / 110
            )
            * 2
        )

        body_center = (
            center[0],
            center[1] + bob,
        )

        body_rect = pygame.Rect(
            0,
            0,
            self.size + 4,
            self.size + 8,
        )

        body_rect.center = (
            body_center[0],
            body_center[1] + 5,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            body_rect.inflate(4, 4),
            border_radius=7,
        )

        pygame.draw.rect(
            surface,
            colour,
            body_rect,
            border_radius=7,
        )

        helmet_center = (
            body_center[0],
            body_center[1] - 8,
        )

        pygame.draw.circle(
            surface,
            BLACK,
            helmet_center,
            max(8, self.size // 2 + 2),
        )

        pygame.draw.circle(
            surface,
            DARK_GREEN,
            helmet_center,
            max(7, self.size // 2),
        )

        helmet_brim = pygame.Rect(
            helmet_center[0] - self.size // 2 - 3,
            helmet_center[1],
            self.size + 6,
            5,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            helmet_brim,
            border_radius=2,
        )

        face = pygame.Rect(
            helmet_center[0] - 5,
            helmet_center[1] + 1,
            10,
            8,
        )

        pygame.draw.rect(
            surface,
            (215, 181, 133),
            face,
            border_radius=3,
        )

        direction = self.last_direction

        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)

        perpendicular = pygame.Vector2(
            -direction.y,
            direction.x,
        )

        gun_start = (
            pygame.Vector2(body_center)
            + perpendicular * 3
        )

        gun_end = (
            gun_start
            + direction * (self.size + 10)
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(gun_start.x),
                round(gun_start.y),
            ),
            (
                round(gun_end.x),
                round(gun_end.y),
            ),
            width=4,
        )

        pygame.draw.circle(
            surface,
            METAL_MID,
            (
                round(gun_start.x),
                round(gun_start.y),
            ),
            3,
        )

        left_leg = (
            body_rect.centerx - 5,
            body_rect.bottom + 5,
        )

        right_leg = (
            body_rect.centerx + 5,
            body_rect.bottom + 5,
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                body_rect.centerx - 3,
                body_rect.bottom - 1,
            ),
            left_leg,
            width=4,
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                body_rect.centerx + 3,
                body_rect.bottom - 1,
            ),
            right_leg,
            width=4,
        )

    def draw_vehicle(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        colour: tuple[int, int, int],
    ) -> None:
        direction = self.last_direction

        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)

        angle = math.atan2(
            direction.y,
            direction.x,
        )

        if self.enemy_type == "jeep":
            self.draw_jeep(
                surface,
                center,
                colour,
                angle,
            )
        else:
            self.draw_enemy_tank(
                surface,
                center,
                colour,
                angle,
                boss=(
                    self.enemy_type
                    == "boss"
                ),
            )

    def draw_jeep(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        colour: tuple[int, int, int],
        angle: float,
    ) -> None:
        draw_shadow(
            surface,
            center,
            48,
            24,
        )

        body_points = [
            (-22, -11),
            (15, -11),
            (23, -5),
            (23, 9),
            (-22, 9),
        ]

        draw_rotated_polygon(
            surface,
            body_points,
            center,
            angle,
            BLACK,
        )

        inner_points = [
            (-19, -8),
            (13, -8),
            (19, -3),
            (19, 6),
            (-19, 6),
        ]

        draw_rotated_polygon(
            surface,
            inner_points,
            center,
            angle,
            colour,
        )

        forward = pygame.Vector2(
            math.cos(angle),
            math.sin(angle),
        )

        side = pygame.Vector2(
            -forward.y,
            forward.x,
        )

        cabin_center = (
            pygame.Vector2(center)
            - forward * 3
        )

        cabin_points = [
            (-8, -7),
            (8, -7),
            (8, 7),
            (-8, 7),
        ]

        draw_rotated_polygon(
            surface,
            cabin_points,
            (
                round(cabin_center.x),
                round(cabin_center.y),
            ),
            angle,
            WINDOW_DARK,
        )

        cabin_inner = [
            (-5, -4),
            (5, -4),
            (5, 4),
            (-5, 4),
        ]

        draw_rotated_polygon(
            surface,
            cabin_inner,
            (
                round(cabin_center.x),
                round(cabin_center.y),
            ),
            angle,
            WINDOW_BLUE,
        )

        for front_offset in (-12, 12):
            for side_offset in (-10, 10):
                wheel_center = (
                    pygame.Vector2(center)
                    + forward * front_offset
                    + side * side_offset
                )

                pygame.draw.circle(
                    surface,
                    TRACK_DARK,
                    (
                        round(wheel_center.x),
                        round(wheel_center.y),
                    ),
                    4,
                )

        turret_center = (
            pygame.Vector2(center)
            + forward * 5
        )

        pygame.draw.circle(
            surface,
            METAL_DARK,
            (
                round(turret_center.x),
                round(turret_center.y),
            ),
            5,
        )

        gun_end = (
            turret_center
            + forward * 15
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(turret_center.x),
                round(turret_center.y),
            ),
            (
                round(gun_end.x),
                round(gun_end.y),
            ),
            width=3,
        )

    def draw_enemy_tank(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        colour: tuple[int, int, int],
        angle: float,
        boss: bool,
    ) -> None:
        body_length = 64 if boss else 50
        body_width = 36 if boss else 28

        forward = pygame.Vector2(
            math.cos(angle),
            math.sin(angle),
        )

        side = pygame.Vector2(
            -forward.y,
            forward.x,
        )

        draw_shadow(
            surface,
            center,
            body_length,
            body_width,
        )

        tread_length = body_length
        tread_width = 9 if boss else 7
        tread_offset = (
            body_width / 2
            - tread_width / 2
        )

        for side_multiplier in (-1, 1):
            tread_center = (
                pygame.Vector2(center)
                + side
                * tread_offset
                * side_multiplier
            )

            outer_tread_points = [
                (
                    -tread_length / 2,
                    -tread_width / 2 - 2,
                ),
                (
                    tread_length / 2,
                    -tread_width / 2 - 2,
                ),
                (
                    tread_length / 2,
                    tread_width / 2 + 2,
                ),
                (
                    -tread_length / 2,
                    tread_width / 2 + 2,
                ),
            ]

            draw_rotated_polygon(
                surface,
                outer_tread_points,
                (
                    round(tread_center.x),
                    round(tread_center.y),
                ),
                angle,
                BLACK,
            )

            inner_tread_points = [
                (
                    -tread_length / 2 + 2,
                    -tread_width / 2,
                ),
                (
                    tread_length / 2 - 2,
                    -tread_width / 2,
                ),
                (
                    tread_length / 2 - 2,
                    tread_width / 2,
                ),
                (
                    -tread_length / 2 + 2,
                    tread_width / 2,
                ),
            ]

            draw_rotated_polygon(
                surface,
                inner_tread_points,
                (
                    round(tread_center.x),
                    round(tread_center.y),
                ),
                angle,
                TRACK_DARK,
            )

            wheel_count = (
                6 if boss else 5
            )

            for wheel_index in range(
                wheel_count
            ):
                progress = (
                    wheel_index
                    / max(
                        1,
                        wheel_count - 1,
                    )
                )

                wheel_position = (
                    tread_center
                    - forward
                    * (
                        tread_length / 2
                        - 7
                    )
                    + forward
                    * progress
                    * (
                        tread_length - 14
                    )
                )

                pygame.draw.circle(
                    surface,
                    BLACK,
                    (
                        round(wheel_position.x),
                        round(wheel_position.y),
                    ),
                    4 if boss else 3,
                )

                pygame.draw.circle(
                    surface,
                    METAL_MID,
                    (
                        round(wheel_position.x),
                        round(wheel_position.y),
                    ),
                    2,
                )

        hull_points = [
            (
                -body_length / 2 + 3,
                -body_width / 2 + 4,
            ),
            (
                body_length / 2 - 9,
                -body_width / 2 + 4,
            ),
            (
                body_length / 2,
                -body_width / 4,
            ),
            (
                body_length / 2,
                body_width / 4,
            ),
            (
                body_length / 2 - 9,
                body_width / 2 - 4,
            ),
            (
                -body_length / 2 + 3,
                body_width / 2 - 4,
            ),
        ]

        draw_rotated_polygon(
            surface,
            hull_points,
            center,
            angle,
            BLACK,
        )

        inner_hull_points = [
            (
                -body_length / 2 + 7,
                -body_width / 2 + 7,
            ),
            (
                body_length / 2 - 11,
                -body_width / 2 + 7,
            ),
            (
                body_length / 2 - 4,
                -body_width / 5,
            ),
            (
                body_length / 2 - 4,
                body_width / 5,
            ),
            (
                body_length / 2 - 11,
                body_width / 2 - 7,
            ),
            (
                -body_length / 2 + 7,
                body_width / 2 - 7,
            ),
        ]

        draw_rotated_polygon(
            surface,
            inner_hull_points,
            center,
            angle,
            colour,
        )

        engine_center = (
            pygame.Vector2(center)
            - forward
            * (
                body_length
                * 0.27
            )
        )

        engine_length = (
            18 if boss else 14
        )

        engine_width = (
            22 if boss else 17
        )

        engine_points = [
            (
                -engine_length / 2,
                -engine_width / 2,
            ),
            (
                engine_length / 2,
                -engine_width / 2,
            ),
            (
                engine_length / 2,
                engine_width / 2,
            ),
            (
                -engine_length / 2,
                engine_width / 2,
            ),
        ]

        draw_rotated_polygon(
            surface,
            engine_points,
            (
                round(engine_center.x),
                round(engine_center.y),
            ),
            angle,
            METAL_DARK,
        )

        for side_offset in (
            -5,
            0,
            5,
        ):
            vent_center = (
                engine_center
                + side * side_offset
            )

            vent_start = (
                vent_center
                - forward * 5
            )

            vent_end = (
                vent_center
                + forward * 5
            )

            pygame.draw.line(
                surface,
                METAL_LIGHT,
                (
                    round(vent_start.x),
                    round(vent_start.y),
                ),
                (
                    round(vent_end.x),
                    round(vent_end.y),
                ),
                width=1,
            )

        turret_center = (
            pygame.Vector2(center)
            + forward * 3
        )

        turret_length = (
            29 if boss else 22
        )

        turret_width = (
            24 if boss else 18
        )

        turret_points = [
            (
                -turret_length / 2,
                -turret_width / 2,
            ),
            (
                turret_length / 2 - 4,
                -turret_width / 2,
            ),
            (
                turret_length / 2,
                -turret_width / 3,
            ),
            (
                turret_length / 2,
                turret_width / 3,
            ),
            (
                turret_length / 2 - 4,
                turret_width / 2,
            ),
            (
                -turret_length / 2,
                turret_width / 2,
            ),
        ]

        draw_rotated_polygon(
            surface,
            turret_points,
            (
                round(turret_center.x),
                round(turret_center.y),
            ),
            angle,
            BLACK,
        )

        inner_turret_points = [
            (
                -turret_length / 2 + 3,
                -turret_width / 2 + 3,
            ),
            (
                turret_length / 2 - 6,
                -turret_width / 2 + 3,
            ),
            (
                turret_length / 2 - 3,
                -turret_width / 4,
            ),
            (
                turret_length / 2 - 3,
                turret_width / 4,
            ),
            (
                turret_length / 2 - 6,
                turret_width / 2 - 3,
            ),
            (
                -turret_length / 2 + 3,
                turret_width / 2 - 3,
            ),
        ]

        draw_rotated_polygon(
            surface,
            inner_turret_points,
            (
                round(turret_center.x),
                round(turret_center.y),
            ),
            angle,
            METAL_DARK,
        )

        barrel_start = (
            turret_center
            + forward
            * (
                turret_length / 3
            )
        )

        barrel_end = (
            turret_center
            + forward
            * (
                43 if boss else 34
            )
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(barrel_start.x),
                round(barrel_start.y),
            ),
            (
                round(barrel_end.x),
                round(barrel_end.y),
            ),
            width=8 if boss else 6,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                round(
                    barrel_start.x
                    + forward.x * 3
                ),
                round(
                    barrel_start.y
                    + forward.y * 3
                ),
            ),
            (
                round(barrel_end.x),
                round(barrel_end.y),
            ),
            width=3 if boss else 2,
        )

        hatch_center = (
            turret_center
            - side
            * (
                6 if boss else 4
            )
        )

        pygame.draw.circle(
            surface,
            BLACK,
            (
                round(hatch_center.x),
                round(hatch_center.y),
            ),
            7 if boss else 5,
        )

        pygame.draw.circle(
            surface,
            METAL_MID,
            (
                round(hatch_center.x),
                round(hatch_center.y),
            ),
            5 if boss else 3,
        )

        if boss:
            pygame.draw.circle(
                surface,
                RED,
                (
                    round(turret_center.x),
                    round(turret_center.y),
                ),
                5,
            )

            antenna_start = (
                turret_center
                - side * 10
            )

            antenna_end = (
                antenna_start
                - side * 15
                - forward * 3
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    round(antenna_start.x),
                    round(antenna_start.y),
                ),
                (
                    round(antenna_end.x),
                    round(antenna_end.y),
                ),
                width=2,
            )

            pygame.draw.circle(
                surface,
                RED,
                (
                    round(antenna_end.x),
                    round(antenna_end.y),
                ),
                3,
            )

    def draw_health_bars(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        bar_width = max(
            38,
            self.size * 2,
        )

        health_rect = pygame.Rect(
            center[0] - bar_width // 2,
            center[1] - self.size - 16,
            bar_width,
            6,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            health_rect.inflate(2, 2),
            border_radius=3,
        )

        pygame.draw.rect(
            surface,
            DARK_GREY,
            health_rect,
            border_radius=2,
        )

        health_ratio = (
            self.health / self.max_health
            if self.max_health > 0
            else 0
        )

        pygame.draw.rect(
            surface,
            HEALTH_GREEN,
            (
                health_rect.x,
                health_rect.y,
                round(
                    health_rect.width
                    * health_ratio
                ),
                health_rect.height,
            ),
            border_radius=2,
        )

        if self.armor > 0:
            armor_rect = pygame.Rect(
                health_rect.x,
                health_rect.y - 7,
                health_rect.width,
                4,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                armor_rect.inflate(2, 2),
                border_radius=2,
            )

            pygame.draw.rect(
                surface,
                DARK_GREY,
                armor_rect,
                border_radius=2,
            )

            pygame.draw.rect(
                surface,
                ARMOR_BLUE,
                (
                    armor_rect.x,
                    armor_rect.y,
                    round(
                        armor_rect.width
                        * min(
                            1.0,
                            self.armor / 10,
                        )
                    ),
                    armor_rect.height,
                ),
                border_radius=2,
            )


# ============================================================
# PROJECTILE
# ============================================================

class Projectile:
    def __init__(
        self,
        position: pygame.Vector2,
        target: Enemy,
        damage: float,
        speed: float,
        colour: tuple[int, int, int],
        projectile_type: str = "bullet",
        splash_radius: float = 0,
        armor_piercing: float = 0,
        slow_multiplier: float = 1.0,
        slow_duration_ms: int = 0,
    ):
        self.position = pygame.Vector2(
            position
        )

        self.previous_position = pygame.Vector2(
            position
        )

        self.target = target

        self.damage = damage
        self.speed = speed
        self.colour = colour

        self.projectile_type = (
            projectile_type
        )

        self.splash_radius = (
            splash_radius
        )

        self.armor_piercing = (
            armor_piercing
        )

        self.slow_multiplier = (
            slow_multiplier
        )

        self.slow_duration_ms = (
            slow_duration_ms
        )

        self.target_position = pygame.Vector2(
            target.position
        )

        self.dead = False

    @classmethod
    def from_tower(
        cls,
        tower: "Tower",
        target: Enemy,
    ) -> "Projectile":
        return cls(
            position=tower.position,
            target=target,
            damage=tower.damage,
            speed=tower.projectile_speed,
            colour=tower.colour,
            projectile_type=tower.projectile_type,
            splash_radius=tower.splash_radius,
            armor_piercing=tower.armor_piercing,
            slow_multiplier=tower.slow_multiplier,
            slow_duration_ms=tower.slow_duration_ms,
        )

    def update(
        self,
        enemies: list[Enemy],
        time_scale: float,
        current_time: int,
    ) -> None:
        if self.dead:
            return

        self.previous_position = pygame.Vector2(
            self.position
        )

        if (
            not self.target.dead
            and not self.target.reached_base
        ):
            self.target_position = pygame.Vector2(
                self.target.position
            )

        direction = (
            self.target_position
            - self.position
        )

        distance = direction.length()
        movement = self.speed * time_scale

        if distance <= movement + 6:
            self.impact(
                enemies,
                current_time,
            )

            self.dead = True
            return

        if distance > 0:
            self.position += (
                direction.normalize()
                * movement
            )

    def impact(
        self,
        enemies: list[Enemy],
        current_time: int,
    ) -> None:
        if self.splash_radius > 0:
            for enemy in enemies:
                if (
                    enemy.dead
                    or enemy.reached_base
                ):
                    continue

                if (
                    enemy.position.distance_to(
                        self.target_position
                    )
                    <= self.splash_radius
                ):
                    enemy.take_damage(
                        self.damage,
                        self.armor_piercing,
                    )

                    if (
                        self.slow_multiplier
                        < 1
                    ):
                        enemy.apply_slow(
                            self.slow_multiplier,
                            self.slow_duration_ms,
                            current_time,
                        )

        elif not self.target.dead:
            self.target.take_damage(
                self.damage,
                self.armor_piercing,
            )

            if self.slow_multiplier < 1:
                self.target.apply_slow(
                    self.slow_multiplier,
                    self.slow_duration_ms,
                    current_time,
                )

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        center = (
            round(self.position.x),
            round(self.position.y),
        )

        previous = (
            round(self.previous_position.x),
            round(self.previous_position.y),
        )

        if self.projectile_type == "shell":
            pygame.draw.line(
                surface,
                (80, 80, 80),
                previous,
                center,
                width=3,
            )

            pygame.draw.circle(
                surface,
                BLACK,
                center,
                8,
            )

            pygame.draw.circle(
                surface,
                self.colour,
                center,
                6,
            )

            pygame.draw.circle(
                surface,
                WHITE,
                (
                    center[0] - 2,
                    center[1] - 2,
                ),
                2,
            )

        elif self.projectile_type == "sniper":
            pygame.draw.line(
                surface,
                self.colour,
                previous,
                center,
                width=3,
            )

            pygame.draw.circle(
                surface,
                WHITE,
                center,
                4,
            )

        else:
            pygame.draw.line(
                surface,
                self.colour,
                previous,
                center,
                width=2,
            )

            pygame.draw.circle(
                surface,
                WHITE,
                center,
                3,
            )


# ============================================================
# FRIENDLY TANK
# ============================================================

class FriendlyTank:
    def __init__(
        self,
        factory: "Tower",
    ):
        self.factory = factory

        self.position = pygame.Vector2(
            PATH_POINTS[-1]
        )

        self.path_index = (
            len(PATH_POINTS) - 2
        )

        self.speed = (
            factory.friendly_tank_speed
        )

        self.damage = (
            factory.friendly_tank_damage
        )

        self.hits_remaining = (
            factory.friendly_tank_health
        )

        self.dead = False

        self.last_direction = pygame.Vector2(
            -1,
            0,
        )

        self.last_hit_times: dict[
            int,
            int,
        ] = {}

        self.hit_flash_until = 0

    def update(
        self,
        enemies: list[Enemy],
        time_scale: float,
        current_time: int,
    ) -> None:
        if self.dead:
            return

        if self.path_index < 0:
            self.dead = True
            return

        target = PATH_POINTS[
            self.path_index
        ]

        direction = target - self.position
        distance = direction.length()

        movement = (
            self.speed * time_scale
        )

        if distance <= movement:
            self.position = pygame.Vector2(
                target
            )

            self.path_index -= 1

        elif distance > 0:
            normalized = direction.normalize()

            self.last_direction = normalized

            self.position += (
                normalized * movement
            )

        for enemy in enemies:
            if (
                enemy.dead
                or enemy.reached_base
            ):
                continue

            enemy_key = id(enemy)

            if (
                self.position.distance_to(
                    enemy.position
                )
                <= enemy.size + 22
            ):
                last_hit = (
                    self.last_hit_times.get(
                        enemy_key,
                        0,
                    )
                )

                if (
                    current_time - last_hit
                    >= 650
                ):
                    enemy.take_damage(
                        self.damage,
                        armor_piercing=3,
                    )

                    self.last_hit_times[
                        enemy_key
                    ] = current_time

                    self.hits_remaining -= 1

                    self.hit_flash_until = (
                        current_time + 100
                    )

                    if (
                        self.hits_remaining
                        <= 0
                    ):
                        self.dead = True
                        break

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        center = (
            round(self.position.x),
            round(self.position.y),
        )

        direction = self.last_direction

        if direction.length_squared() == 0:
            direction = pygame.Vector2(
                -1,
                0,
            )

        direction = direction.normalize()

        angle = math.atan2(
            direction.y,
            direction.x,
        )

        side = pygame.Vector2(
            -direction.y,
            direction.x,
        )

        current_time = (
            pygame.time.get_ticks()
        )

        body_colour = (
            WHITE
            if current_time
            < self.hit_flash_until
            else FRIENDLY_GREEN
        )

        body_length = 50
        body_width = 28

        draw_shadow(
            surface,
            center,
            body_length,
            body_width,
        )

        tread_length = body_length
        tread_width = 7

        tread_offset = (
            body_width / 2
            - tread_width / 2
        )

        for side_multiplier in (-1, 1):
            tread_center = (
                pygame.Vector2(center)
                + side
                * tread_offset
                * side_multiplier
            )

            outer_tread_points = [
                (
                    -tread_length / 2,
                    -tread_width / 2 - 2,
                ),
                (
                    tread_length / 2,
                    -tread_width / 2 - 2,
                ),
                (
                    tread_length / 2,
                    tread_width / 2 + 2,
                ),
                (
                    -tread_length / 2,
                    tread_width / 2 + 2,
                ),
            ]

            draw_rotated_polygon(
                surface,
                outer_tread_points,
                (
                    round(tread_center.x),
                    round(tread_center.y),
                ),
                angle,
                BLACK,
            )

            inner_tread_points = [
                (
                    -tread_length / 2 + 2,
                    -tread_width / 2,
                ),
                (
                    tread_length / 2 - 2,
                    -tread_width / 2,
                ),
                (
                    tread_length / 2 - 2,
                    tread_width / 2,
                ),
                (
                    -tread_length / 2 + 2,
                    tread_width / 2,
                ),
            ]

            draw_rotated_polygon(
                surface,
                inner_tread_points,
                (
                    round(tread_center.x),
                    round(tread_center.y),
                ),
                angle,
                TRACK_DARK,
            )

            for wheel_index in range(5):
                progress = (
                    wheel_index / 4
                )

                wheel_position = (
                    tread_center
                    - direction
                    * (
                        tread_length / 2
                        - 7
                    )
                    + direction
                    * progress
                    * (
                        tread_length - 14
                    )
                )

                pygame.draw.circle(
                    surface,
                    BLACK,
                    (
                        round(wheel_position.x),
                        round(wheel_position.y),
                    ),
                    3,
                )

                pygame.draw.circle(
                    surface,
                    METAL_MID,
                    (
                        round(wheel_position.x),
                        round(wheel_position.y),
                    ),
                    2,
                )

        hull_points = [
            (-25, -10),
            (16, -10),
            (25, -5),
            (25, 5),
            (16, 10),
            (-25, 10),
        ]

        draw_rotated_polygon(
            surface,
            hull_points,
            center,
            angle,
            BLACK,
        )

        inner_hull = [
            (-21, -7),
            (14, -7),
            (21, -3),
            (21, 3),
            (14, 7),
            (-21, 7),
        ]

        draw_rotated_polygon(
            surface,
            inner_hull,
            center,
            angle,
            body_colour,
        )

        engine_center = (
            pygame.Vector2(center)
            - direction * 13
        )

        engine_points = [
            (-7, -8),
            (7, -8),
            (7, 8),
            (-7, 8),
        ]

        draw_rotated_polygon(
            surface,
            engine_points,
            (
                round(engine_center.x),
                round(engine_center.y),
            ),
            angle,
            MILITARY_DARK,
        )

        turret_center = (
            pygame.Vector2(center)
            + direction * 3
        )

        turret_points = [
            (-11, -8),
            (8, -8),
            (12, -4),
            (12, 4),
            (8, 8),
            (-11, 8),
        ]

        draw_rotated_polygon(
            surface,
            turret_points,
            (
                round(turret_center.x),
                round(turret_center.y),
            ),
            angle,
            BLACK,
        )

        inner_turret = [
            (-8, -5),
            (6, -5),
            (9, -3),
            (9, 3),
            (6, 5),
            (-8, 5),
        ]

        draw_rotated_polygon(
            surface,
            inner_turret,
            (
                round(turret_center.x),
                round(turret_center.y),
            ),
            angle,
            FRIENDLY_LIGHT,
        )

        barrel_start = (
            turret_center
            + direction * 6
        )

        barrel_end = (
            turret_center
            + direction * 34
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(barrel_start.x),
                round(barrel_start.y),
            ),
            (
                round(barrel_end.x),
                round(barrel_end.y),
            ),
            width=6,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                round(
                    barrel_start.x
                    + direction.x * 3
                ),
                round(
                    barrel_start.y
                    + direction.y * 3
                ),
            ),
            (
                round(barrel_end.x),
                round(barrel_end.y),
            ),
            width=2,
        )

        marking_center = (
            pygame.Vector2(center)
            - direction * 6
        )

        pygame.draw.circle(
            surface,
            YELLOW,
            (
                round(marking_center.x),
                round(marking_center.y),
            ),
            4,
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(marking_center.x - 3),
                round(marking_center.y),
            ),
            (
                round(marking_center.x + 3),
                round(marking_center.y),
            ),
            width=1,
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(marking_center.x),
                round(marking_center.y - 3),
            ),
            (
                round(marking_center.x),
                round(marking_center.y + 3),
            ),
            width=1,
        )

        health_ratio = max(
            0.0,
            min(
                1.0,
                self.hits_remaining
                / max(
                    1,
                    self.factory.friendly_tank_health,
                ),
            ),
        )

        bar_rect = pygame.Rect(
            center[0] - 23,
            center[1] - 28,
            46,
            5,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            bar_rect.inflate(2, 2),
            border_radius=2,
        )

        pygame.draw.rect(
            surface,
            DARK_GREY,
            bar_rect,
            border_radius=2,
        )

        pygame.draw.rect(
            surface,
            HEALTH_GREEN,
            (
                bar_rect.x,
                bar_rect.y,
                round(
                    bar_rect.width
                    * health_ratio
                ),
                bar_rect.height,
            ),
            border_radius=2,
        )

# ============================================================
# HELICOPTER
# ============================================================

class Helicopter:
    def __init__(
        self,
        pad: "Tower",
        index: int,
        total: int,
    ):
        self.pad = pad
        self.index = index

        self.angle = (
            math.tau
            * index
            / max(1, total)
        )

        self.position = pygame.Vector2(
            pad.position
        )

        self.previous_position = pygame.Vector2(
            pad.position
        )

        self.last_shot_time = 0
        self.last_target: Enemy | None = None

        self.rotor_angle = (
            index * 0.7
        )

        self.tail_rotor_angle = (
            index * 0.9
        )

        self.bob_offset = (
            index * 1.3
        )

        self.muzzle_flash_until = 0

    def update_position(
        self,
        time_scale: float,
    ) -> None:
        self.previous_position = pygame.Vector2(
            self.position
        )

        self.angle += (
            0.018
            * time_scale
        )

        self.rotor_angle += (
            0.34
            * time_scale
        )

        self.tail_rotor_angle += (
            0.52
            * time_scale
        )

        orbit_radius = (
            48
            + self.pad.level * 4
        )

        bob = (
            math.sin(
                self.angle * 3
                + self.bob_offset
            )
            * 3
        )

        self.position = pygame.Vector2(
            self.pad.position.x
            + math.cos(self.angle)
            * orbit_radius,
            self.pad.position.y
            + math.sin(self.angle)
            * orbit_radius
            + bob,
        )

    def find_target(
        self,
        enemies: list[Enemy],
    ) -> Enemy | None:
        valid = [
            enemy
            for enemy in enemies
            if (
                not enemy.dead
                and not enemy.reached_base
                and self.position.distance_to(
                    enemy.position
                )
                <= self.pad.helicopter_range
            )
        ]

        if not valid:
            self.last_target = None
            return None

        target = max(
            valid,
            key=lambda enemy: (
                enemy.progress_value()
            ),
        )

        self.last_target = target
        return target

    def update(
        self,
        enemies: list[Enemy],
        current_time: int,
        time_scale: float,
    ) -> Projectile | None:
        self.update_position(
            time_scale
        )

        if (
            current_time
            - self.last_shot_time
            < self.pad.helicopter_cooldown
        ):
            return None

        target = self.find_target(
            enemies
        )

        if target is None:
            return None

        self.last_shot_time = current_time

        self.muzzle_flash_until = (
            pygame.time.get_ticks()
            + 80
        )

        return Projectile(
            position=self.position,
            target=target,
            damage=self.pad.helicopter_damage,
            speed=13,
            colour=CYAN,
            projectile_type="bullet",
            armor_piercing=1.5,
        )

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        center = pygame.Vector2(
            round(self.position.x),
            round(self.position.y),
        )

        current_time = pygame.time.get_ticks()

        velocity = (
            self.position
            - self.previous_position
        )

        if velocity.length_squared() > 0:
            facing = velocity.normalize()

        elif (
            self.last_target is not None
            and not self.last_target.dead
        ):
            target_direction = (
                self.last_target.position
                - self.position
            )

            if (
                target_direction.length_squared()
                > 0
            ):
                facing = (
                    target_direction.normalize()
                )
            else:
                facing = pygame.Vector2(1, 0)

        else:
            facing = pygame.Vector2(
                math.cos(
                    self.angle
                    + math.pi / 2
                ),
                math.sin(
                    self.angle
                    + math.pi / 2
                ),
            )

        angle = math.atan2(
            facing.y,
            facing.x,
        )

        side = pygame.Vector2(
            -facing.y,
            facing.x,
        )

        draw_shadow(
            surface,
            (
                round(center.x),
                round(center.y + 10),
            ),
            46,
            18,
        )

        # Tail boom.
        tail_start = (
            center
            - facing * 8
        )

        tail_end = (
            center
            - facing * 34
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(tail_start.x),
                round(tail_start.y),
            ),
            (
                round(tail_end.x),
                round(tail_end.y),
            ),
            width=8,
        )

        pygame.draw.line(
            surface,
            MILITARY_GREEN,
            (
                round(tail_start.x),
                round(tail_start.y),
            ),
            (
                round(tail_end.x),
                round(tail_end.y),
            ),
            width=5,
        )

        # Tail fin.
        fin_points = [
            (
                tail_end
                + side * 2
            ),
            (
                tail_end
                - facing * 3
                + side * 11
            ),
            (
                tail_end
                + facing * 4
                + side * 4
            ),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(point.x),
                    round(point.y),
                )
                for point in fin_points
            ],
        )

        inner_fin = [
            (
                tail_end
                + side * 2
            ),
            (
                tail_end
                - facing * 2
                + side * 8
            ),
            (
                tail_end
                + facing * 3
                + side * 3
            ),
        ]

        pygame.draw.polygon(
            surface,
            MILITARY_LIGHT,
            [
                (
                    round(point.x),
                    round(point.y),
                )
                for point in inner_fin
            ],
        )

        # Main fuselage.
        fuselage_points = [
            (-17, -9),
            (7, -11),
            (17, -5),
            (19, 3),
            (10, 10),
            (-15, 9),
            (-21, 2),
        ]

        draw_rotated_polygon(
            surface,
            fuselage_points,
            (
                round(center.x),
                round(center.y),
            ),
            angle,
            BLACK,
        )

        inner_fuselage = [
            (-14, -7),
            (6, -8),
            (14, -4),
            (16, 2),
            (8, 7),
            (-13, 7),
            (-17, 1),
        ]

        draw_rotated_polygon(
            surface,
            inner_fuselage,
            (
                round(center.x),
                round(center.y),
            ),
            angle,
            MILITARY_GREEN,
        )

        # Cockpit.
        cockpit_center = (
            center
            + facing * 9
        )

        cockpit_points = [
            (-2, -7),
            (9, -5),
            (12, 0),
            (7, 6),
            (-3, 6),
        ]

        draw_rotated_polygon(
            surface,
            cockpit_points,
            (
                round(cockpit_center.x),
                round(cockpit_center.y),
            ),
            angle,
            WINDOW_DARK,
        )

        cockpit_inner = [
            (0, -5),
            (7, -3),
            (9, 0),
            (5, 4),
            (-1, 4),
        ]

        draw_rotated_polygon(
            surface,
            cockpit_inner,
            (
                round(cockpit_center.x),
                round(cockpit_center.y),
            ),
            angle,
            WINDOW_BLUE,
        )

        # Engine housing.
        engine_center = (
            center
            - facing * 4
        )

        pygame.draw.circle(
            surface,
            BLACK,
            (
                round(engine_center.x),
                round(engine_center.y),
            ),
            8,
        )

        pygame.draw.circle(
            surface,
            METAL_DARK,
            (
                round(engine_center.x),
                round(engine_center.y),
            ),
            6,
        )

        # Landing skids.
        for skid_offset in (-7, 7):
            skid_center = (
                center
                + side * skid_offset
                + pygame.Vector2(0, 8)
            )

            skid_start = (
                skid_center
                - facing * 13
            )

            skid_end = (
                skid_center
                + facing * 13
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    round(skid_start.x),
                    round(skid_start.y),
                ),
                (
                    round(skid_end.x),
                    round(skid_end.y),
                ),
                width=3,
            )

            support_start = (
                center
                + side * skid_offset
            )

            pygame.draw.line(
                surface,
                METAL_LIGHT,
                (
                    round(support_start.x),
                    round(support_start.y),
                ),
                (
                    round(skid_center.x),
                    round(skid_center.y),
                ),
                width=2,
            )

        # Weapon pods.
        for pod_offset in (-10, 10):
            pod_center = (
                center
                + side * pod_offset
                + facing * 2
            )

            pod_end = (
                pod_center
                + facing * 14
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    round(pod_center.x),
                    round(pod_center.y),
                ),
                (
                    round(pod_end.x),
                    round(pod_end.y),
                ),
                width=5,
            )

            pygame.draw.line(
                surface,
                METAL_MID,
                (
                    round(
                        pod_center.x
                        + facing.x * 2
                    ),
                    round(
                        pod_center.y
                        + facing.y * 2
                    ),
                ),
                (
                    round(pod_end.x),
                    round(pod_end.y),
                ),
                width=2,
            )

        # Main rotor.
        pygame.draw.circle(
            surface,
            BLACK,
            (
                round(center.x),
                round(center.y),
            ),
            4,
        )

        rotor_direction = pygame.Vector2(
            math.cos(self.rotor_angle),
            math.sin(self.rotor_angle),
        )

        rotor_side = pygame.Vector2(
            -rotor_direction.y,
            rotor_direction.x,
        )

        rotor_length = 33

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(
                    center.x
                    - rotor_direction.x
                    * rotor_length
                ),
                round(
                    center.y
                    - rotor_direction.y
                    * rotor_length
                ),
            ),
            (
                round(
                    center.x
                    + rotor_direction.x
                    * rotor_length
                ),
                round(
                    center.y
                    + rotor_direction.y
                    * rotor_length
                ),
            ),
            width=4,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                round(
                    center.x
                    - rotor_side.x
                    * rotor_length
                ),
                round(
                    center.y
                    - rotor_side.y
                    * rotor_length
                ),
            ),
            (
                round(
                    center.x
                    + rotor_side.x
                    * rotor_length
                ),
                round(
                    center.y
                    + rotor_side.y
                    * rotor_length
                ),
            ),
            width=3,
        )

        pygame.draw.circle(
            surface,
            YELLOW,
            (
                round(center.x),
                round(center.y),
            ),
            3,
        )

        # Tail rotor.
        tail_rotor_center = (
            tail_end
            - side
        )

        tail_rotor_direction = pygame.Vector2(
            math.cos(
                self.tail_rotor_angle
            ),
            math.sin(
                self.tail_rotor_angle
            ),
        )

        tail_rotor_side = pygame.Vector2(
            -tail_rotor_direction.y,
            tail_rotor_direction.x,
        )

        tail_rotor_length = 8

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(
                    tail_rotor_center.x
                    - tail_rotor_direction.x
                    * tail_rotor_length
                ),
                round(
                    tail_rotor_center.y
                    - tail_rotor_direction.y
                    * tail_rotor_length
                ),
            ),
            (
                round(
                    tail_rotor_center.x
                    + tail_rotor_direction.x
                    * tail_rotor_length
                ),
                round(
                    tail_rotor_center.y
                    + tail_rotor_direction.y
                    * tail_rotor_length
                ),
            ),
            width=2,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                round(
                    tail_rotor_center.x
                    - tail_rotor_side.x
                    * tail_rotor_length
                ),
                round(
                    tail_rotor_center.y
                    - tail_rotor_side.y
                    * tail_rotor_length
                ),
            ),
            (
                round(
                    tail_rotor_center.x
                    + tail_rotor_side.x
                    * tail_rotor_length
                ),
                round(
                    tail_rotor_center.y
                    + tail_rotor_side.y
                    * tail_rotor_length
                ),
            ),
            width=2,
        )

        if (
            current_time
            < self.muzzle_flash_until
        ):
            gun_position = (
                center
                + facing * 20
                + side * 9
            )

            draw_muzzle_flash(
                surface,
                (
                    round(gun_position.x),
                    round(gun_position.y),
                ),
                facing,
                size=9,
            )


# ============================================================
# TOWER / DEFENCE UNIT
# ============================================================

class Tower:
    TARGETING_MODES = (
        "first",
        "strongest",
        "closest",
        "last",
    )

    def __init__(
        self,
        tower_type: str,
        tile: tuple[int, int],
    ):
        data = TOWER_TYPES[
            tower_type
        ]

        self.tower_type = tower_type
        self.name = str(data["name"])
        self.tile = tile

        self.position = tile_center(
            tile
        )

        self.category = str(
            data["category"]
        )

        self.unit_kind = str(
            data["unit_kind"]
        )

        self.placement = str(
            data["placement"]
        )

        self.level = 1

        self.max_level = int(
            data.get(
                "max_level",
                4,
            )
        )

        self.total_spent = int(
            data["cost"]
        )

        self.colour = data["colour"]

        self.base_damage = float(
            data.get(
                "damage",
                0,
            )
        )

        self.base_range = float(
            data.get(
                "range",
                0,
            )
        )

        self.base_cooldown = int(
            data.get(
                "cooldown",
                0,
            )
        )

        self.projectile_speed = float(
            data.get(
                "projectile_speed",
                0,
            )
        )

        self.projectile_type = str(
            data.get(
                "projectile_type",
                "none",
            )
        )

        self.base_armor_piercing = float(
            data.get(
                "armor_piercing",
                0,
            )
        )

        self.base_splash_radius = float(
            data.get(
                "splash_radius",
                0,
            )
        )

        self.slow_multiplier = float(
            data.get(
                "slow_multiplier",
                1.0,
            )
        )

        self.slow_duration_ms = int(
            data.get(
                "slow_duration_ms",
                0,
            )
        )

        self.base_wave_income = int(
            data.get(
                "wave_income",
                0,
            )
        )

        self.base_wave_score = int(
            data.get(
                "wave_score",
                0,
            )
        )

        self.base_factory_interval = int(
            data.get(
                "factory_interval",
                0,
            )
        )

        self.base_tank_damage = float(
            data.get(
                "friendly_tank_damage",
                0,
            )
        )

        self.base_tank_health = int(
            data.get(
                "friendly_tank_health",
                0,
            )
        )

        self.base_tank_speed = float(
            data.get(
                "friendly_tank_speed",
                0,
            )
        )

        self.base_helicopter_count = int(
            data.get(
                "helicopter_count",
                0,
            )
        )

        self.base_helicopter_damage = float(
            data.get(
                "helicopter_damage",
                0,
            )
        )

        self.base_helicopter_range = float(
            data.get(
                "helicopter_range",
                0,
            )
        )

        self.base_helicopter_cooldown = int(
            data.get(
                "helicopter_cooldown",
                0,
            )
        )

        self.targeting_mode = str(
            data.get(
                "default_targeting",
                "first",
            )
        )

        self.last_shot_time = 0
        self.last_factory_spawn_time = 0

        self.current_target: Enemy | None = None

        self.mine_armed = (
            self.unit_kind == "mine"
        )

        self.helicopters: list[
            Helicopter
        ] = []

        self.rebuild_helicopters()

        self.last_visual_shot_time = 0

    @property
    def damage(self) -> float:
        return (
            self.base_damage
            * (
                1
                + (self.level - 1)
                * 0.42
            )
        )

    @property
    def attack_range(self) -> float:
        return (
            self.base_range
            * (
                1
                + (self.level - 1)
                * 0.10
            )
        )

    @property
    def cooldown(self) -> int:
        if self.base_cooldown <= 0:
            return 0

        return max(
            65,
            int(
                self.base_cooldown
                * (
                    0.87
                    ** (self.level - 1)
                )
            ),
        )

    @property
    def armor_piercing(self) -> float:
        return (
            self.base_armor_piercing
            + (self.level - 1)
            * 0.8
        )

    @property
    def splash_radius(self) -> float:
        return (
            self.base_splash_radius
            * (
                1
                + (self.level - 1)
                * 0.12
            )
        )

    @property
    def wave_income(self) -> int:
        return int(
            self.base_wave_income
            * (
                1
                + (self.level - 1)
                * 0.55
            )
        )

    @property
    def wave_score(self) -> int:
        return int(
            self.base_wave_score
            + (self.level - 1) * 2
        )

    @property
    def factory_interval(self) -> int:
        if (
            self.base_factory_interval
            <= 0
        ):
            return 0

        return max(
            3500,
            int(
                self.base_factory_interval
                * (
                    0.84
                    ** (self.level - 1)
                )
            ),
        )

    @property
    def friendly_tank_damage(self) -> float:
        return (
            self.base_tank_damage
            * (
                1
                + (self.level - 1)
                * 0.45
            )
        )

    @property
    def friendly_tank_health(self) -> int:
        return (
            self.base_tank_health
            + (self.level - 1) * 2
        )

    @property
    def friendly_tank_speed(self) -> float:
        return (
            self.base_tank_speed
            * (
                1
                + (self.level - 1)
                * 0.08
            )
        )

    @property
    def helicopter_count(self) -> int:
        return (
            self.base_helicopter_count
            + (self.level - 1)
        )

    @property
    def helicopter_damage(self) -> float:
        return (
            self.base_helicopter_damage
            * (
                1
                + (self.level - 1)
                * 0.38
            )
        )

    @property
    def helicopter_range(self) -> float:
        return (
            self.base_helicopter_range
            * (
                1
                + (self.level - 1)
                * 0.10
            )
        )

    @property
    def helicopter_cooldown(self) -> int:
        return max(
            180,
            int(
                self.base_helicopter_cooldown
                * (
                    0.88
                    ** (self.level - 1)
                )
            ),
        )

    @property
    def upgrade_cost(self) -> int:
        base_cost = int(
            TOWER_TYPES[
                self.tower_type
            ]["cost"]
        )

        return int(
            base_cost
            * (
                0.75
                + self.level
                * 0.45
            )
        )

    @property
    def sell_value(self) -> int:
        return int(
            self.total_spent
            * 0.70
        )

    def can_upgrade(self) -> bool:
        return (
            self.level
            < self.max_level
        )

    def upgrade(self) -> int:
        if not self.can_upgrade():
            return 0

        cost = self.upgrade_cost

        self.level += 1
        self.total_spent += cost

        self.rebuild_helicopters()

        return cost

    def rebuild_helicopters(
        self,
    ) -> None:
        if (
            self.unit_kind
            != "helipad"
        ):
            self.helicopters = []
            return

        required = self.helicopter_count

        if len(self.helicopters) == required:
            return

        self.helicopters = [
            Helicopter(
                self,
                index,
                required,
            )
            for index
            in range(required)
        ]

    def rearm_for_wave(self) -> None:
        if self.unit_kind == "mine":
            self.mine_armed = True

        if self.unit_kind == "factory":
            self.last_factory_spawn_time = 0

    def cycle_targeting_mode(
        self,
    ) -> str:
        current_index = (
            self.TARGETING_MODES.index(
                self.targeting_mode
            )
        )

        next_index = (
            current_index + 1
        ) % len(self.TARGETING_MODES)

        self.targeting_mode = (
            self.TARGETING_MODES[
                next_index
            ]
        )

        return self.targeting_mode

    def find_target(
        self,
        enemies: list[Enemy],
    ) -> Enemy | None:
        valid = [
            enemy
            for enemy in enemies
            if (
                not enemy.dead
                and not enemy.reached_base
                and self.position.distance_to(
                    enemy.position
                )
                <= self.attack_range
            )
        ]

        if not valid:
            self.current_target = None
            return None

        if (
            self.targeting_mode
            == "strongest"
        ):
            target = max(
                valid,
                key=lambda enemy: (
                    enemy.health,
                    enemy.armor,
                ),
            )

        elif (
            self.targeting_mode
            == "closest"
        ):
            target = min(
                valid,
                key=lambda enemy: (
                    self.position.distance_to(
                        enemy.position
                    )
                ),
            )

        elif (
            self.targeting_mode
            == "last"
        ):
            target = min(
                valid,
                key=lambda enemy: (
                    enemy.progress_value()
                ),
            )

        else:
            target = max(
                valid,
                key=lambda enemy: (
                    enemy.progress_value()
                ),
            )

        self.current_target = target
        return target

    def update_attack(
        self,
        enemies: list[Enemy],
        current_time: int,
    ) -> Projectile | None:
        if self.unit_kind != "tower":
            return None

        if (
            current_time
            - self.last_shot_time
            < self.cooldown
        ):
            return None

        target = self.find_target(
            enemies
        )

        if target is None:
            return None

        self.last_shot_time = current_time

        self.last_visual_shot_time = (
            pygame.time.get_ticks()
        )

        return Projectile.from_tower(
            self,
            target,
        )

    def update_helicopters(
        self,
        enemies: list[Enemy],
        current_time: int,
        time_scale: float,
    ) -> list[Projectile]:
        projectiles: list[
            Projectile
        ] = []

        if (
            self.unit_kind
            != "helipad"
        ):
            return projectiles

        for helicopter in self.helicopters:
            projectile = helicopter.update(
                enemies,
                current_time,
                time_scale,
            )

            if projectile is not None:
                projectiles.append(
                    projectile
                )

        return projectiles

    def try_trigger_mine(
        self,
        enemies: list[Enemy],
        current_time: int,
    ) -> bool:
        if (
            self.unit_kind != "mine"
            or not self.mine_armed
        ):
            return False

        triggering_enemy = None

        for enemy in enemies:
            if (
                enemy.dead
                or enemy.reached_base
            ):
                continue

            if (
                self.position.distance_to(
                    enemy.position
                )
                <= 25
            ):
                triggering_enemy = enemy
                break

        if triggering_enemy is None:
            return False

        for enemy in enemies:
            if (
                enemy.dead
                or enemy.reached_base
            ):
                continue

            if (
                self.position.distance_to(
                    enemy.position
                )
                <= self.splash_radius
            ):
                enemy.take_damage(
                    self.damage,
                    self.armor_piercing,
                )

                enemy.apply_slow(
                    self.slow_multiplier,
                    self.slow_duration_ms,
                    current_time,
                )

        self.mine_armed = False
        return True

    def should_factory_spawn(
        self,
        current_time: int,
    ) -> bool:
        if (
            self.unit_kind
            != "factory"
        ):
            return False

        if (
            self.last_factory_spawn_time
            == 0
        ):
            self.last_factory_spawn_time = (
                current_time
            )

            return True

        if (
            current_time
            - self.last_factory_spawn_time
            >= self.factory_interval
        ):
            self.last_factory_spawn_time = (
                current_time
            )

            return True

        return False

    def draw(
        self,
        surface: pygame.Surface,
        selected: bool = False,
    ) -> None:
        center = (
            round(self.position.x),
            round(self.position.y),
        )

        if selected:
            radius = 0

            if self.unit_kind == "tower":
                radius = round(
                    self.attack_range
                )

            elif self.unit_kind == "helipad":
                radius = round(
                    self.helicopter_range
                )

            elif self.unit_kind == "mine":
                radius = round(
                    self.splash_radius
                )

            if radius > 0:
                range_surface = pygame.Surface(
                    surface.get_size(),
                    pygame.SRCALPHA,
                )

                pygame.draw.circle(
                    range_surface,
                    (120, 220, 150, 32),
                    center,
                    radius,
                )

                pygame.draw.circle(
                    range_surface,
                    (235, 255, 235, 170),
                    center,
                    radius,
                    width=2,
                )

                surface.blit(
                    range_surface,
                    (0, 0),
                )

        if self.unit_kind == "mine":
            self.draw_mine(
                surface,
                center,
            )

        elif self.unit_kind == "income":
            self.draw_supply_depot(
                surface,
                center,
            )

        elif self.unit_kind == "score":
            self.draw_intelligence(
                surface,
                center,
            )

        elif self.unit_kind == "factory":
            self.draw_factory(
                surface,
                center,
            )

        elif self.unit_kind == "helipad":
            self.draw_helipad(
                surface,
                center,
            )

        else:
            self.draw_combat_tower(
                surface,
                center,
            )

        self.draw_level_badge(
            surface,
            center,
        )

        for helicopter in self.helicopters:
            helicopter.draw(
                surface
            )

    def get_target_direction(
        self,
    ) -> pygame.Vector2:
        if (
            self.current_target is not None
            and not self.current_target.dead
        ):
            direction = (
                self.current_target.position
                - self.position
            )

            if (
                direction.length_squared()
                > 0
            ):
                return (
                    direction.normalize()
                )

        return pygame.Vector2(1, 0)

    def draw_combat_tower(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        draw_shadow(
            surface,
            center,
            44,
            34,
        )

        base_rect = pygame.Rect(
            0,
            0,
            44,
            44,
        )

        base_rect.center = center

        pygame.draw.rect(
            surface,
            BLACK,
            base_rect.inflate(6, 6),
            border_radius=10,
        )

        pygame.draw.rect(
            surface,
            MILITARY_DARK,
            base_rect,
            border_radius=10,
        )

        inner_base = base_rect.inflate(
            -8,
            -8,
        )

        pygame.draw.rect(
            surface,
            self.colour,
            inner_base,
            border_radius=8,
        )

        direction = (
            self.get_target_direction()
        )

        side = pygame.Vector2(
            -direction.y,
            direction.x,
        )

        if self.tower_type == "rifle":
            self.draw_rifle_team(
                surface,
                center,
                direction,
                side,
            )

        elif (
            self.tower_type
            == "machine_gun"
        ):
            self.draw_machine_gun(
                surface,
                center,
                direction,
                side,
            )

        elif (
            self.tower_type
            == "sniper"
        ):
            self.draw_sniper_team(
                surface,
                center,
                direction,
                side,
            )

        elif (
            self.tower_type
            == "mortar"
        ):
            self.draw_mortar(
                surface,
                center,
                direction,
            )

    def draw_rifle_team(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        direction: pygame.Vector2,
        side: pygame.Vector2,
    ) -> None:
        for offset in (-7, 7):
            soldier_center = (
                pygame.Vector2(center)
                + side * offset
                - direction * 2
            )

            pygame.draw.circle(
                surface,
                BLACK,
                (
                    round(soldier_center.x),
                    round(soldier_center.y),
                ),
                7,
            )

            pygame.draw.circle(
                surface,
                MILITARY_LIGHT,
                (
                    round(soldier_center.x),
                    round(soldier_center.y),
                ),
                5,
            )

            gun_end = (
                soldier_center
                + direction * 17
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    round(soldier_center.x),
                    round(soldier_center.y),
                ),
                (
                    round(gun_end.x),
                    round(gun_end.y),
                ),
                width=3,
            )

        if (
            pygame.time.get_ticks()
            - self.last_visual_shot_time
            < 80
        ):
            flash_position = (
                pygame.Vector2(center)
                + direction * 18
                + side * 7
            )

            draw_muzzle_flash(
                surface,
                (
                    round(flash_position.x),
                    round(flash_position.y),
                ),
                direction,
                size=7,
            )

    def draw_machine_gun(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        direction: pygame.Vector2,
        side: pygame.Vector2,
    ) -> None:
        pygame.draw.circle(
            surface,
            BLACK,
            center,
            15,
        )

        pygame.draw.circle(
            surface,
            METAL_DARK,
            center,
            12,
        )

        shield_center = (
            pygame.Vector2(center)
            + direction * 5
        )

        shield_points = [
            shield_center + side * 11,
            shield_center - side * 11,
            shield_center
            + direction * 8
            - side * 8,
            shield_center
            + direction * 8
            + side * 8,
        ]

        pygame.draw.polygon(
            surface,
            MILITARY_GREEN,
            [
                (
                    round(point.x),
                    round(point.y),
                )
                for point in shield_points
            ],
        )

        for offset in (-3, 3):
            barrel_start = (
                pygame.Vector2(center)
                + side * offset
            )

            barrel_end = (
                barrel_start
                + direction * 28
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    round(barrel_start.x),
                    round(barrel_start.y),
                ),
                (
                    round(barrel_end.x),
                    round(barrel_end.y),
                ),
                width=4,
            )

            pygame.draw.line(
                surface,
                METAL_LIGHT,
                (
                    round(
                        barrel_start.x
                        + direction.x * 4
                    ),
                    round(
                        barrel_start.y
                        + direction.y * 4
                    ),
                ),
                (
                    round(barrel_end.x),
                    round(barrel_end.y),
                ),
                width=2,
            )

        ammo_box = (
            pygame.Vector2(center)
            - side * 10
        )

        ammo_rect = pygame.Rect(
            0,
            0,
            9,
            12,
        )

        ammo_rect.center = (
            round(ammo_box.x),
            round(ammo_box.y),
        )

        pygame.draw.rect(
            surface,
            YELLOW,
            ammo_rect,
            border_radius=2,
        )

        if (
            pygame.time.get_ticks()
            - self.last_visual_shot_time
            < 70
        ):
            flash_position = (
                pygame.Vector2(center)
                + direction * 29
            )

            draw_muzzle_flash(
                surface,
                (
                    round(flash_position.x),
                    round(flash_position.y),
                ),
                direction,
                size=9,
            )

    def draw_sniper_team(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        direction: pygame.Vector2,
        side: pygame.Vector2,
    ) -> None:
        prone_center = (
            pygame.Vector2(center)
            - direction * 4
        )

        body_start = (
            prone_center
            - direction * 9
        )

        body_end = (
            prone_center
            + direction * 5
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(body_start.x),
                round(body_start.y),
            ),
            (
                round(body_end.x),
                round(body_end.y),
            ),
            width=9,
        )

        pygame.draw.line(
            surface,
            MILITARY_GREEN,
            (
                round(body_start.x),
                round(body_start.y),
            ),
            (
                round(body_end.x),
                round(body_end.y),
            ),
            width=6,
        )

        head_center = (
            body_start
            - direction * 4
        )

        pygame.draw.circle(
            surface,
            BLACK,
            (
                round(head_center.x),
                round(head_center.y),
            ),
            6,
        )

        pygame.draw.circle(
            surface,
            MILITARY_LIGHT,
            (
                round(head_center.x),
                round(head_center.y),
            ),
            4,
        )

        rifle_start = (
            prone_center
            - side * 3
        )

        rifle_end = (
            rifle_start
            + direction * 34
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(rifle_start.x),
                round(rifle_start.y),
            ),
            (
                round(rifle_end.x),
                round(rifle_end.y),
            ),
            width=4,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                round(
                    rifle_start.x
                    + direction.x * 6
                ),
                round(
                    rifle_start.y
                    + direction.y * 6
                ),
            ),
            (
                round(rifle_end.x),
                round(rifle_end.y),
            ),
            width=2,
        )

        scope_center = (
            rifle_start
            + direction * 10
        )

        pygame.draw.circle(
            surface,
            WINDOW_BLUE,
            (
                round(scope_center.x),
                round(scope_center.y),
            ),
            3,
        )

        if (
            pygame.time.get_ticks()
            - self.last_visual_shot_time
            < 90
        ):
            draw_muzzle_flash(
                surface,
                (
                    round(rifle_end.x),
                    round(rifle_end.y),
                ),
                direction,
                size=10,
            )

    def draw_mortar(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        direction: pygame.Vector2,
    ) -> None:
        pygame.draw.circle(
            surface,
            BLACK,
            center,
            17,
        )

        pygame.draw.circle(
            surface,
            METAL_DARK,
            center,
            14,
        )

        tube_start = (
            pygame.Vector2(center)
            - direction * 3
        )

        tube_end = (
            pygame.Vector2(center)
            + direction * 20
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(tube_start.x),
                round(tube_start.y),
            ),
            (
                round(tube_end.x),
                round(tube_end.y),
            ),
            width=10,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                round(
                    tube_start.x
                    + direction.x * 2
                ),
                round(
                    tube_start.y
                    + direction.y * 2
                ),
            ),
            (
                round(tube_end.x),
                round(tube_end.y),
            ),
            width=5,
        )

        pygame.draw.circle(
            surface,
            BLACK,
            (
                round(tube_end.x),
                round(tube_end.y),
            ),
            6,
        )

        for leg_angle in (
            -2.2,
            -0.9,
            1.6,
        ):
            leg_direction = pygame.Vector2(
                math.cos(leg_angle),
                math.sin(leg_angle),
            )

            leg_end = (
                pygame.Vector2(center)
                + leg_direction * 18
            )

            pygame.draw.line(
                surface,
                BLACK,
                center,
                (
                    round(leg_end.x),
                    round(leg_end.y),
                ),
                width=3,
            )

    def draw_mine(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        draw_shadow(
            surface,
            center,
            34,
            14,
        )

        colour = (
            self.colour
            if self.mine_armed
            else DARK_GREY
        )

        pygame.draw.circle(
            surface,
            BLACK,
            center,
            17,
        )

        pygame.draw.circle(
            surface,
            METAL_DARK,
            center,
            14,
        )

        pygame.draw.circle(
            surface,
            colour,
            center,
            11,
        )

        for angle_degrees in range(
            0,
            360,
            45,
        ):
            radians = math.radians(
                angle_degrees
            )

            direction = pygame.Vector2(
                math.cos(radians),
                math.sin(radians),
            )

            start = (
                pygame.Vector2(center)
                + direction * 9
            )

            end = (
                pygame.Vector2(center)
                + direction * 17
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    round(start.x),
                    round(start.y),
                ),
                (
                    round(end.x),
                    round(end.y),
                ),
                width=4,
            )

            pygame.draw.circle(
                surface,
                METAL_MID,
                (
                    round(end.x),
                    round(end.y),
                ),
                2,
            )

        pygame.draw.circle(
            surface,
            (
                YELLOW
                if self.mine_armed
                else BLACK
            ),
            center,
            4,
        )

        if self.mine_armed:
            pulse = (
                5
                + int(
                    math.sin(
                        pygame.time.get_ticks()
                        / 130
                    )
                    * 2
                )
            )

            pygame.draw.circle(
                surface,
                RED,
                center,
                pulse,
                width=1,
            )

    def draw_supply_depot(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        draw_shadow(
            surface,
            center,
            48,
            38,
        )

        building = pygame.Rect(
            0,
            0,
            46,
            38,
        )

        building.center = center

        pygame.draw.rect(
            surface,
            BLACK,
            building.inflate(6, 6),
            border_radius=5,
        )

        pygame.draw.rect(
            surface,
            SUPPLY_BROWN,
            building,
            border_radius=5,
        )

        roof_points = [
            (
                building.left - 3,
                building.top + 7,
            ),
            (
                building.centerx,
                building.top - 10,
            ),
            (
                building.right + 3,
                building.top + 7,
            ),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            roof_points,
        )

        pygame.draw.polygon(
            surface,
            SUPPLY_LIGHT,
            [
                (
                    building.left + 1,
                    building.top + 6,
                ),
                (
                    building.centerx,
                    building.top - 6,
                ),
                (
                    building.right - 1,
                    building.top + 6,
                ),
            ],
        )

        door = pygame.Rect(
            building.centerx - 7,
            building.centery + 1,
            14,
            building.height // 2,
        )

        pygame.draw.rect(
            surface,
            DARK_GREY,
            door,
            border_radius=2,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                door.centerx,
                door.top,
            ),
            (
                door.centerx,
                door.bottom,
            ),
            width=1,
        )

        crate_positions = [
            (
                building.left + 8,
                building.top + 12,
            ),
            (
                building.right - 9,
                building.top + 12,
            ),
        ]

        for crate_center in crate_positions:
            crate = pygame.Rect(
                0,
                0,
                10,
                9,
            )

            crate.center = crate_center

            pygame.draw.rect(
                surface,
                YELLOW,
                crate,
                border_radius=2,
            )

            pygame.draw.line(
                surface,
                BLACK,
                crate.topleft,
                crate.bottomright,
                width=1,
            )

            pygame.draw.line(
                surface,
                BLACK,
                crate.topright,
                crate.bottomleft,
                width=1,
            )

    def draw_intelligence(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        draw_shadow(
            surface,
            center,
            46,
            38,
        )

        building = pygame.Rect(
            0,
            0,
            43,
            42,
        )

        building.center = center

        pygame.draw.rect(
            surface,
            BLACK,
            building.inflate(6, 6),
            border_radius=8,
        )

        pygame.draw.rect(
            surface,
            INTEL_PURPLE,
            building,
            border_radius=8,
        )

        inner = building.inflate(
            -8,
            -8,
        )

        pygame.draw.rect(
            surface,
            INTEL_LIGHT,
            inner,
            border_radius=5,
        )

        screen = pygame.Rect(
            center[0] - 13,
            center[1] + 1,
            26,
            13,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            screen.inflate(3, 3),
            border_radius=3,
        )

        pygame.draw.rect(
            surface,
            WINDOW_BLUE,
            screen,
            border_radius=2,
        )

        pygame.draw.line(
            surface,
            CYAN,
            (
                screen.left + 4,
                screen.centery,
            ),
            (
                screen.right - 4,
                screen.centery,
            ),
            width=2,
        )

        antenna_base = pygame.Vector2(
            center[0],
            center[1] - 11,
        )

        antenna_top = (
            antenna_base
            + pygame.Vector2(0, -18)
        )

        pygame.draw.line(
            surface,
            BLACK,
            (
                round(antenna_base.x),
                round(antenna_base.y),
            ),
            (
                round(antenna_top.x),
                round(antenna_top.y),
            ),
            width=3,
        )

        pygame.draw.circle(
            surface,
            CYAN,
            (
                round(antenna_top.x),
                round(antenna_top.y),
            ),
            5,
        )

        pulse = (
            16
            + int(
                math.sin(
                    pygame.time.get_ticks()
                    / 180
                )
                * 3
            )
        )

        pygame.draw.arc(
            surface,
            WHITE,
            (
                center[0] - pulse,
                center[1] - 42,
                pulse * 2,
                26,
            ),
            0.35,
            2.8,
            width=2,
        )

    def draw_factory(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        draw_shadow(
            surface,
            center,
            52,
            42,
        )

        building = pygame.Rect(
            0,
            0,
            48,
            42,
        )

        building.center = center

        pygame.draw.rect(
            surface,
            BLACK,
            building.inflate(6, 6),
            border_radius=5,
        )

        pygame.draw.rect(
            surface,
            FACTORY_GREY,
            building,
            border_radius=5,
        )

        upper = pygame.Rect(
            building.left + 4,
            building.top + 4,
            building.width - 8,
            15,
        )

        pygame.draw.rect(
            surface,
            FACTORY_LIGHT,
            upper,
            border_radius=3,
        )

        garage = pygame.Rect(
            building.left + 5,
            building.centery - 1,
            building.width - 10,
            building.height // 2,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            garage,
            border_radius=3,
        )

        pygame.draw.rect(
            surface,
            DARK_GREY,
            garage.inflate(-4, -4),
            border_radius=2,
        )

        for stripe_x in range(
            garage.left + 5,
            garage.right - 4,
            7,
        ):
            pygame.draw.line(
                surface,
                METAL_MID,
                (
                    stripe_x,
                    garage.top + 3,
                ),
                (
                    stripe_x,
                    garage.bottom - 3,
                ),
                width=1,
            )

        chimney = pygame.Rect(
            building.right - 14,
            building.top - 19,
            9,
            23,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            chimney.inflate(3, 3),
            border_radius=2,
        )

        pygame.draw.rect(
            surface,
            METAL_DARK,
            chimney,
            border_radius=2,
        )

        smoke_y = (
            chimney.top - 5
            + int(
                math.sin(
                    pygame.time.get_ticks()
                    / 240
                )
                * 2
            )
        )

        smoke_surface = pygame.Surface(
            (18, 18),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            smoke_surface,
            (150, 150, 150, 90),
            (8, 10),
            6,
        )

        pygame.draw.circle(
            smoke_surface,
            (180, 180, 180, 65),
            (12, 6),
            5,
        )

        surface.blit(
            smoke_surface,
            (
                chimney.centerx - 8,
                smoke_y - 12,
            ),
        )

        warning_light = (
            building.left + 10,
            building.top + 10,
        )

        pygame.draw.circle(
            surface,
            YELLOW,
            warning_light,
            4,
        )

        if (
            pygame.time.get_ticks()
            // 400
        ) % 2 == 0:
            pygame.draw.circle(
                surface,
                RED,
                warning_light,
                6,
                width=1,
            )

    def draw_helipad(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        draw_shadow(
            surface,
            center,
            50,
            32,
        )

        pygame.draw.circle(
            surface,
            BLACK,
            center,
            27,
        )

        pygame.draw.circle(
            surface,
            HELIPAD_GREY,
            center,
            24,
        )

        pygame.draw.circle(
            surface,
            HELIPAD_EDGE,
            center,
            20,
            width=2,
        )

        for angle_degrees in range(
            0,
            360,
            45,
        ):
            radians = math.radians(
                angle_degrees
            )

            start = (
                center[0]
                + math.cos(radians)
                * 20,
                center[1]
                + math.sin(radians)
                * 20,
            )

            end = (
                center[0]
                + math.cos(radians)
                * 25,
                center[1]
                + math.sin(radians)
                * 25,
            )

            pygame.draw.line(
                surface,
                WHITE,
                (
                    round(start[0]),
                    round(start[1]),
                ),
                (
                    round(end[0]),
                    round(end[1]),
                ),
                width=2,
            )

        font = pygame.font.Font(
            None,
            32,
        )

        image = font.render(
            "H",
            True,
            WHITE,
        )

        surface.blit(
            image,
            image.get_rect(
                center=center
            ),
        )

        beacon_position = (
            center[0] + 19,
            center[1] - 19,
        )

        pygame.draw.circle(
            surface,
            BLACK,
            beacon_position,
            5,
        )

        beacon_colour = (
            RED
            if (
                pygame.time.get_ticks()
                // 350
            ) % 2 == 0
            else YELLOW
        )

        pygame.draw.circle(
            surface,
            beacon_colour,
            beacon_position,
            3,
        )

    def draw_level_badge(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        badge_center = (
            center[0] + 19,
            center[1] - 19,
        )

        pygame.draw.circle(
            surface,
            BLACK,
            badge_center,
            11,
        )

        pygame.draw.circle(
            surface,
            self.colour,
            badge_center,
            8,
        )

        font = pygame.font.Font(
            None,
            18,
        )

        image = font.render(
            str(self.level),
            True,
            WHITE,
        )

        surface.blit(
            image,
            image.get_rect(
                center=badge_center
            ),
        )