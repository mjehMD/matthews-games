from __future__ import annotations

import asyncio
import json
import math
import random
from pathlib import Path

import pygame
from online_leaderboard import (
    load_online_leaderboard,
    submit_online_score,
)


# ============================================================
# GENERAL SETTINGS
# ============================================================

GAME_WIDTH = 1100
GAME_HEIGHT = 750
FPS = 60

WINDOW_TITLE = "Matthew's Space Shooter"

LEADERBOARD_FILE = Path(__file__).with_name("leaderboard.json")
MAX_LEADERBOARD_ENTRIES = 10

PLAYER_STARTING_LIVES = 3
PLAYER_SPEED = 8
PLAYER_WIDTH = 66
PLAYER_HEIGHT = 62

PLAYER_INVINCIBILITY_MS = 2400

BULLET_SPEED = 13
BASE_SHOT_COOLDOWN_MS = 240

ENEMY_BASE_SPAWN_DELAY_MS = 1250
BOSS_WAVE_INTERVAL = 5

POWERUP_DROP_CHANCE = 0.23
POWERUP_DURATION_MS = 9000

MAX_EXPLOSION_PARTICLES = 400


# ============================================================
# COLOURS
# ============================================================

BLACK = (5, 8, 18)
SPACE_BLACK = (3, 6, 16)

DEEP_BLUE = (9, 18, 42)
DARK_BLUE = (18, 38, 80)
MID_BLUE = (29, 65, 130)

BLUE = (45, 115, 235)
LIGHT_BLUE = (90, 195, 255)
CYAN = (90, 245, 255)

WHITE = (245, 248, 255)
LIGHT_GREY = (195, 205, 225)
GREY = (125, 140, 170)
DARK_GREY = (48, 58, 82)

METAL_DARK = (34, 42, 65)
METAL_MID = (72, 89, 125)
METAL_LIGHT = (145, 165, 205)

RED = (235, 65, 75)
DARK_RED = (135, 35, 50)

ORANGE = (255, 145, 60)
YELLOW = (255, 225, 75)

GREEN = (75, 220, 125)
DARK_GREEN = (35, 105, 70)

PURPLE = (165, 90, 235)
DARK_PURPLE = (84, 44, 135)

PINK = (255, 95, 195)

WINDOW_BLUE = (85, 190, 225)
WINDOW_HIGHLIGHT = (190, 245, 255)

ENGINE_BLUE = (80, 170, 255)
ENGINE_WHITE = (225, 250, 255)

ENEMY_METAL = (82, 52, 70)
ENEMY_ARMOR = (135, 55, 75)

BOSS_ARMOR = (88, 38, 74)
BOSS_HIGHLIGHT = (185, 60, 130)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def draw_text(
    surface,
    text,
    font,
    colour,
    x,
    y,
    center=False,
    right=False,
):
    image = font.render(str(text), True, colour)
    rect = image.get_rect()

    if center:
        rect.center = (x, y)
    elif right:
        rect.topright = (x, y)
    else:
        rect.topleft = (x, y)

    surface.blit(image, rect)
    return rect


def rotate_points(
    points,
    center,
    angle,
):
    cosine = math.cos(angle)
    sine = math.sin(angle)

    rotated = []

    for local_x, local_y in points:
        rotated_x = (
            local_x * cosine
            - local_y * sine
        )

        rotated_y = (
            local_x * sine
            + local_y * cosine
        )

        rotated.append(
            (
                round(center[0] + rotated_x),
                round(center[1] + rotated_y),
            )
        )

    return rotated


def draw_rotated_polygon(
    surface,
    points,
    center,
    angle,
    colour,
    outline=None,
    outline_width=0,
):
    rotated = rotate_points(
        points,
        center,
        angle,
    )

    if outline is not None and outline_width > 0:
        pygame.draw.polygon(
            surface,
            outline,
            rotated,
        )

        inner_points = []

        for point_x, point_y in points:
            inner_points.append(
                (
                    point_x * 0.88,
                    point_y * 0.88,
                )
            )

        pygame.draw.polygon(
            surface,
            colour,
            rotate_points(
                inner_points,
                center,
                angle,
            ),
        )

    else:
        pygame.draw.polygon(
            surface,
            colour,
            rotated,
        )


def draw_glow_circle(
    surface,
    position,
    colour,
    radius,
    glow_radius=None,
):
    if glow_radius is None:
        glow_radius = radius * 3

    size = glow_radius * 2 + 4

    glow_surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )

    center = (
        size // 2,
        size // 2,
    )

    for layer in range(4, 0, -1):
        layer_radius = int(
            radius
            + (
                glow_radius - radius
            )
            * layer / 4
        )

        alpha = int(18 + 12 * (5 - layer))

        pygame.draw.circle(
            glow_surface,
            (
                colour[0],
                colour[1],
                colour[2],
                alpha,
            ),
            center,
            layer_radius,
        )

    pygame.draw.circle(
        glow_surface,
        colour,
        center,
        radius,
    )

    surface.blit(
        glow_surface,
        (
            position[0] - center[0],
            position[1] - center[1],
        ),
    )


def draw_ship_shadow(
    surface,
    rect,
    width_scale=0.82,
):
    shadow_surface = pygame.Surface(
        (
            rect.width + 24,
            rect.height // 2 + 18,
        ),
        pygame.SRCALPHA,
    )

    shadow_rect = shadow_surface.get_rect().inflate(
        -8,
        -8,
    )

    shadow_rect.width = int(
        shadow_rect.width * width_scale
    )

    shadow_rect.centerx = (
        shadow_surface.get_width() // 2
    )

    pygame.draw.ellipse(
        shadow_surface,
        (0, 0, 0, 75),
        shadow_rect,
    )

    surface.blit(
        shadow_surface,
        (
            rect.centerx
            - shadow_surface.get_width() // 2,
            rect.bottom - 4,
        ),
    )


def draw_panel(
    surface,
    rect,
    fill=DARK_BLUE,
    border=LIGHT_BLUE,
    border_width=2,
):
    pygame.draw.rect(
        surface,
        BLACK,
        rect.move(0, 5),
        border_radius=14,
    )

    pygame.draw.rect(
        surface,
        fill,
        rect,
        border_radius=14,
    )

    pygame.draw.rect(
        surface,
        border,
        rect,
        width=border_width,
        border_radius=14,
    )


# ============================================================
# LEADERBOARD
# ============================================================

def load_leaderboard():
    try:
        if not LEADERBOARD_FILE.exists():
            return []

        with LEADERBOARD_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        cleaned = []

        for entry in data:
            if not isinstance(entry, dict):
                continue

            name = str(
                entry.get("name", "Player")
            ).strip()[:15]

            score = entry.get("score", 0)
            wave = entry.get("wave", 1)

            if (
                not isinstance(score, int)
                or score < 0
            ):
                continue

            if (
                not isinstance(wave, int)
                or wave < 1
            ):
                wave = 1

            cleaned.append(
                {
                    "name": name or "Player",
                    "score": score,
                    "wave": wave,
                }
            )

        cleaned.sort(
            key=lambda item: (
                item["score"],
                item["wave"],
            ),
            reverse=True,
        )

        return cleaned[
            :MAX_LEADERBOARD_ENTRIES
        ]

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []


def save_leaderboard(leaderboard):
    try:
        with LEADERBOARD_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                leaderboard,
                file,
                indent=4,
            )

    except OSError:
        pass


def add_leaderboard_score(
    leaderboard,
    name,
    score,
    wave,
):
    cleaned_name = str(name).strip()[:16] or "Player"
    cleaned_score = max(0, int(score))
    cleaned_wave = max(1, int(wave))

    matching_entry = None

    for entry in leaderboard:
        if str(entry.get("name", "")).casefold() == cleaned_name.casefold():
            matching_entry = entry
            break

    if matching_entry is None:
        leaderboard.append(
            {
                "name": cleaned_name,
                "score": cleaned_score,
                "wave": cleaned_wave,
            }
        )
    else:
        old_result = (
            int(matching_entry.get("score", 0)),
            int(matching_entry.get("wave", 1)),
        )
        new_result = (cleaned_score, cleaned_wave)

        if new_result > old_result:
            matching_entry["name"] = cleaned_name
            matching_entry["score"] = cleaned_score
            matching_entry["wave"] = cleaned_wave

    leaderboard.sort(
        key=lambda item: (
            int(item["score"]),
            int(item["wave"]),
        ),
        reverse=True,
    )

    del leaderboard[MAX_LEADERBOARD_ENTRIES:]
    save_leaderboard(leaderboard)


# ============================================================
# BUTTON
# ============================================================

class Button:
    def __init__(
        self,
        rect,
        text,
        font,
        hotkey_text="",
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hotkey_text = hotkey_text
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(
            mouse_pos
        )

    def draw(self, surface):
        fill_colour = (
            MID_BLUE
            if self.hovered
            else DARK_BLUE
        )

        border_colour = (
            CYAN
            if self.hovered
            else LIGHT_BLUE
        )

        shadow_rect = self.rect.move(0, 6)

        pygame.draw.rect(
            surface,
            BLACK,
            shadow_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            surface,
            fill_colour,
            self.rect,
            border_radius=12,
        )

        highlight_rect = pygame.Rect(
            self.rect.x + 5,
            self.rect.y + 5,
            self.rect.width - 10,
            max(
                8,
                self.rect.height // 3,
            ),
        )

        pygame.draw.rect(
            surface,
            (
                min(255, fill_colour[0] + 18),
                min(255, fill_colour[1] + 18),
                min(255, fill_colour[2] + 18),
            ),
            highlight_rect,
            border_radius=8,
        )

        pygame.draw.rect(
            surface,
            border_colour,
            self.rect,
            width=3,
            border_radius=12,
        )

        draw_text(
            surface,
            self.text,
            self.font,
            WHITE,
            self.rect.centerx,
            self.rect.centery - 4,
            center=True,
        )

        if self.hotkey_text:
            draw_text(
                surface,
                self.hotkey_text,
                pygame.font.Font(None, 22),
                LIGHT_GREY,
                self.rect.right - 16,
                self.rect.bottom - 24,
                right=True,
            )

    def clicked(self, event):
        return (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(
                event.pos
            )
        )


# ============================================================
# BACKGROUND
# ============================================================

class Star:
    def __init__(self):
        self.reset(
            random.randint(
                0,
                GAME_HEIGHT,
            )
        )

    def reset(self, y_position=-10):
        self.x = random.randint(
            0,
            GAME_WIDTH,
        )

        self.y = float(y_position)

        self.depth = random.choice(
            (
                1,
                1,
                2,
                2,
                3,
            )
        )

        self.speed = {
            1: random.uniform(0.25, 0.7),
            2: random.uniform(0.8, 1.6),
            3: random.uniform(1.8, 3.0),
        }[self.depth]

        self.radius = {
            1: 1,
            2: 1,
            3: random.choice((1, 2)),
        }[self.depth]

        if self.depth == 1:
            self.colour = random.choice(
                (
                    (80, 105, 165),
                    (95, 115, 180),
                    (110, 125, 195),
                )
            )

        elif self.depth == 2:
            self.colour = random.choice(
                (
                    (145, 170, 220),
                    (165, 195, 235),
                    (120, 195, 225),
                )
            )

        else:
            self.colour = random.choice(
                (
                    (215, 230, 255),
                    (180, 235, 255),
                    (245, 245, 255),
                )
            )

        self.twinkle_offset = random.uniform(
            0,
            math.tau,
        )

    def update(self):
        self.y += self.speed

        if self.y > GAME_HEIGHT + 5:
            self.reset(-5)

    def draw(self, surface):
        current_time = pygame.time.get_ticks()

        brightness = (
            0.78
            + math.sin(
                current_time / 450
                + self.twinkle_offset
            )
            * 0.22
        )

        colour = (
            int(self.colour[0] * brightness),
            int(self.colour[1] * brightness),
            int(self.colour[2] * brightness),
        )

        position = (
            int(self.x),
            int(self.y),
        )

        pygame.draw.circle(
            surface,
            colour,
            position,
            self.radius,
        )

        if self.depth == 3 and self.radius == 2:
            pygame.draw.line(
                surface,
                colour,
                (
                    position[0] - 3,
                    position[1],
                ),
                (
                    position[0] + 3,
                    position[1],
                ),
            )

            pygame.draw.line(
                surface,
                colour,
                (
                    position[0],
                    position[1] - 3,
                ),
                (
                    position[0],
                    position[1] + 3,
                ),
            )


class NebulaCloud:
    def __init__(self):
        self.x = random.randint(
            -100,
            GAME_WIDTH + 100,
        )

        self.y = random.randint(
            -200,
            GAME_HEIGHT,
        )

        self.radius = random.randint(
            110,
            230,
        )

        self.speed = random.uniform(
            0.05,
            0.16,
        )

        self.colour = random.choice(
            (
                (45, 65, 145),
                (80, 40, 125),
                (35, 95, 135),
                (95, 35, 100),
            )
        )

        self.alpha = random.randint(
            10,
            25,
        )

    def update(self):
        self.y += self.speed

        if self.y - self.radius > GAME_HEIGHT:
            self.y = -self.radius
            self.x = random.randint(
                -100,
                GAME_WIDTH + 100,
            )

    def draw(self, surface):
        size = self.radius * 2

        cloud = pygame.Surface(
            (size, size),
            pygame.SRCALPHA,
        )

        center = (
            self.radius,
            self.radius,
        )

        for layer in range(5, 0, -1):
            radius = int(
                self.radius * layer / 5
            )

            alpha = int(
                self.alpha
                * (
                    1.0
                    - layer / 7
                )
            )

            pygame.draw.circle(
                cloud,
                (
                    self.colour[0],
                    self.colour[1],
                    self.colour[2],
                    alpha,
                ),
                center,
                radius,
            )

        surface.blit(
            cloud,
            (
                int(self.x - self.radius),
                int(self.y - self.radius),
            ),
        )


class DistantPlanet:
    def __init__(self):
        self.radius = random.randint(
            50,
            90,
        )

        self.x = random.choice(
            (
                random.randint(
                    -20,
                    120,
                ),
                random.randint(
                    GAME_WIDTH - 120,
                    GAME_WIDTH + 20,
                ),
            )
        )

        self.y = random.randint(
            80,
            GAME_HEIGHT // 2,
        )

        self.base_colour = random.choice(
            (
                (50, 80, 140),
                (90, 55, 130),
                (45, 105, 120),
            )
        )

    def draw(self, surface):
        planet_surface = pygame.Surface(
            (
                self.radius * 2 + 20,
                self.radius * 2 + 20,
            ),
            pygame.SRCALPHA,
        )

        center = (
            planet_surface.get_width() // 2,
            planet_surface.get_height() // 2,
        )

        pygame.draw.circle(
            planet_surface,
            (
                self.base_colour[0],
                self.base_colour[1],
                self.base_colour[2],
                90,
            ),
            center,
            self.radius,
        )

        pygame.draw.circle(
            planet_surface,
            (
                min(
                    255,
                    self.base_colour[0] + 50,
                ),
                min(
                    255,
                    self.base_colour[1] + 50,
                ),
                min(
                    255,
                    self.base_colour[2] + 50,
                ),
                80,
            ),
            (
                center[0] - self.radius // 4,
                center[1] - self.radius // 4,
            ),
            self.radius // 2,
        )

        pygame.draw.circle(
            planet_surface,
            (0, 0, 0, 65),
            (
                center[0] + self.radius // 3,
                center[1] + self.radius // 4,
            ),
            int(self.radius * 0.75),
        )

        surface.blit(
            planet_surface,
            (
                self.x - center[0],
                self.y - center[1],
            ),
        )


# ============================================================
# PARTICLES
# ============================================================

class Particle:
    def __init__(
        self,
        x,
        y,
        colour,
        large=False,
        particle_type="spark",
    ):
        angle = random.uniform(
            0,
            math.tau,
        )

        self.particle_type = particle_type

        if particle_type == "smoke":
            speed = random.uniform(
                0.3,
                1.5,
            )

            self.life = random.randint(
                40,
                80,
            )

            self.size = random.randint(
                5,
                11,
            )

        elif large:
            speed = random.uniform(
                2.0,
                7.5,
            )

            self.life = random.randint(
                28,
                55,
            )

            self.size = random.randint(
                3,
                7,
            )

        else:
            speed = random.uniform(
                1.2,
                4.8,
            )

            self.life = random.randint(
                18,
                40,
            )

            self.size = random.randint(
                2,
                5,
            )

        self.max_life = self.life

        self.x = float(x)
        self.y = float(y)

        self.dx = (
            math.cos(angle)
            * speed
        )

        self.dy = (
            math.sin(angle)
            * speed
        )

        if particle_type == "smoke":
            self.dy -= random.uniform(
                0.5,
                1.3,
            )

        self.colour = colour

    def update(self):
        self.x += self.dx
        self.y += self.dy

        if self.particle_type == "smoke":
            self.dx *= 0.975
            self.dy *= 0.985
            self.size += 0.06

        else:
            self.dx *= 0.96
            self.dy *= 0.96
            self.dy += 0.04

        self.life -= 1

    def draw(
        self,
        surface,
        offset_x=0,
        offset_y=0,
    ):
        if self.life <= 0:
            return

        fade = (
            self.life
            / self.max_life
        )

        position = (
            int(self.x + offset_x),
            int(self.y + offset_y),
        )

        if self.particle_type == "smoke":
            alpha = int(
                110 * fade
            )

            radius = max(
                2,
                int(self.size * (1.1 - fade * 0.2)),
            )

            smoke_surface = pygame.Surface(
                (
                    radius * 2 + 4,
                    radius * 2 + 4,
                ),
                pygame.SRCALPHA,
            )

            pygame.draw.circle(
                smoke_surface,
                (
                    self.colour[0],
                    self.colour[1],
                    self.colour[2],
                    alpha,
                ),
                (
                    radius + 2,
                    radius + 2,
                ),
                radius,
            )

            surface.blit(
                smoke_surface,
                (
                    position[0] - radius - 2,
                    position[1] - radius - 2,
                ),
            )

        else:
            colour = (
                int(
                    self.colour[0]
                    * fade
                ),
                int(
                    self.colour[1]
                    * fade
                ),
                int(
                    self.colour[2]
                    * fade
                ),
            )

            radius = max(
                1,
                int(self.size * fade),
            )

            pygame.draw.circle(
                surface,
                colour,
                position,
                radius,
            )

            if self.particle_type == "spark":
                trail_end = (
                    int(
                        position[0]
                        - self.dx * 2
                    ),
                    int(
                        position[1]
                        - self.dy * 2
                    ),
                )

                pygame.draw.line(
                    surface,
                    colour,
                    position,
                    trail_end,
                    width=max(
                        1,
                        radius // 2,
                    ),
                )


class FloatingText:
    def __init__(
        self,
        text,
        x,
        y,
        colour,
    ):
        self.text = text
        self.x = x
        self.y = y
        self.colour = colour
        self.life = 55

    def update(self):
        self.y -= 0.8
        self.life -= 1

    def draw(
        self,
        surface,
        font,
        offset_x=0,
        offset_y=0,
    ):
        draw_text(
            surface,
            self.text,
            font,
            self.colour,
            self.x + offset_x,
            self.y + offset_y,
            center=True,
        )

# ============================================================
# BULLETS
# ============================================================

class Bullet:
    def __init__(
        self,
        x,
        y,
        dx=0,
        dy=-BULLET_SPEED,
        damage=1,
        friendly=True,
    ):
        self.x = float(x)
        self.y = float(y)

        self.previous_x = float(x)
        self.previous_y = float(y)

        self.dx = dx
        self.dy = dy

        self.damage = damage
        self.friendly = friendly

        if friendly:
            self.rect = pygame.Rect(
                0,
                0,
                8,
                22,
            )
        else:
            self.rect = pygame.Rect(
                0,
                0,
                12,
                20,
            )

        self.pulse_offset = random.uniform(
            0,
            math.tau,
        )

        self.update_rect()

    def update_rect(self):
        self.rect.center = (
            round(self.x),
            round(self.y),
        )

    def update(self):
        self.previous_x = self.x
        self.previous_y = self.y

        self.x += self.dx
        self.y += self.dy

        self.update_rect()

    def outside_screen(self):
        return (
            self.rect.bottom < -30
            or self.rect.top > GAME_HEIGHT + 30
            or self.rect.right < -30
            or self.rect.left > GAME_WIDTH + 30
        )

    def draw(
        self,
        surface,
        offset_x=0,
        offset_y=0,
    ):
        center = (
            round(self.x + offset_x),
            round(self.y + offset_y),
        )

        previous = (
            round(self.previous_x + offset_x),
            round(self.previous_y + offset_y),
        )

        if self.friendly:
            trail_start = (
                center[0],
                center[1] + 18,
            )

            pygame.draw.line(
                surface,
                BLUE,
                trail_start,
                center,
                width=7,
            )

            pygame.draw.line(
                surface,
                LIGHT_BLUE,
                (
                    center[0],
                    center[1] + 15,
                ),
                center,
                width=4,
            )

            pygame.draw.line(
                surface,
                WHITE,
                (
                    center[0],
                    center[1] + 10,
                ),
                center,
                width=2,
            )

            draw_glow_circle(
                surface,
                center,
                WHITE,
                3,
                glow_radius=10,
            )

        else:
            pulse = (
                1.0
                + math.sin(
                    pygame.time.get_ticks() / 90
                    + self.pulse_offset
                )
                * 0.15
            )

            radius = max(
                4,
                round(6 * pulse),
            )

            trail_direction = pygame.Vector2(
                self.dx,
                self.dy,
            )

            if trail_direction.length_squared() == 0:
                trail_direction = pygame.Vector2(
                    0,
                    1,
                )
            else:
                trail_direction = trail_direction.normalize()

            trail_end = (
                round(
                    center[0]
                    - trail_direction.x * 20
                ),
                round(
                    center[1]
                    - trail_direction.y * 20
                ),
            )

            pygame.draw.line(
                surface,
                DARK_PURPLE,
                trail_end,
                center,
                width=8,
            )

            pygame.draw.line(
                surface,
                PINK,
                (
                    round(
                        center[0]
                        - trail_direction.x * 14
                    ),
                    round(
                        center[1]
                        - trail_direction.y * 14
                    ),
                ),
                center,
                width=4,
            )

            draw_glow_circle(
                surface,
                center,
                PINK,
                radius,
                glow_radius=16,
            )

            pygame.draw.circle(
                surface,
                WHITE,
                center,
                max(2, radius // 2),
            )


# ============================================================
# PLAYER
# ============================================================

class Player:
    def __init__(self):
        self.rect = pygame.Rect(
            GAME_WIDTH // 2
            - PLAYER_WIDTH // 2,
            GAME_HEIGHT - 115,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )

        self.speed = PLAYER_SPEED
        self.lives = PLAYER_STARTING_LIVES

        self.invincible_until = 0
        self.shield_until = 0
        self.rapid_fire_until = 0
        self.triple_shot_until = 0

        self.last_shot_time = 0
        self.muzzle_flash_until = 0

        self.engine_animation = 0.0
        self.bank_amount = 0.0
        self.last_movement = 0

    def reset(self):
        self.rect.centerx = GAME_WIDTH // 2
        self.rect.bottom = GAME_HEIGHT - 35

        self.lives = PLAYER_STARTING_LIVES

        self.invincible_until = 0
        self.shield_until = 0
        self.rapid_fire_until = 0
        self.triple_shot_until = 0

        self.last_shot_time = 0
        self.muzzle_flash_until = 0

        self.engine_animation = 0.0
        self.bank_amount = 0.0
        self.last_movement = 0

    def update(self, keys):
        movement = 0

        if (
            keys[pygame.K_a]
            or keys[pygame.K_LEFT]
        ):
            movement -= self.speed

        if (
            keys[pygame.K_d]
            or keys[pygame.K_RIGHT]
        ):
            movement += self.speed

        self.rect.x += movement

        self.rect.x = clamp(
            self.rect.x,
            8,
            GAME_WIDTH - self.rect.width - 8,
        )

        target_bank = 0.0

        if movement < 0:
            target_bank = -1.0
        elif movement > 0:
            target_bank = 1.0

        self.bank_amount += (
            target_bank
            - self.bank_amount
        ) * 0.18

        self.last_movement = movement
        self.engine_animation += 0.18

    def can_shoot(self, current_time):
        cooldown = BASE_SHOT_COOLDOWN_MS

        if current_time < self.rapid_fire_until:
            cooldown = 100

        return (
            current_time
            - self.last_shot_time
            >= cooldown
        )

    def shoot(self, current_time):
        if not self.can_shoot(current_time):
            return []

        self.last_shot_time = current_time
        self.muzzle_flash_until = (
            current_time + 75
        )

        if (
            current_time
            < self.triple_shot_until
        ):
            return [
                Bullet(
                    self.rect.centerx - 15,
                    self.rect.top + 8,
                    dx=-2.5,
                    dy=-12.5,
                ),
                Bullet(
                    self.rect.centerx,
                    self.rect.top - 3,
                ),
                Bullet(
                    self.rect.centerx + 15,
                    self.rect.top + 8,
                    dx=2.5,
                    dy=-12.5,
                ),
            ]

        return [
            Bullet(
                self.rect.centerx,
                self.rect.top - 3,
            )
        ]

    def take_damage(self, current_time):
        if current_time < self.invincible_until:
            return False

        if current_time < self.shield_until:
            self.shield_until = 0
            self.invincible_until = (
                current_time + 900
            )
            return False

        self.lives -= 1

        self.invincible_until = (
            current_time
            + PLAYER_INVINCIBILITY_MS
        )

        return True

    def draw(
        self,
        surface,
        current_time,
        offset_x=0,
        offset_y=0,
    ):
        if (
            current_time
            < self.invincible_until
            and current_time % 180 < 90
        ):
            return

        rect = self.rect.move(
            offset_x,
            offset_y,
        )

        center = pygame.Vector2(
            rect.centerx,
            rect.centery,
        )

        draw_ship_shadow(
            surface,
            rect,
        )

        bank_shift = (
            self.bank_amount * 4
        )

        left_engine_center = pygame.Vector2(
            rect.left + 16,
            rect.bottom - 13,
        )

        right_engine_center = pygame.Vector2(
            rect.right - 16,
            rect.bottom - 13,
        )

        flame_length = (
            14
            + math.sin(
                self.engine_animation
            )
            * 4
            + random.randint(0, 4)
        )

        for engine_center in (
            left_engine_center,
            right_engine_center,
        ):
            outer_flame = [
                (
                    engine_center.x - 6,
                    engine_center.y,
                ),
                (
                    engine_center.x,
                    engine_center.y
                    + flame_length,
                ),
                (
                    engine_center.x + 6,
                    engine_center.y,
                ),
            ]

            pygame.draw.polygon(
                surface,
                ORANGE,
                [
                    (
                        round(point[0]),
                        round(point[1]),
                    )
                    for point in outer_flame
                ],
            )

            inner_flame = [
                (
                    engine_center.x - 3,
                    engine_center.y,
                ),
                (
                    engine_center.x,
                    engine_center.y
                    + flame_length * 0.7,
                ),
                (
                    engine_center.x + 3,
                    engine_center.y,
                ),
            ]

            pygame.draw.polygon(
                surface,
                ENGINE_WHITE,
                [
                    (
                        round(point[0]),
                        round(point[1]),
                    )
                    for point in inner_flame
                ],
            )

            draw_glow_circle(
                surface,
                (
                    round(engine_center.x),
                    round(engine_center.y + 4),
                ),
                ENGINE_BLUE,
                4,
                glow_radius=13,
            )

        # Outer silhouette.
        hull_points = [
            (
                0 + bank_shift,
                -31,
            ),
            (
                13 + bank_shift * 0.4,
                -16,
            ),
            (
                29,
                9,
            ),
            (
                24,
                25,
            ),
            (
                11,
                18,
            ),
            (
                5,
                28,
            ),
            (
                -5,
                28,
            ),
            (
                -11,
                18,
            ),
            (
                -24,
                25,
            ),
            (
                -29,
                9,
            ),
            (
                -13 + bank_shift * 0.4,
                -16,
            ),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(center.x + point[0]),
                    round(center.y + point[1]),
                )
                for point in hull_points
            ],
        )

        inner_hull = [
            (
                0 + bank_shift,
                -27,
            ),
            (
                11 + bank_shift * 0.35,
                -13,
            ),
            (
                25,
                9,
            ),
            (
                20,
                19,
            ),
            (
                9,
                13,
            ),
            (
                3,
                23,
            ),
            (
                -3,
                23,
            ),
            (
                -9,
                13,
            ),
            (
                -20,
                19,
            ),
            (
                -25,
                9,
            ),
            (
                -11 + bank_shift * 0.35,
                -13,
            ),
        ]

        pygame.draw.polygon(
            surface,
            LIGHT_BLUE,
            [
                (
                    round(center.x + point[0]),
                    round(center.y + point[1]),
                )
                for point in inner_hull
            ],
        )

        # Wing armor.
        left_wing = [
            (-8, -3),
            (-26, 8),
            (-21, 16),
            (-8, 10),
        ]

        right_wing = [
            (8, -3),
            (26, 8),
            (21, 16),
            (8, 10),
        ]

        pygame.draw.polygon(
            surface,
            BLUE,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in left_wing
            ],
        )

        pygame.draw.polygon(
            surface,
            BLUE,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in right_wing
            ],
        )

        # Central armor spine.
        spine = [
            (0, -24),
            (9, -7),
            (7, 17),
            (0, 23),
            (-7, 17),
            (-9, -7),
        ]

        pygame.draw.polygon(
            surface,
            MID_BLUE,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in spine
            ],
        )

        # Cockpit.
        cockpit = [
            (0, -20),
            (7, -7),
            (5, 5),
            (0, 10),
            (-5, 5),
            (-7, -7),
        ]

        pygame.draw.polygon(
            surface,
            WINDOW_BLUE,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in cockpit
            ],
        )

        cockpit_highlight = [
            (-2, -15),
            (2, -12),
            (2, -2),
            (-1, 2),
            (-3, -3),
        ]

        pygame.draw.polygon(
            surface,
            WINDOW_HIGHLIGHT,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in cockpit_highlight
            ],
        )

        # Panel lines.
        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                rect.centerx - 20,
                rect.centery + 9,
            ),
            (
                rect.centerx - 9,
                rect.centery + 13,
            ),
            width=2,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                rect.centerx + 20,
                rect.centery + 9,
            ),
            (
                rect.centerx + 9,
                rect.centery + 13,
            ),
            width=2,
        )

        # Wing weapon pods.
        for pod_x in (
            rect.centerx - 20,
            rect.centerx + 20,
        ):
            pod_rect = pygame.Rect(
                0,
                0,
                8,
                18,
            )

            pod_rect.center = (
                pod_x,
                rect.centery + 7,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                pod_rect.inflate(3, 3),
                border_radius=4,
            )

            pygame.draw.rect(
                surface,
                METAL_MID,
                pod_rect,
                border_radius=4,
            )

            pygame.draw.circle(
                surface,
                CYAN,
                (
                    pod_rect.centerx,
                    pod_rect.top + 3,
                ),
                2,
            )

        if (
            current_time
            < self.muzzle_flash_until
        ):
            flash_center = (
                rect.centerx,
                rect.top - 5,
            )

            draw_glow_circle(
                surface,
                flash_center,
                YELLOW,
                random.randint(6, 9),
                glow_radius=18,
            )

            pygame.draw.polygon(
                surface,
                WHITE,
                [
                    (
                        flash_center[0],
                        flash_center[1] - 12,
                    ),
                    (
                        flash_center[0] - 5,
                        flash_center[1] + 3,
                    ),
                    (
                        flash_center[0] + 5,
                        flash_center[1] + 3,
                    ),
                ],
            )

        if current_time < self.shield_until:
            shield_surface = pygame.Surface(
                (
                    rect.width + 42,
                    rect.height + 42,
                ),
                pygame.SRCALPHA,
            )

            shield_rect = shield_surface.get_rect()

            pulse = (
                2
                + int(
                    math.sin(
                        current_time / 120
                    )
                    * 2
                )
            )

            pygame.draw.ellipse(
                shield_surface,
                (70, 220, 255, 35),
                shield_rect.inflate(
                    -6,
                    -6,
                ),
            )

            pygame.draw.ellipse(
                shield_surface,
                (120, 245, 255, 210),
                shield_rect.inflate(
                    -10 + pulse,
                    -10 + pulse,
                ),
                width=3,
            )

            pygame.draw.arc(
                shield_surface,
                WHITE,
                shield_rect.inflate(
                    -16,
                    -16,
                ),
                0.2,
                1.5,
                width=2,
            )

            surface.blit(
                shield_surface,
                (
                    rect.centerx
                    - shield_surface.get_width() // 2,
                    rect.centery
                    - shield_surface.get_height() // 2,
                ),
            )


# ============================================================
# ENEMIES
# ============================================================

class Enemy:
    def __init__(
        self,
        enemy_type,
        wave,
    ):
        self.enemy_type = enemy_type

        if enemy_type == "basic":
            self.width = 50
            self.height = 44
            self.health = 1
            self.speed = random.uniform(
                1.5,
                2.2,
            )
            self.score_value = 1
            self.colour = RED

        elif enemy_type == "fast":
            self.width = 42
            self.height = 38
            self.health = 1
            self.speed = random.uniform(
                2.7,
                3.8,
            )
            self.score_value = 2
            self.colour = ORANGE

        elif enemy_type == "tough":
            self.width = 64
            self.height = 54

            self.health = (
                2
                + max(
                    0,
                    wave - 15,
                )
                // 10
            )

            self.speed = random.uniform(
                1.15,
                1.7,
            )

            self.score_value = 3
            self.colour = PURPLE

        else:
            raise ValueError(
                f"Unknown enemy type: {enemy_type}"
            )

        self.max_health = self.health

        difficulty_bonus = min(
            1.4,
            (wave - 1) * 0.045,
        )

        self.speed += difficulty_bonus

        self.rect = pygame.Rect(
            random.randint(
                20,
                GAME_WIDTH
                - self.width
                - 20,
            ),
            -self.height
            - random.randint(
                0,
                100,
            ),
            self.width,
            self.height,
        )

        self.x = float(
            self.rect.x
        )

        self.y = float(
            self.rect.y
        )

        self.start_x = self.x

        self.wave_offset = random.uniform(
            0,
            math.tau,
        )

        self.wave_strength = random.uniform(
            10,
            28,
        )

        self.hit_flash_until = 0

        self.engine_animation = random.uniform(
            0,
            math.tau,
        )

        self.bank_angle = 0.0

    def update(self, current_time):
        self.y += self.speed
        self.engine_animation += 0.16

        target_bank = 0.0

        if self.enemy_type == "fast":
            old_x = self.x

            self.x = (
                self.start_x
                + math.sin(
                    current_time / 340
                    + self.wave_offset
                )
                * self.wave_strength
            )

            horizontal_change = (
                self.x - old_x
            )

            target_bank = clamp(
                horizontal_change / 3,
                -1,
                1,
            )

        self.bank_angle += (
            target_bank
            - self.bank_angle
        ) * 0.18

        self.x = clamp(
            self.x,
            5,
            GAME_WIDTH
            - self.width
            - 5,
        )

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def take_damage(
        self,
        damage,
        current_time,
    ):
        self.health -= damage
        self.hit_flash_until = (
            current_time + 90
        )

        return self.health <= 0

    def draw(
        self,
        surface,
        current_time,
        offset_x=0,
        offset_y=0,
    ):
        rect = self.rect.move(
            offset_x,
            offset_y,
        )

        colour = (
            WHITE
            if current_time
            < self.hit_flash_until
            else self.colour
        )

        draw_ship_shadow(
            surface,
            rect,
            width_scale=0.72,
        )

        if self.enemy_type == "basic":
            self.draw_basic_ship(
                surface,
                rect,
                colour,
            )

        elif self.enemy_type == "fast":
            self.draw_fast_ship(
                surface,
                rect,
                colour,
            )

        elif self.enemy_type == "tough":
            self.draw_tough_ship(
                surface,
                rect,
                colour,
            )

            health_ratio = (
                self.health
                / self.max_health
            )

            health_bar = pygame.Rect(
                rect.left,
                rect.top - 10,
                rect.width,
                6,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                health_bar.inflate(
                    2,
                    2,
                ),
                border_radius=3,
            )

            pygame.draw.rect(
                surface,
                DARK_GREY,
                health_bar,
                border_radius=3,
            )

            pygame.draw.rect(
                surface,
                GREEN,
                (
                    health_bar.x,
                    health_bar.y,
                    int(
                        health_bar.width
                        * health_ratio
                    ),
                    health_bar.height,
                ),
                border_radius=3,
            )

    def draw_basic_ship(
        self,
        surface,
        rect,
        colour,
    ):
        center = pygame.Vector2(
            rect.centerx,
            rect.centery,
        )

        flame_length = (
            9
            + math.sin(
                self.engine_animation
            )
            * 3
        )

        engine_positions = (
            rect.centerx - 11,
            rect.centerx + 11,
        )

        for engine_x in engine_positions:
            pygame.draw.polygon(
                surface,
                ORANGE,
                [
                    (
                        engine_x - 4,
                        rect.top + 5,
                    ),
                    (
                        engine_x,
                        rect.top - flame_length,
                    ),
                    (
                        engine_x + 4,
                        rect.top + 5,
                    ),
                ],
            )

            pygame.draw.polygon(
                surface,
                YELLOW,
                [
                    (
                        engine_x - 2,
                        rect.top + 4,
                    ),
                    (
                        engine_x,
                        rect.top
                        - flame_length * 0.55,
                    ),
                    (
                        engine_x + 2,
                        rect.top + 4,
                    ),
                ],
            )

        outer_points = [
            (0, 23),
            (20, 6),
            (18, -8),
            (8, -20),
            (0, -15),
            (-8, -20),
            (-18, -8),
            (-20, 6),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in outer_points
            ],
        )

        inner_points = [
            (0, 19),
            (16, 5),
            (14, -6),
            (7, -16),
            (0, -12),
            (-7, -16),
            (-14, -6),
            (-16, 5),
        ]

        pygame.draw.polygon(
            surface,
            colour,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in inner_points
            ],
        )

        wing_left = [
            (-6, 1),
            (-18, -5),
            (-15, 8),
            (-5, 11),
        ]

        wing_right = [
            (6, 1),
            (18, -5),
            (15, 8),
            (5, 11),
        ]

        pygame.draw.polygon(
            surface,
            ENEMY_METAL,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in wing_left
            ],
        )

        pygame.draw.polygon(
            surface,
            ENEMY_METAL,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in wing_right
            ],
        )

        cockpit = [
            (0, 12),
            (7, 2),
            (4, -7),
            (0, -11),
            (-4, -7),
            (-7, 2),
        ]

        pygame.draw.polygon(
            surface,
            DARK_PURPLE,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in cockpit
            ],
        )

        draw_glow_circle(
            surface,
            (
                rect.centerx,
                rect.centery + 4,
            ),
            YELLOW,
            5,
            glow_radius=12,
        )

    def draw_fast_ship(
        self,
        surface,
        rect,
        colour,
    ):
        center = pygame.Vector2(
            rect.centerx,
            rect.centery,
        )

        shift = self.bank_angle * 3

        flame_length = (
            12
            + math.sin(
                self.engine_animation * 1.4
            )
            * 4
        )

        pygame.draw.polygon(
            surface,
            ORANGE,
            [
                (
                    rect.centerx - 5,
                    rect.top + 7,
                ),
                (
                    rect.centerx,
                    rect.top - flame_length,
                ),
                (
                    rect.centerx + 5,
                    rect.top + 7,
                ),
            ],
        )

        outer_points = [
            (
                shift,
                19,
            ),
            (
                19,
                -13,
            ),
            (
                7,
                -7,
            ),
            (
                0,
                -18,
            ),
            (
                -7,
                -7,
            ),
            (
                -19,
                -13,
            ),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in outer_points
            ],
        )

        inner_points = [
            (
                shift * 0.7,
                15,
            ),
            (
                15,
                -9,
            ),
            (
                6,
                -5,
            ),
            (
                0,
                -14,
            ),
            (
                -6,
                -5,
            ),
            (
                -15,
                -9,
            ),
        ]

        pygame.draw.polygon(
            surface,
            colour,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in inner_points
            ],
        )

        spine = [
            (0, 13),
            (5, 0),
            (0, -11),
            (-5, 0),
        ]

        pygame.draw.polygon(
            surface,
            YELLOW,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in spine
            ],
        )

        draw_glow_circle(
            surface,
            (
                rect.centerx,
                rect.centery - 1,
            ),
            WHITE,
            3,
            glow_radius=9,
        )

    def draw_tough_ship(
        self,
        surface,
        rect,
        colour,
    ):
        center = pygame.Vector2(
            rect.centerx,
            rect.centery,
        )

        flame_length = (
            10
            + math.sin(
                self.engine_animation
            )
            * 3
        )

        for engine_x in (
            rect.centerx - 17,
            rect.centerx + 17,
        ):
            pygame.draw.polygon(
                surface,
                DARK_PURPLE,
                [
                    (
                        engine_x - 6,
                        rect.top + 7,
                    ),
                    (
                        engine_x,
                        rect.top - flame_length,
                    ),
                    (
                        engine_x + 6,
                        rect.top + 7,
                    ),
                ],
            )

            pygame.draw.polygon(
                surface,
                PINK,
                [
                    (
                        engine_x - 3,
                        rect.top + 6,
                    ),
                    (
                        engine_x,
                        rect.top
                        - flame_length * 0.55,
                    ),
                    (
                        engine_x + 3,
                        rect.top + 6,
                    ),
                ],
            )

        outer_hull = [
            (0, 25),
            (28, 13),
            (30, -8),
            (19, -22),
            (8, -18),
            (0, -24),
            (-8, -18),
            (-19, -22),
            (-30, -8),
            (-28, 13),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in outer_hull
            ],
        )

        inner_hull = [
            (0, 20),
            (23, 10),
            (25, -6),
            (16, -17),
            (7, -14),
            (0, -19),
            (-7, -14),
            (-16, -17),
            (-25, -6),
            (-23, 10),
        ]

        pygame.draw.polygon(
            surface,
            colour,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in inner_hull
            ],
        )

        left_armor = [
            (-5, 5),
            (-24, 8),
            (-21, -7),
            (-7, -10),
        ]

        right_armor = [
            (5, 5),
            (24, 8),
            (21, -7),
            (7, -10),
        ]

        pygame.draw.polygon(
            surface,
            ENEMY_ARMOR,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in left_armor
            ],
        )

        pygame.draw.polygon(
            surface,
            ENEMY_ARMOR,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in right_armor
            ],
        )

        core_rect = pygame.Rect(
            0,
            0,
            24,
            30,
        )

        core_rect.center = (
            rect.centerx,
            rect.centery,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            core_rect.inflate(
                5,
                5,
            ),
            border_radius=8,
        )

        pygame.draw.rect(
            surface,
            DARK_BLUE,
            core_rect,
            border_radius=8,
        )

        pulse_radius = (
            7
            + int(
                math.sin(
                    pygame.time.get_ticks()
                    / 130
                )
                * 2
            )
        )

        draw_glow_circle(
            surface,
            rect.center,
            PINK,
            pulse_radius,
            glow_radius=17,
        )

        for cannon_x in (
            rect.centerx - 22,
            rect.centerx + 22,
        ):
            cannon_rect = pygame.Rect(
                0,
                0,
                7,
                18,
            )

            cannon_rect.center = (
                cannon_x,
                rect.centery + 9,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                cannon_rect.inflate(
                    3,
                    3,
                ),
                border_radius=3,
            )

            pygame.draw.rect(
                surface,
                METAL_MID,
                cannon_rect,
                border_radius=3,
            )

# ============================================================
# BOSS
# ============================================================

class Boss:
    def __init__(self, wave):
        self.width = 230
        self.height = 125

        self.rect = pygame.Rect(
            GAME_WIDTH // 2 - self.width // 2,
            -self.height,
            self.width,
            self.height,
        )

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.target_y = 95
        self.direction = random.choice((-1, 1))

        self.speed = 2.0 + wave * 0.035

        self.max_health = 20 + wave * 4
        self.health = self.max_health

        self.score_value = 20 + wave * 2

        self.last_shot_time = 0
        self.shot_delay = max(
            850,
            1250 - wave * 15,
        )

        self.hit_flash_until = 0

        self.engine_animation = random.uniform(
            0,
            math.tau,
        )

        self.core_animation = random.uniform(
            0,
            math.tau,
        )

        self.weapon_animation = 0.0

    def update(self, current_time):
        self.engine_animation += 0.13
        self.core_animation += 0.08
        self.weapon_animation += 0.05

        if self.y < self.target_y:
            self.y += 1.7

        else:
            self.x += (
                self.speed
                * self.direction
            )

            if self.x <= 18:
                self.x = 18
                self.direction = 1

            if (
                self.x + self.width
                >= GAME_WIDTH - 18
            ):
                self.x = (
                    GAME_WIDTH
                    - self.width
                    - 18
                )

                self.direction = -1

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def should_shoot(self, current_time):
        if self.y < self.target_y - 10:
            return False

        return (
            current_time
            - self.last_shot_time
            >= self.shot_delay
        )

    def shoot(
        self,
        current_time,
        player_rect,
    ):
        self.last_shot_time = current_time

        center_x = self.rect.centerx
        start_y = self.rect.bottom

        player_dx = (
            player_rect.centerx
            - center_x
        )

        player_dy = (
            player_rect.centery
            - start_y
        )

        length = max(
            1,
            math.hypot(
                player_dx,
                player_dy,
            ),
        )

        aimed_dx = (
            player_dx
            / length
            * 3.2
        )

        aimed_dy = (
            player_dy
            / length
            * 3.2
        )

        return [
            Bullet(
                center_x,
                start_y,
                dx=aimed_dx,
                dy=aimed_dy,
                friendly=False,
            ),
            Bullet(
                center_x - 68,
                start_y - 8,
                dx=-0.9,
                dy=3.7,
                friendly=False,
            ),
            Bullet(
                center_x + 68,
                start_y - 8,
                dx=0.9,
                dy=3.7,
                friendly=False,
            ),
        ]

    def take_damage(
        self,
        damage,
        current_time,
    ):
        self.health -= damage

        self.hit_flash_until = (
            current_time + 80
        )

        return self.health <= 0

    def draw(
        self,
        surface,
        current_time,
        offset_x=0,
        offset_y=0,
    ):
        rect = self.rect.move(
            offset_x,
            offset_y,
        )

        flash_active = (
            current_time
            < self.hit_flash_until
        )

        hull_colour = (
            WHITE
            if flash_active
            else DARK_RED
        )

        center = pygame.Vector2(
            rect.centerx,
            rect.centery,
        )

        draw_ship_shadow(
            surface,
            rect,
            width_scale=0.9,
        )

        # Main engine flames.
        engine_positions = (
            rect.centerx - 72,
            rect.centerx - 28,
            rect.centerx + 28,
            rect.centerx + 72,
        )

        flame_length = (
            18
            + math.sin(
                self.engine_animation
            )
            * 5
            + random.randint(0, 4)
        )

        for engine_x in engine_positions:
            pygame.draw.polygon(
                surface,
                DARK_PURPLE,
                [
                    (
                        engine_x - 10,
                        rect.top + 15,
                    ),
                    (
                        engine_x,
                        rect.top
                        - flame_length,
                    ),
                    (
                        engine_x + 10,
                        rect.top + 15,
                    ),
                ],
            )

            pygame.draw.polygon(
                surface,
                PINK,
                [
                    (
                        engine_x - 5,
                        rect.top + 12,
                    ),
                    (
                        engine_x,
                        rect.top
                        - flame_length * 0.65,
                    ),
                    (
                        engine_x + 5,
                        rect.top + 12,
                    ),
                ],
            )

            draw_glow_circle(
                surface,
                (
                    engine_x,
                    rect.top + 4,
                ),
                PINK,
                5,
                glow_radius=16,
            )

        # Outer armor silhouette.
        outer_hull = [
            (0, 58),
            (42, 48),
            (94, 40),
            (112, 18),
            (102, -17),
            (74, -45),
            (31, -53),
            (0, -43),
            (-31, -53),
            (-74, -45),
            (-102, -17),
            (-112, 18),
            (-94, 40),
            (-42, 48),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in outer_hull
            ],
        )

        inner_hull = [
            (0, 51),
            (39, 41),
            (87, 34),
            (103, 16),
            (93, -14),
            (68, -38),
            (29, -45),
            (0, -36),
            (-29, -45),
            (-68, -38),
            (-93, -14),
            (-103, 16),
            (-87, 34),
            (-39, 41),
        ]

        pygame.draw.polygon(
            surface,
            hull_colour,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in inner_hull
            ],
        )

        # Large side armor plates.
        left_armor = [
            (-14, 16),
            (-91, 28),
            (-84, -12),
            (-58, -31),
            (-17, -16),
        ]

        right_armor = [
            (14, 16),
            (91, 28),
            (84, -12),
            (58, -31),
            (17, -16),
        ]

        pygame.draw.polygon(
            surface,
            BOSS_ARMOR,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in left_armor
            ],
        )

        pygame.draw.polygon(
            surface,
            BOSS_ARMOR,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in right_armor
            ],
        )

        # Wing edge highlights.
        pygame.draw.line(
            surface,
            BOSS_HIGHLIGHT,
            (
                rect.centerx - 88,
                rect.centery + 24,
            ),
            (
                rect.centerx - 56,
                rect.centery - 25,
            ),
            width=4,
        )

        pygame.draw.line(
            surface,
            BOSS_HIGHLIGHT,
            (
                rect.centerx + 88,
                rect.centery + 24,
            ),
            (
                rect.centerx + 56,
                rect.centery - 25,
            ),
            width=4,
        )

        # Central command section.
        command_section = [
            (0, 42),
            (27, 24),
            (31, -19),
            (15, -38),
            (0, -31),
            (-15, -38),
            (-31, -19),
            (-27, 24),
        ]

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in command_section
            ],
        )

        inner_command = [
            (0, 35),
            (21, 19),
            (24, -15),
            (12, -31),
            (0, -25),
            (-12, -31),
            (-24, -15),
            (-21, 19),
        ]

        pygame.draw.polygon(
            surface,
            DARK_PURPLE,
            [
                (
                    round(center.x + x),
                    round(center.y + y),
                )
                for x, y in inner_command
            ],
        )

        # Animated energy core.
        pulse = (
            15
            + int(
                math.sin(
                    self.core_animation * 2
                )
                * 4
            )
        )

        draw_glow_circle(
            surface,
            rect.center,
            PINK,
            pulse,
            glow_radius=38,
        )

        pygame.draw.circle(
            surface,
            WHITE,
            rect.center,
            max(
                5,
                pulse // 3,
            ),
        )

        pygame.draw.circle(
            surface,
            CYAN,
            rect.center,
            max(
                2,
                pulse // 6,
            ),
        )

        # Core energy rings.
        ring_radius = (
            25
            + int(
                math.sin(
                    self.core_animation
                )
                * 4
            )
        )

        pygame.draw.circle(
            surface,
            PINK,
            rect.center,
            ring_radius,
            width=2,
        )

        pygame.draw.arc(
            surface,
            WHITE,
            (
                rect.centerx
                - ring_radius
                - 5,
                rect.centery
                - ring_radius
                - 5,
                ring_radius * 2 + 10,
                ring_radius * 2 + 10,
            ),
            self.core_animation,
            self.core_animation + 1.6,
            width=3,
        )

        # Side gun mounts.
        weapon_positions = (
            (
                rect.centerx - 76,
                rect.centery + 23,
            ),
            (
                rect.centerx + 76,
                rect.centery + 23,
            ),
        )

        for weapon_x, weapon_y in weapon_positions:
            pod = pygame.Rect(
                0,
                0,
                26,
                35,
            )

            pod.center = (
                weapon_x,
                weapon_y,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                pod.inflate(5, 5),
                border_radius=8,
            )

            pygame.draw.rect(
                surface,
                ENEMY_METAL,
                pod,
                border_radius=8,
            )

            barrel_left = pygame.Rect(
                0,
                0,
                6,
                24,
            )

            barrel_right = pygame.Rect(
                0,
                0,
                6,
                24,
            )

            barrel_left.midtop = (
                pod.centerx - 6,
                pod.bottom - 4,
            )

            barrel_right.midtop = (
                pod.centerx + 6,
                pod.bottom - 4,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                barrel_left.inflate(3, 3),
                border_radius=3,
            )

            pygame.draw.rect(
                surface,
                BLACK,
                barrel_right.inflate(3, 3),
                border_radius=3,
            )

            pygame.draw.rect(
                surface,
                METAL_LIGHT,
                barrel_left,
                border_radius=3,
            )

            pygame.draw.rect(
                surface,
                METAL_LIGHT,
                barrel_right,
                border_radius=3,
            )

            draw_glow_circle(
                surface,
                (
                    pod.centerx,
                    pod.centery - 4,
                ),
                PINK,
                4,
                glow_radius=10,
            )

        # Smaller defensive turrets.
        turret_positions = (
            (
                rect.centerx - 42,
                rect.centery - 25,
            ),
            (
                rect.centerx + 42,
                rect.centery - 25,
            ),
        )

        for turret_x, turret_y in turret_positions:
            pygame.draw.circle(
                surface,
                BLACK,
                (
                    turret_x,
                    turret_y,
                ),
                12,
            )

            pygame.draw.circle(
                surface,
                METAL_MID,
                (
                    turret_x,
                    turret_y,
                ),
                9,
            )

            pygame.draw.line(
                surface,
                BLACK,
                (
                    turret_x,
                    turret_y + 2,
                ),
                (
                    turret_x,
                    turret_y + 21,
                ),
                width=6,
            )

            pygame.draw.line(
                surface,
                METAL_LIGHT,
                (
                    turret_x,
                    turret_y + 5,
                ),
                (
                    turret_x,
                    turret_y + 21,
                ),
                width=2,
            )

        # Hull panel lines.
        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                rect.centerx - 67,
                rect.centery + 2,
            ),
            (
                rect.centerx - 28,
                rect.centery + 18,
            ),
            width=2,
        )

        pygame.draw.line(
            surface,
            METAL_LIGHT,
            (
                rect.centerx + 67,
                rect.centery + 2,
            ),
            (
                rect.centerx + 28,
                rect.centery + 18,
            ),
            width=2,
        )

        # Boss health bar.
        bar_width = 520

        bar_rect = pygame.Rect(
            GAME_WIDTH // 2
            - bar_width // 2,
            24,
            bar_width,
            20,
        )

        pygame.draw.rect(
            surface,
            BLACK,
            bar_rect.inflate(
                8,
                8,
            ),
            border_radius=10,
        )

        pygame.draw.rect(
            surface,
            DARK_GREY,
            bar_rect,
            border_radius=9,
        )

        health_ratio = max(
            0,
            self.health
            / self.max_health,
        )

        health_fill = pygame.Rect(
            bar_rect.x,
            bar_rect.y,
            int(
                bar_rect.width
                * health_ratio
            ),
            bar_rect.height,
        )

        pygame.draw.rect(
            surface,
            RED,
            health_fill,
            border_radius=9,
        )

        if health_fill.width > 8:
            highlight = pygame.Rect(
                health_fill.x + 3,
                health_fill.y + 3,
                health_fill.width - 6,
                max(
                    3,
                    health_fill.height // 3,
                ),
            )

            pygame.draw.rect(
                surface,
                (255, 120, 135),
                highlight,
                border_radius=5,
            )

        pygame.draw.rect(
            surface,
            WHITE,
            bar_rect,
            width=2,
            border_radius=9,
        )


# ============================================================
# POWER-UPS
# ============================================================

class PowerUp:
    TYPES = (
        "rapid_fire",
        "triple_shot",
        "shield",
        "extra_life",
    )

    COLOURS = {
        "rapid_fire": ORANGE,
        "triple_shot": PURPLE,
        "shield": CYAN,
        "extra_life": GREEN,
    }

    LABELS = {
        "rapid_fire": "R",
        "triple_shot": "3",
        "shield": "S",
        "extra_life": "+",
    }

    def __init__(
        self,
        x,
        y,
        forced_type=None,
    ):
        self.power_type = (
            forced_type
            or random.choice(
                self.TYPES
            )
        )

        self.rect = pygame.Rect(
            0,
            0,
            40,
            46,
        )

        self.rect.center = (
            x,
            y,
        )

        self.x = float(
            self.rect.x
        )

        self.y = float(
            self.rect.y
        )

        self.speed = 1.8

        self.rotation = random.uniform(
            0,
            math.tau,
        )

        self.pulse_offset = random.uniform(
            0,
            math.tau,
        )

    def update(self):
        self.y += self.speed
        self.rotation += 0.04

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def apply(
        self,
        player,
        current_time,
    ):
        if (
            self.power_type
            == "rapid_fire"
        ):
            player.rapid_fire_until = max(
                player.rapid_fire_until,
                current_time,
            ) + POWERUP_DURATION_MS

        elif (
            self.power_type
            == "triple_shot"
        ):
            player.triple_shot_until = max(
                player.triple_shot_until,
                current_time,
            ) + POWERUP_DURATION_MS

        elif (
            self.power_type
            == "shield"
        ):
            player.shield_until = max(
                player.shield_until,
                current_time,
            ) + POWERUP_DURATION_MS

        elif (
            self.power_type
            == "extra_life"
        ):
            player.lives = min(
                5,
                player.lives + 1,
            )

    def draw(
        self,
        surface,
        font,
        offset_x=0,
        offset_y=0,
    ):
        rect = self.rect.move(
            offset_x,
            offset_y,
        )

        colour = self.COLOURS[
            self.power_type
        ]

        center = (
            rect.centerx,
            rect.centery,
        )

        pulse = (
            1.0
            + math.sin(
                pygame.time.get_ticks()
                / 130
                + self.pulse_offset
            )
            * 0.12
        )

        glow_radius = int(
            20 * pulse
        )

        draw_glow_circle(
            surface,
            center,
            colour,
            6,
            glow_radius=glow_radius,
        )

        capsule_points = [
            (0, -22),
            (13, -14),
            (16, 0),
            (13, 14),
            (0, 22),
            (-13, 14),
            (-16, 0),
            (-13, -14),
        ]

        rotated_capsule = rotate_points(
            capsule_points,
            center,
            self.rotation,
        )

        pygame.draw.polygon(
            surface,
            BLACK,
            rotated_capsule,
        )

        inner_capsule = [
            (
                x * 0.78,
                y * 0.78,
            )
            for x, y in capsule_points
        ]

        pygame.draw.polygon(
            surface,
            colour,
            rotate_points(
                inner_capsule,
                center,
                self.rotation,
            ),
        )

        # Metallic capsule bands.
        band_direction = pygame.Vector2(
            math.cos(self.rotation),
            math.sin(self.rotation),
        )

        band_side = pygame.Vector2(
            -band_direction.y,
            band_direction.x,
        )

        for offset in (-10, 10):
            band_center = (
                pygame.Vector2(center)
                + band_direction * offset
            )

            band_start = (
                band_center
                - band_side * 11
            )

            band_end = (
                band_center
                + band_side * 11
            )

            pygame.draw.line(
                surface,
                METAL_LIGHT,
                (
                    round(band_start.x),
                    round(band_start.y),
                ),
                (
                    round(band_end.x),
                    round(band_end.y),
                ),
                width=3,
            )

        pygame.draw.circle(
            surface,
            BLACK,
            center,
            12,
        )

        pygame.draw.circle(
            surface,
            DARK_BLUE,
            center,
            9,
        )

        draw_text(
            surface,
            self.LABELS[
                self.power_type
            ],
            font,
            WHITE,
            center[0],
            center[1],
            center=True,
        )


# ============================================================
# MAIN GAME
# ============================================================

class SpaceShooterGame:
    def __init__(self):
        pygame.init()

        self.fullscreen = False

        self.screen = pygame.display.set_mode(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            pygame.SCALED,
        )

        pygame.display.set_caption(
            WINDOW_TITLE
        )

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.Font(
            None,
            78,
        )

        self.large_font = pygame.font.Font(
            None,
            54,
        )

        self.medium_font = pygame.font.Font(
            None,
            36,
        )

        self.normal_font = pygame.font.Font(
            None,
            29,
        )

        self.small_font = pygame.font.Font(
            None,
            22,
        )

        self.tiny_font = pygame.font.Font(
            None,
            18,
        )

        self.stars = [
            Star()
            for _ in range(165)
        ]

        self.nebula_clouds = [
            NebulaCloud()
            for _ in range(5)
        ]

        self.planet = DistantPlanet()

        self.player = Player()

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.powerups = []
        self.particles = []
        self.floating_texts = []

        self.boss = None

        self.leaderboard = (
            load_leaderboard()
        )

        self.leaderboard_status = (
            "Local leaderboard loaded."
        )
        self.leaderboard_loading = False
        self.score_uploading = False
        self.leaderboard_task = None
        self.score_submit_task = None

        self.player_name = ""
        self.state = "name_entry"

        self.score = 0
        self.wave = 1
        self.wave_kills = 0

        self.wave_goal = (
            self.get_wave_goal(1)
        )

        self.streak = 0
        self.highest_streak = 0
        self.multiplier = 1

        self.last_enemy_spawn_time = 0

        self.wave_message_until = 0
        self.wave_transition_until = 0

        self.screen_shake_strength = 0
        self.screen_shake_until = 0

        self.score_saved = False
        self.running = True

        self.create_buttons()

    def create_buttons(self):
        button_width = 320
        button_height = 62

        center_x = (
            GAME_WIDTH // 2
            - button_width // 2
        )

        self.play_button = Button(
            (
                center_x,
                320,
                button_width,
                button_height,
            ),
            "PLAY",
            self.medium_font,
            "SPACE",
        )

        self.leaderboard_button = Button(
            (
                center_x,
                405,
                button_width,
                button_height,
            ),
            "LEADERBOARD",
            self.medium_font,
            "L",
        )

        self.instructions_button = Button(
            (
                center_x,
                490,
                button_width,
                button_height,
            ),
            "HOW TO PLAY",
            self.medium_font,
            "H",
        )

        self.resume_button = Button(
            (
                center_x,
                310,
                button_width,
                button_height,
            ),
            "RESUME",
            self.medium_font,
            "P",
        )

        self.restart_button = Button(
            (
                center_x,
                395,
                button_width,
                button_height,
            ),
            "RESTART",
            self.medium_font,
            "R",
        )

        self.menu_button = Button(
            (
                center_x,
                480,
                button_width,
                button_height,
            ),
            "MAIN MENU",
            self.medium_font,
            "M",
        )

    def get_wave_goal(self, wave):
        if (
            wave
            % BOSS_WAVE_INTERVAL
            == 0
        ):
            return 0

        return (
            5
            + min(
                8,
                wave // 2,
            )
        )

    def get_unlocked_enemy_types(self):
        if self.wave <= 5:
            return [
                "basic"
            ]

        if self.wave <= 10:
            return [
                "basic",
                "fast",
            ]

        return [
            "basic",
            "fast",
            "tough",
        ]

    def choose_enemy_type(self):
        unlocked = (
            self.get_unlocked_enemy_types()
        )

        if unlocked == ["basic"]:
            return "basic"

        chance = random.random()

        if unlocked == [
            "basic",
            "fast",
        ]:
            if chance < 0.72:
                return "basic"

            return "fast"

        if chance < 0.58:
            return "basic"

        if chance < 0.84:
            return "fast"

        return "tough"

    def toggle_fullscreen(self):
        self.fullscreen = (
            not self.fullscreen
        )

        flags = pygame.SCALED

        if self.fullscreen:
            flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            flags,
        )

        pygame.display.set_caption(
            WINDOW_TITLE
        )

    def reset_game(self):
        current_time = (
            pygame.time.get_ticks()
        )

        self.player.reset()

        self.bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.floating_texts.clear()

        self.boss = None

        self.score = 0
        self.wave = 1
        self.wave_kills = 0

        self.wave_goal = (
            self.get_wave_goal(
                self.wave
            )
        )

        self.streak = 0
        self.highest_streak = 0
        self.multiplier = 1

        self.last_enemy_spawn_time = (
            current_time
        )

        self.wave_message_until = (
            current_time + 1800
        )

        self.wave_transition_until = (
            current_time + 900
        )

        self.score_saved = False
        self.state = "playing"

    def create_explosion(
        self,
        x,
        y,
        colour,
        amount=20,
        large=False,
    ):
        if (
            len(self.particles)
            >= MAX_EXPLOSION_PARTICLES
        ):
            return

        available_space = (
            MAX_EXPLOSION_PARTICLES
            - len(self.particles)
        )

        amount = min(
            amount,
            available_space,
        )

        for _ in range(amount):
            particle_colour = random.choice(
                (
                    colour,
                    YELLOW,
                    ORANGE,
                    WHITE,
                )
            )

            self.particles.append(
                Particle(
                    x,
                    y,
                    particle_colour,
                    large=large,
                    particle_type="spark",
                )
            )

        smoke_amount = (
            10 if large else 3
        )

        for _ in range(smoke_amount):
            if (
                len(self.particles)
                >= MAX_EXPLOSION_PARTICLES
            ):
                break

            self.particles.append(
                Particle(
                    x
                    + random.randint(
                        -10,
                        10,
                    ),
                    y
                    + random.randint(
                        -10,
                        10,
                    ),
                    random.choice(
                        (
                            (55, 60, 75),
                            (75, 65, 80),
                            (90, 75, 75),
                        )
                    ),
                    large=large,
                    particle_type="smoke",
                )
            )

    def add_screen_shake(
        self,
        strength,
        duration_ms,
    ):
        current_time = (
            pygame.time.get_ticks()
        )

        self.screen_shake_strength = max(
            self.screen_shake_strength,
            strength,
        )

        self.screen_shake_until = max(
            self.screen_shake_until,
            current_time + duration_ms,
        )

    def spawn_enemy(
        self,
        current_time,
    ):
        spawn_delay = max(
            600,
            ENEMY_BASE_SPAWN_DELAY_MS
            - (self.wave - 1) * 30,
        )

        if (
            current_time
            - self.last_enemy_spawn_time
            < spawn_delay
        ):
            return

        max_enemies = min(
            10,
            3 + self.wave // 2,
        )

        if (
            len(self.enemies)
            >= max_enemies
        ):
            return

        self.enemies.append(
            Enemy(
                self.choose_enemy_type(),
                self.wave,
            )
        )

        self.last_enemy_spawn_time = (
            current_time
        )

    def spawn_boss(self):
        self.enemies.clear()
        self.enemy_bullets.clear()

        self.boss = Boss(
            self.wave
        )

    def update_multiplier(self):
        if self.streak >= 20:
            self.multiplier = 4

        elif self.streak >= 10:
            self.multiplier = 3

        elif self.streak >= 5:
            self.multiplier = 2

        else:
            self.multiplier = 1

    def reset_streak(self):
        self.streak = 0
        self.multiplier = 1

    def award_enemy_kill(
        self,
        enemy,
    ):
        gained_score = (
            enemy.score_value
            * self.multiplier
        )

        self.score += gained_score
        self.streak += 1

        self.highest_streak = max(
            self.highest_streak,
            self.streak,
        )

        self.update_multiplier()

        self.wave_kills += 1

        self.floating_texts.append(
            FloatingText(
                f"+{gained_score}",
                enemy.rect.centerx,
                enemy.rect.centery,
                YELLOW,
            )
        )

        if (
            random.random()
            < POWERUP_DROP_CHANCE
        ):
            self.powerups.append(
                PowerUp(
                    enemy.rect.centerx,
                    enemy.rect.centery,
                )
            )

    def complete_wave(
        self,
        current_time,
    ):
        self.wave += 1
        self.wave_kills = 0

        self.wave_goal = (
            self.get_wave_goal(
                self.wave
            )
        )

        self.enemies.clear()
        self.enemy_bullets.clear()

        self.wave_message_until = (
            current_time + 1800
        )

        self.wave_transition_until = (
            current_time + 1300
        )

        if (
            self.wave
            % BOSS_WAVE_INTERVAL
            == 0
        ):
            self.spawn_boss()

    def open_leaderboard(self):
        self.state = "leaderboard"
        self.start_online_leaderboard_load()

    def start_online_leaderboard_load(self):
        if (
            self.leaderboard_task is not None
            and not self.leaderboard_task.done()
        ):
            return

        self.leaderboard_loading = True
        self.leaderboard_status = (
            "Loading all-time online scores..."
        )
        self.leaderboard_task = asyncio.create_task(
            load_online_leaderboard()
        )

    def start_online_score_submit(self):
        if (
            self.score_submit_task is not None
            and not self.score_submit_task.done()
        ):
            return

        self.score_uploading = True
        self.leaderboard_status = (
            "Saving score online..."
        )
        self.score_submit_task = asyncio.create_task(
            submit_online_score(
                self.player_name,
                self.score,
                self.wave,
            )
        )

    def update_online_leaderboard_tasks(self):
        if (
            self.score_submit_task is not None
            and self.score_submit_task.done()
        ):
            try:
                success, message = (
                    self.score_submit_task.result()
                )
            except Exception as error:
                success = False
                message = (
                    "Online score error: "
                    f"{error}"
                )

            self.score_submit_task = None
            self.score_uploading = False
            self.leaderboard_status = message

            if success:
                self.start_online_leaderboard_load()

        if (
            self.leaderboard_task is not None
            and self.leaderboard_task.done()
        ):
            try:
                online_scores, message = (
                    self.leaderboard_task.result()
                )
            except Exception as error:
                online_scores = []
                message = (
                    "Online leaderboard error: "
                    f"{error}"
                )

            self.leaderboard_task = None
            self.leaderboard_loading = False

            if online_scores:
                self.leaderboard = online_scores
                save_leaderboard(self.leaderboard)
            elif not self.leaderboard:
                self.leaderboard = load_leaderboard()

            self.leaderboard_status = message

    def finish_game(self):
        if not self.score_saved:
            add_leaderboard_score(
                self.leaderboard,
                self.player_name,
                self.score,
                self.wave,
            )

            self.score_saved = True
            self.start_online_score_submit()

        self.state = "game_over"

    def damage_player(
        self,
        current_time,
    ):
        actual_damage = (
            self.player.take_damage(
                current_time
            )
        )

        self.add_screen_shake(
            7,
            300,
        )

        self.create_explosion(
            self.player.rect.centerx,
            self.player.rect.centery,
            LIGHT_BLUE,
            amount=25,
            large=True,
        )

        if actual_damage:
            self.reset_streak()

        if self.player.lives <= 0:
            self.finish_game()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            alt_enter = (
                event.key == pygame.K_RETURN
                and bool(event.mod & pygame.KMOD_ALT)
            )

            if event.key == pygame.K_F11 or alt_enter:
                self.toggle_fullscreen()
                return

        if self.state == "name_entry":
            self.handle_name_entry(event)

        elif self.state == "menu":
            self.handle_menu(event)

        elif self.state == "playing":
            if (
                event.type == pygame.KEYDOWN
                and event.key
                in (
                    pygame.K_p,
                    pygame.K_ESCAPE,
                )
            ):
                self.state = "paused"

        elif self.state == "paused":
            self.handle_paused(event)

        elif self.state == "game_over":
            self.handle_game_over(event)

        elif self.state in (
            "leaderboard",
            "instructions",
        ):
            if (
                event.type == pygame.KEYDOWN
                and event.key
                in (
                    pygame.K_ESCAPE,
                    pygame.K_RETURN,
                    pygame.K_m,
                )
            ):
                self.state = "menu"

    def handle_name_entry(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            cleaned_name = (
                self.player_name.strip()
            )

            if cleaned_name:
                self.player_name = (
                    cleaned_name[:15]
                )

                self.state = "menu"

        elif event.key == pygame.K_BACKSPACE:
            self.player_name = (
                self.player_name[:-1]
            )

        elif event.unicode.isprintable():
            if len(self.player_name) < 15:
                self.player_name += (
                    event.unicode
                )

    def handle_menu(self, event):
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        ):
            self.reset_game()

        elif (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_l
        ):
            self.open_leaderboard()

        elif (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_h
        ):
            self.state = "instructions"

        elif self.play_button.clicked(event):
            self.reset_game()

        elif self.leaderboard_button.clicked(
            event
        ):
            self.open_leaderboard()

        elif self.instructions_button.clicked(
            event
        ):
            self.state = "instructions"

    def handle_paused(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_p,
                pygame.K_ESCAPE,
            ):
                self.state = "playing"

            elif event.key == pygame.K_r:
                self.reset_game()

            elif event.key == pygame.K_m:
                self.state = "menu"

        elif self.resume_button.clicked(event):
            self.state = "playing"

        elif self.restart_button.clicked(event):
            self.reset_game()

        elif self.menu_button.clicked(event):
            self.state = "menu"

    def handle_game_over(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_r:
            self.reset_game()

        elif event.key == pygame.K_l:
            self.open_leaderboard()

        elif event.key in (
            pygame.K_m,
            pygame.K_ESCAPE,
            pygame.K_RETURN,
        ):
            self.state = "menu"

    def update_buttons(self):
        mouse_pos = pygame.mouse.get_pos()

        for button in (
            self.play_button,
            self.leaderboard_button,
            self.instructions_button,
            self.resume_button,
            self.restart_button,
            self.menu_button,
        ):
            button.update(mouse_pos)

    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()

            if particle.life <= 0:
                self.particles.remove(
                    particle
                )

        for text in self.floating_texts[:]:
            text.update()

            if text.life <= 0:
                self.floating_texts.remove(
                    text
                )

    def update_playing(self, current_time):
        keys = pygame.key.get_pressed()

        self.player.update(keys)

        if keys[pygame.K_SPACE]:
            self.bullets.extend(
                self.player.shoot(
                    current_time
                )
            )

        for star in self.stars:
            star.update()

        for cloud in self.nebula_clouds:
            cloud.update()

        self.update_bullets(
            current_time
        )

        self.update_enemies(
            current_time
        )

        self.update_boss(
            current_time
        )

        self.update_powerups(
            current_time
        )

        self.update_particles()

        self.check_collisions(
            current_time
        )

        if (
            self.state != "playing"
        ):
            return

        if (
            current_time
            < self.wave_transition_until
        ):
            return

        if (
            self.wave
            % BOSS_WAVE_INTERVAL
            == 0
        ):
            if self.boss is None:
                self.complete_wave(
                    current_time
                )

        else:
            self.spawn_enemy(
                current_time
            )

            if (
                self.wave_kills
                >= self.wave_goal
            ):
                self.complete_wave(
                    current_time
                )

    def update_bullets(
        self,
        current_time,
    ):
        for bullet in self.bullets[:]:
            bullet.update()

            if bullet.outside_screen():
                self.bullets.remove(
                    bullet
                )

        for bullet in self.enemy_bullets[:]:
            bullet.update()

            if bullet.outside_screen():
                self.enemy_bullets.remove(
                    bullet
                )

    def update_enemies(
        self,
        current_time,
    ):
        for enemy in self.enemies[:]:
            enemy.update(
                current_time
            )

            if (
                enemy.rect.top
                > GAME_HEIGHT
            ):
                self.enemies.remove(
                    enemy
                )

                self.reset_streak()

                self.damage_player(
                    current_time
                )

                if self.state != "playing":
                    return

    def update_boss(
        self,
        current_time,
    ):
        if self.boss is None:
            return

        self.boss.update(
            current_time
        )

        if self.boss.should_shoot(
            current_time
        ):
            self.enemy_bullets.extend(
                self.boss.shoot(
                    current_time,
                    self.player.rect,
                )
            )

    def update_powerups(
        self,
        current_time,
    ):
        for powerup in self.powerups[:]:
            powerup.update()

            if powerup.rect.top > GAME_HEIGHT:
                self.powerups.remove(
                    powerup
                )

    def check_collisions(
        self,
        current_time,
    ):
        self.check_player_bullet_collisions(
            current_time
        )

        if self.state != "playing":
            return

        self.check_enemy_collisions(
            current_time
        )

        if self.state != "playing":
            return

        self.check_enemy_bullet_collisions(
            current_time
        )

        if self.state != "playing":
            return

        self.check_powerup_collisions(
            current_time
        )

    def check_player_bullet_collisions(
        self,
        current_time,
    ):
        for bullet in self.bullets[:]:
            hit_something = False

            for enemy in self.enemies[:]:
                if not bullet.rect.colliderect(
                    enemy.rect
                ):
                    continue

                hit_something = True

                destroyed = (
                    enemy.take_damage(
                        bullet.damage,
                        current_time,
                    )
                )

                self.create_explosion(
                    bullet.rect.centerx,
                    bullet.rect.centery,
                    enemy.colour,
                    amount=6,
                )

                if destroyed:
                    self.award_enemy_kill(
                        enemy
                    )

                    self.create_explosion(
                        enemy.rect.centerx,
                        enemy.rect.centery,
                        enemy.colour,
                        amount=28,
                        large=True,
                    )

                    self.add_screen_shake(
                        3,
                        150,
                    )

                    self.enemies.remove(
                        enemy
                    )

                break

            if (
                not hit_something
                and self.boss is not None
                and bullet.rect.colliderect(
                    self.boss.rect
                )
            ):
                hit_something = True

                boss_destroyed = (
                    self.boss.take_damage(
                        bullet.damage,
                        current_time,
                    )
                )

                self.create_explosion(
                    bullet.rect.centerx,
                    bullet.rect.centery,
                    PINK,
                    amount=8,
                )

                if boss_destroyed:
                    boss_score = (
                        self.boss.score_value
                        * self.multiplier
                    )

                    self.score += boss_score
                    self.streak += 1

                    self.highest_streak = max(
                        self.highest_streak,
                        self.streak,
                    )

                    self.update_multiplier()

                    boss_center = (
                        self.boss.rect.center
                    )

                    self.floating_texts.append(
                        FloatingText(
                            f"+{boss_score}",
                            boss_center[0],
                            boss_center[1],
                            YELLOW,
                        )
                    )

                    self.create_explosion(
                        boss_center[0],
                        boss_center[1],
                        PINK,
                        amount=90,
                        large=True,
                    )

                    self.add_screen_shake(
                        14,
                        800,
                    )

                    self.powerups.append(
                        PowerUp(
                            boss_center[0],
                            boss_center[1],
                            forced_type=random.choice(
                                (
                                    "rapid_fire",
                                    "triple_shot",
                                    "shield",
                                    "extra_life",
                                )
                            ),
                        )
                    )

                    self.boss = None
                    self.enemy_bullets.clear()

            if hit_something:
                if bullet in self.bullets:
                    self.bullets.remove(
                        bullet
                    )

    def check_enemy_collisions(
        self,
        current_time,
    ):
        for enemy in self.enemies[:]:
            if not enemy.rect.colliderect(
                self.player.rect
            ):
                continue

            self.create_explosion(
                enemy.rect.centerx,
                enemy.rect.centery,
                enemy.colour,
                amount=30,
                large=True,
            )

            self.add_screen_shake(
                8,
                350,
            )

            self.enemies.remove(
                enemy
            )

            self.damage_player(
                current_time
            )

            if self.state != "playing":
                return

    def check_enemy_bullet_collisions(
        self,
        current_time,
    ):
        for bullet in self.enemy_bullets[:]:
            if not bullet.rect.colliderect(
                self.player.rect
            ):
                continue

            self.enemy_bullets.remove(
                bullet
            )

            self.create_explosion(
                bullet.rect.centerx,
                bullet.rect.centery,
                PINK,
                amount=14,
            )

            self.damage_player(
                current_time
            )

            if self.state != "playing":
                return

    def check_powerup_collisions(
        self,
        current_time,
    ):
        for powerup in self.powerups[:]:
            if not powerup.rect.colliderect(
                self.player.rect
            ):
                continue

            powerup.apply(
                self.player,
                current_time,
            )

            self.create_explosion(
                powerup.rect.centerx,
                powerup.rect.centery,
                PowerUp.COLOURS[
                    powerup.power_type
                ],
                amount=22,
            )

            self.floating_texts.append(
                FloatingText(
                    powerup.power_type
                    .replace("_", " ")
                    .title(),
                    powerup.rect.centerx,
                    powerup.rect.centery,
                    WHITE,
                )
            )

            self.powerups.remove(
                powerup
            )

    def get_screen_shake_offset(
        self,
        current_time,
    ):
        if (
            current_time
            >= self.screen_shake_until
        ):
            self.screen_shake_strength = 0
            return 0, 0

        return (
            random.randint(
                -self.screen_shake_strength,
                self.screen_shake_strength,
            ),
            random.randint(
                -self.screen_shake_strength,
                self.screen_shake_strength,
            ),
        )

    def draw_background(self):
        self.screen.fill(
            SPACE_BLACK
        )

        background_gradient = pygame.Surface(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        for y in range(
            0,
            GAME_HEIGHT,
            12,
        ):
            progress = (
                y / GAME_HEIGHT
            )

            colour = (
                int(
                    DEEP_BLUE[0]
                    * (1 - progress)
                    + SPACE_BLACK[0]
                    * progress
                ),
                int(
                    DEEP_BLUE[1]
                    * (1 - progress)
                    + SPACE_BLACK[1]
                    * progress
                ),
                int(
                    DEEP_BLUE[2]
                    * (1 - progress)
                    + SPACE_BLACK[2]
                    * progress
                ),
                255,
            )

            pygame.draw.rect(
                background_gradient,
                colour,
                (
                    0,
                    y,
                    GAME_WIDTH,
                    12,
                ),
            )

        self.screen.blit(
            background_gradient,
            (0, 0),
        )

        for cloud in self.nebula_clouds:
            cloud.draw(
                self.screen
            )

        self.planet.draw(
            self.screen
        )

        for star in self.stars:
            star.draw(
                self.screen
            )

    def draw_game_objects(
        self,
        current_time,
    ):
        offset_x, offset_y = (
            self.get_screen_shake_offset(
                current_time
            )
        )

        for powerup in self.powerups:
            powerup.draw(
                self.screen,
                self.normal_font,
                offset_x,
                offset_y,
            )

        for enemy in self.enemies:
            enemy.draw(
                self.screen,
                current_time,
                offset_x,
                offset_y,
            )

        if self.boss is not None:
            self.boss.draw(
                self.screen,
                current_time,
                offset_x,
                offset_y,
            )

        for bullet in self.bullets:
            bullet.draw(
                self.screen,
                offset_x,
                offset_y,
            )

        for bullet in self.enemy_bullets:
            bullet.draw(
                self.screen,
                offset_x,
                offset_y,
            )

        self.player.draw(
            self.screen,
            current_time,
            offset_x,
            offset_y,
        )

        for particle in self.particles:
            particle.draw(
                self.screen,
                offset_x,
                offset_y,
            )

        for text in self.floating_texts:
            text.draw(
                self.screen,
                self.small_font,
                offset_x,
                offset_y,
            )

    def draw_hud(
        self,
        current_time,
    ):
        hud_rect = pygame.Rect(
            18,
            16,
            270,
            154,
        )

        draw_panel(
            self.screen,
            hud_rect,
            fill=(12, 24, 56),
            border=LIGHT_BLUE,
        )

        draw_text(
            self.screen,
            f"Score  {self.score}",
            self.normal_font,
            YELLOW,
            hud_rect.x + 18,
            hud_rect.y + 14,
        )

        draw_text(
            self.screen,
            f"Lives  {self.player.lives}",
            self.small_font,
            WHITE,
            hud_rect.x + 18,
            hud_rect.y + 51,
        )

        draw_text(
            self.screen,
            f"Wave  {self.wave}",
            self.small_font,
            WHITE,
            hud_rect.x + 18,
            hud_rect.y + 80,
        )

        draw_text(
            self.screen,
            f"Streak  {self.streak}",
            self.small_font,
            WHITE,
            hud_rect.x + 18,
            hud_rect.y + 109,
        )

        draw_text(
            self.screen,
            f"x{self.multiplier}",
            self.large_font,
            CYAN,
            hud_rect.right - 18,
            hud_rect.y + 72,
            right=True,
        )

        if (
            self.wave
            % BOSS_WAVE_INTERVAL
            != 0
        ):
            progress_width = 250

            progress_rect = pygame.Rect(
                GAME_WIDTH
                - progress_width
                - 24,
                24,
                progress_width,
                22,
            )

            pygame.draw.rect(
                self.screen,
                BLACK,
                progress_rect.inflate(
                    6,
                    6,
                ),
                border_radius=10,
            )

            pygame.draw.rect(
                self.screen,
                DARK_GREY,
                progress_rect,
                border_radius=8,
            )

            progress = min(
                1.0,
                self.wave_kills
                / max(
                    1,
                    self.wave_goal,
                ),
            )

            pygame.draw.rect(
                self.screen,
                BLUE,
                (
                    progress_rect.x,
                    progress_rect.y,
                    int(
                        progress_rect.width
                        * progress
                    ),
                    progress_rect.height,
                ),
                border_radius=8,
            )

            pygame.draw.rect(
                self.screen,
                WHITE,
                progress_rect,
                width=2,
                border_radius=8,
            )

            draw_text(
                self.screen,
                (
                    f"Wave progress "
                    f"{self.wave_kills}/"
                    f"{self.wave_goal}"
                ),
                self.small_font,
                WHITE,
                progress_rect.centerx,
                progress_rect.bottom + 18,
                center=True,
            )

        active_powerups = []

        if (
            current_time
            < self.player.rapid_fire_until
        ):
            active_powerups.append(
                (
                    "Rapid Fire",
                    self.player.rapid_fire_until,
                    ORANGE,
                )
            )

        if (
            current_time
            < self.player.triple_shot_until
        ):
            active_powerups.append(
                (
                    "Triple Shot",
                    self.player.triple_shot_until,
                    PURPLE,
                )
            )

        if (
            current_time
            < self.player.shield_until
        ):
            active_powerups.append(
                (
                    "Shield",
                    self.player.shield_until,
                    CYAN,
                )
            )

        power_y = 190

        for (
            power_name,
            power_until,
            power_colour,
        ) in active_powerups:
            seconds_left = max(
                0,
                math.ceil(
                    (
                        power_until
                        - current_time
                    )
                    / 1000
                ),
            )

            power_rect = pygame.Rect(
                18,
                power_y,
                190,
                30,
            )

            pygame.draw.rect(
                self.screen,
                BLACK,
                power_rect.move(
                    0,
                    3,
                ),
                border_radius=8,
            )

            pygame.draw.rect(
                self.screen,
                power_colour,
                power_rect,
                border_radius=8,
            )

            draw_text(
                self.screen,
                (
                    f"{power_name} "
                    f"{seconds_left}s"
                ),
                self.tiny_font,
                WHITE,
                power_rect.centerx,
                power_rect.centery,
                center=True,
            )

            power_y += 38

        draw_text(
            self.screen,
            "F11 or Alt+Enter: Fullscreen",
            self.tiny_font,
            GREY,
            GAME_WIDTH - 18,
            GAME_HEIGHT - 28,
            right=True,
        )

    def draw_name_entry(
        self,
        current_time,
    ):
        title_panel = pygame.Rect(
            GAME_WIDTH // 2 - 350,
            105,
            700,
            500,
        )

        draw_panel(
            self.screen,
            title_panel,
            fill=(10, 22, 52),
            border=LIGHT_BLUE,
            border_width=3,
        )

        draw_text(
            self.screen,
            "MATTHEW'S",
            self.large_font,
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            170,
            center=True,
        )

        draw_text(
            self.screen,
            "SPACE SHOOTER",
            self.title_font,
            WHITE,
            GAME_WIDTH // 2,
            230,
            center=True,
        )

        draw_text(
            self.screen,
            "Enter your pilot name",
            self.medium_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            335,
            center=True,
        )

        entry_rect = pygame.Rect(
            GAME_WIDTH // 2 - 210,
            390,
            420,
            72,
        )

        pygame.draw.rect(
            self.screen,
            BLACK,
            entry_rect.move(
                0,
                5,
            ),
            border_radius=12,
        )

        pygame.draw.rect(
            self.screen,
            DARK_BLUE,
            entry_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            self.screen,
            CYAN,
            entry_rect,
            width=3,
            border_radius=12,
        )

        shown_name = self.player_name

        if current_time % 1000 < 500:
            shown_name += "|"

        draw_text(
            self.screen,
            shown_name,
            self.large_font,
            WHITE,
            entry_rect.centerx,
            entry_rect.centery,
            center=True,
        )

        draw_text(
            self.screen,
            "Press Enter to continue",
            self.normal_font,
            GREY,
            GAME_WIDTH // 2,
            520,
            center=True,
        )

    def draw_menu(self):
        draw_text(
            self.screen,
            "MATTHEW'S SPACE SHOOTER",
            self.title_font,
            WHITE,
            GAME_WIDTH // 2,
            135,
            center=True,
        )

        draw_text(
            self.screen,
            f"Pilot: {self.player_name}",
            self.normal_font,
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            225,
            center=True,
        )

        self.play_button.draw(
            self.screen
        )

        self.leaderboard_button.draw(
            self.screen
        )

        self.instructions_button.draw(
            self.screen
        )

        draw_text(
            self.screen,
            "F11 or Alt+Enter for fullscreen",
            self.small_font,
            GREY,
            GAME_WIDTH // 2,
            610,
            center=True,
        )

    def draw_pause(self):
        overlay = pygame.Surface(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (0, 0, 0, 185)
        )

        self.screen.blit(
            overlay,
            (0, 0),
        )

        pause_panel = pygame.Rect(
            GAME_WIDTH // 2 - 220,
            180,
            440,
            420,
        )

        draw_panel(
            self.screen,
            pause_panel,
            fill=(12, 24, 56),
            border=CYAN,
            border_width=3,
        )

        draw_text(
            self.screen,
            "PAUSED",
            self.title_font,
            WHITE,
            GAME_WIDTH // 2,
            235,
            center=True,
        )

        self.resume_button.draw(
            self.screen
        )

        self.restart_button.draw(
            self.screen
        )

        self.menu_button.draw(
            self.screen
        )

    def draw_game_over(self):
        game_over_panel = pygame.Rect(
            GAME_WIDTH // 2 - 350,
            105,
            700,
            520,
        )

        draw_panel(
            self.screen,
            game_over_panel,
            fill=(35, 13, 34),
            border=PINK,
            border_width=3,
        )

        draw_text(
            self.screen,
            "MISSION FAILED",
            self.title_font,
            RED,
            GAME_WIDTH // 2,
            180,
            center=True,
        )

        draw_text(
            self.screen,
            f"Final score: {self.score}",
            self.large_font,
            YELLOW,
            GAME_WIDTH // 2,
            290,
            center=True,
        )

        draw_text(
            self.screen,
            f"Wave reached: {self.wave}",
            self.normal_font,
            WHITE,
            GAME_WIDTH // 2,
            360,
            center=True,
        )

        draw_text(
            self.screen,
            (
                "Highest streak: "
                f"{self.highest_streak}"
            ),
            self.normal_font,
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            410,
            center=True,
        )

        draw_text(
            self.screen,
            "R: Restart",
            self.normal_font,
            WHITE,
            GAME_WIDTH // 2,
            500,
            center=True,
        )

        draw_text(
            self.screen,
            "L: Leaderboard   M: Menu",
            self.small_font,
            GREY,
            GAME_WIDTH // 2,
            555,
            center=True,
        )

    def draw_leaderboard(self):
        panel = pygame.Rect(
            GAME_WIDTH // 2 - 410,
            75,
            820,
            590,
        )

        draw_panel(
            self.screen,
            panel,
            fill=(11, 23, 52),
            border=YELLOW,
            border_width=3,
        )

        draw_text(
            self.screen,
            "LEADERBOARD",
            self.title_font,
            YELLOW,
            GAME_WIDTH // 2,
            125,
            center=True,
        )

        header_y = 200

        draw_text(
            self.screen,
            "Rank",
            self.small_font,
            LIGHT_BLUE,
            panel.left + 55,
            header_y,
            center=True,
        )

        draw_text(
            self.screen,
            "Pilot",
            self.small_font,
            LIGHT_BLUE,
            panel.left + 190,
            header_y,
            center=True,
        )

        draw_text(
            self.screen,
            "Score",
            self.small_font,
            LIGHT_BLUE,
            panel.left + 490,
            header_y,
            center=True,
        )

        draw_text(
            self.screen,
            "Wave",
            self.small_font,
            LIGHT_BLUE,
            panel.left + 690,
            header_y,
            center=True,
        )

        pygame.draw.line(
            self.screen,
            LIGHT_BLUE,
            (
                panel.left + 30,
                header_y + 28,
            ),
            (
                panel.right - 30,
                header_y + 28,
            ),
            width=2,
        )

        if not self.leaderboard:
            draw_text(
                self.screen,
                "No scores yet",
                self.large_font,
                GREY,
                GAME_WIDTH // 2,
                360,
                center=True,
            )

        else:
            y = 250

            for position, entry in enumerate(
                self.leaderboard,
                start=1,
            ):
                row_rect = pygame.Rect(
                    panel.left + 30,
                    y - 10,
                    panel.width - 60,
                    40,
                )

                pygame.draw.rect(
                    self.screen,
                    (
                        20,
                        37,
                        74,
                    )
                    if position % 2
                    else (
                        15,
                        29,
                        62,
                    ),
                    row_rect,
                    border_radius=8,
                )

                rank_colour = (
                    YELLOW
                    if position == 1
                    else LIGHT_BLUE
                    if position == 2
                    else PINK
                    if position == 3
                    else WHITE
                )

                draw_text(
                    self.screen,
                    str(position),
                    self.normal_font,
                    rank_colour,
                    panel.left + 55,
                    y + 8,
                    center=True,
                )

                draw_text(
                    self.screen,
                    entry["name"],
                    self.normal_font,
                    WHITE,
                    panel.left + 190,
                    y - 5,
                )

                draw_text(
                    self.screen,
                    str(
                        entry["score"]
                    ),
                    self.normal_font,
                    YELLOW,
                    panel.left + 490,
                    y + 8,
                    center=True,
                )

                draw_text(
                    self.screen,
                    str(
                        entry["wave"]
                    ),
                    self.normal_font,
                    LIGHT_BLUE,
                    panel.left + 690,
                    y + 8,
                    center=True,
                )

                y += 46

        status_colour = (
            CYAN
            if self.leaderboard_loading
            or self.score_uploading
            else GREY
        )

        draw_text(
            self.screen,
            self.leaderboard_status,
            self.tiny_font,
            status_colour,
            GAME_WIDTH // 2,
            600,
            center=True,
        )

        draw_text(
            self.screen,
            "Press Enter, M, or Escape to return",
            self.small_font,
            GREY,
            GAME_WIDTH // 2,
            625,
            center=True,
        )

    def draw_instructions(self):
        panel = pygame.Rect(
            GAME_WIDTH // 2 - 410,
            75,
            820,
            590,
        )

        draw_panel(
            self.screen,
            panel,
            fill=(11, 23, 52),
            border=CYAN,
            border_width=3,
        )

        draw_text(
            self.screen,
            "HOW TO PLAY",
            self.title_font,
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            125,
            center=True,
        )

        instructions = [
            (
                "Move",
                "A and D or the left and right arrow keys",
            ),
            (
                "Shoot",
                "Hold Space",
            ),
            (
                "Pause",
                "P or Escape",
            ),
            (
                "Lives",
                "You begin with three lives",
            ),
            (
                "Enemies",
                "New enemy types unlock after boss fights",
            ),
            (
                "Bosses",
                "A boss appears every five waves",
            ),
            (
                "Streak",
                "Consecutive kills increase your multiplier",
            ),
            (
                "Power-ups",
                "Collect rapid fire, triple shot, shields, and lives",
            ),
        ]

        y = 205

        for title, description in instructions:
            pygame.draw.circle(
                self.screen,
                CYAN,
                (
                    panel.left + 75,
                    y + 8,
                ),
                5,
            )

            draw_text(
                self.screen,
                title,
                self.normal_font,
                WHITE,
                panel.left + 100,
                y - 6,
            )

            draw_text(
                self.screen,
                description,
                self.small_font,
                LIGHT_GREY,
                panel.left + 280,
                y,
            )

            y += 48

        draw_text(
            self.screen,
            "Press Enter, M, or Escape to return",
            self.small_font,
            GREY,
            GAME_WIDTH // 2,
            625,
            center=True,
        )

    def draw_wave_message(
        self,
        current_time,
    ):
        if (
            current_time
            >= self.wave_message_until
        ):
            return

        if (
            self.wave
            % BOSS_WAVE_INTERVAL
            == 0
        ):
            text = (
                f"BOSS WAVE {self.wave}"
            )

            colour = RED

        else:
            text = (
                f"WAVE {self.wave}"
            )

            colour = LIGHT_BLUE

        message_panel = pygame.Rect(
            GAME_WIDTH // 2 - 230,
            GAME_HEIGHT // 2 - 70,
            460,
            140,
        )

        message_surface = pygame.Surface(
            message_panel.size,
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            message_surface,
            (5, 10, 28, 205),
            message_surface.get_rect(),
            border_radius=18,
        )

        pygame.draw.rect(
            message_surface,
            (
                colour[0],
                colour[1],
                colour[2],
                230,
            ),
            message_surface.get_rect(),
            width=3,
            border_radius=18,
        )

        self.screen.blit(
            message_surface,
            message_panel.topleft,
        )

        draw_text(
            self.screen,
            text,
            self.title_font,
            colour,
            GAME_WIDTH // 2,
            GAME_HEIGHT // 2,
            center=True,
        )

    async def run(self):
        while self.running:
            self.clock.tick(FPS)

            current_time = (
                pygame.time.get_ticks()
            )

            self.update_online_leaderboard_tasks()
            self.update_buttons()

            for event in pygame.event.get():
                self.handle_event(event)

            if self.state == "playing":
                self.update_playing(
                    current_time
                )

            else:
                for star in self.stars:
                    star.update()

                for cloud in self.nebula_clouds:
                    cloud.update()

                self.update_particles()

            self.draw_background()

            if self.state == "name_entry":
                self.draw_name_entry(
                    current_time
                )

            elif self.state == "menu":
                self.draw_menu()

            elif self.state in (
                "playing",
                "paused",
            ):
                self.draw_game_objects(
                    current_time
                )

                self.draw_hud(
                    current_time
                )

                self.draw_wave_message(
                    current_time
                )

                if self.state == "paused":
                    self.draw_pause()

            elif self.state == "game_over":
                self.draw_game_over()

            elif self.state == "leaderboard":
                self.draw_leaderboard()

            elif self.state == "instructions":
                self.draw_instructions()

            pygame.display.flip()

            await asyncio.sleep(0)

        pygame.quit()


async def main():
    game = SpaceShooterGame()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())