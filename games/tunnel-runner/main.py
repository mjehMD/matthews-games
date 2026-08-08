from __future__ import annotations

import asyncio
import gc
import math
import random
import sys
from typing import Any

import pygame

from config import (
    ALLOW_FULLSCREEN,
    ALLOW_RESIZING,
    BACKGROUND_COLOUR,
    BLACK,
    BUTTON_CORNER_RADIUS,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
    CAMERA_SHAKE_AMOUNT,
    CAMERA_SHAKE_DURATION,
    CYAN,
    FPS,
    GAME_CENTER_X,
    GAME_CENTER_Y,
    GAME_HEIGHT,
    GAME_TITLE,
    GAME_WIDTH,
    GREEN,
    GREY,
    HEADING_FONT_SIZE,
    HUD_HEIGHT,
    HUD_MARGIN,
    HUD_WIDTH,
    LARGE_FONT_SIZE,
    LETTERBOX_COLOUR,
    LIGHT_BLUE,
    LIGHT_GREY,
    MAX_LEADERBOARD_ENTRIES,
    MODE_ENDLESS,
    MODE_LEVELS,
    NORMAL_FONT_SIZE,
    ORANGE,
    PANEL_ALPHA,
    PANEL_CORNER_RADIUS,
    PLAYER_MAX_ROTATION_SPEED,
    PLAYER_ROTATION_ACCELERATION,
    PLAYER_ROTATION_DECELERATION,
    PLAYER_START_ANGLE,
    PURPLE,
    RED,
    SHOW_DISTANCE,
    SHOW_LEVEL,
    SHOW_SPEED,
    SMALL_FONT_SIZE,
    START_FULLSCREEN,
    STATE_ACHIEVEMENTS,
    STATE_GAME_OVER,
    STATE_HELP,
    STATE_LEADERBOARD,
    STATE_LEVEL_COMPLETE,
    STATE_LEVEL_SELECT,
    STATE_LOADING,
    STATE_MAIN_MENU,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_SETTINGS,
    STATE_SIGN_IN_REQUIRED,
    STATE_STATISTICS,
    TINY_FONT_SIZE,
    TOTAL_LEVELS,
    TUNNEL_RADIUS,
    TUNNEL_SECTION_LENGTH,
    TUNNEL_SEGMENTS,
    TUNNEL_VISIBLE_LENGTH,
    VERSION_FONT_SIZE,
    WHITE,
    WINDOW_TITLE,
    YELLOW,
    clamp,
    format_distance,
    format_version,
    get_theme,
)

from geometry import (
    Camera3D,
    Mesh3D,
    SceneRenderer3D,
    Vec2,
    Vec3,
    create_tunnel_section_mesh,
)

from obstacles import (
    ObstacleManager,
)

from levels import (
    EndlessGenerator,
    campaign_speed_at_distance,
    endless_speed_at_distance,
    generate_campaign_level,
    get_level,
    get_next_level,
    level_completion_percentage,
    prepare_endless,
)

from storage import (
    StorageManager,
    achievement_is_hidden,
    format_level_time,
    format_play_time,
    get_achievement_description,
    get_achievement_name,
)

from player_session import (
    PlayerSessionManager,
)

from online_leaderboard import (
    format_leaderboard_distance,
    get_player_rank,
    keep_best_score_per_user,
    leaderboard_entry_distance,
    leaderboard_entry_name,
    load_global_leaderboard,
    load_personal_best,
    submit_endless_distance,
)


# ============================================================
# TUNNEL RUNNER
# MAIN
# VERSION 0.1.3
# PERFORMANCE BUILD
# ============================================================


IS_WEB = sys.platform in (
    "emscripten",
    "wasi",
)


# ============================================================
# PERFORMANCE
# ============================================================

TARGET_FPS = 60

# Only the 3D world is rendered smaller.
# Text/HUD/menu stay full resolution.

WORLD_SCALE_HIGH = 0.66
WORLD_SCALE_MEDIUM = 0.56
WORLD_SCALE_LOW = 0.48

AUTO_QUALITY = True

FPS_CHECK_SECONDS = 2.0

FPS_DROP_THRESHOLD = 56.0
FPS_RECOVER_THRESHOLD = 59.0

QUALITY_RECOVER_SECONDS = 8.0


# Tunnel detail.

PERFORMANCE_TUNNEL_SEGMENTS = max(
    10,
    min(
        TUNNEL_SEGMENTS,
        10,
    ),
)

PERFORMANCE_TUNNEL_SECTION_LENGTH = max(
    9.0,
    TUNNEL_SECTION_LENGTH,
)

TUNNEL_RENDER_DISTANCE = (
    TUNNEL_VISIBLE_LENGTH
    * 0.68
)

OBSTACLE_RENDER_DISTANCE = (
    TUNNEL_VISIBLE_LENGTH
    * 0.70
)

TUNNEL_CACHE_REMOVE_BEHIND = 16.0

TUNNEL_CACHE_EXTRA_AHEAD = 18.0

TUNNEL_CACHE_MAX_CHUNKS = 32


# ============================================================
# DRAW HELPERS
# ============================================================

def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    colour: tuple[int, int, int],
    x: int,
    y: int,
    *,
    center: bool = False,
    right: bool = False,
) -> pygame.Rect:

    image = font.render(
        str(text),
        True,
        colour,
    )

    rect = image.get_rect()

    if center:
        rect.center = (
            x,
            y,
        )

    elif right:
        rect.topright = (
            x,
            y,
        )

    else:
        rect.topleft = (
            x,
            y,
        )

    surface.blit(
        image,
        rect,
    )

    return rect


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: tuple[int, int, int] = (
        8,
        12,
        28,
    ),
    border: tuple[int, int, int] = CYAN,
    alpha: int = PANEL_ALPHA,
    width: int = 2,
) -> None:

    panel = pygame.Surface(
        rect.size,
        pygame.SRCALPHA,
    )

    pygame.draw.rect(
        panel,
        (
            fill[0],
            fill[1],
            fill[2],
            alpha,
        ),
        panel.get_rect(),
        border_radius=PANEL_CORNER_RADIUS,
    )

    pygame.draw.rect(
        panel,
        (
            border[0],
            border[1],
            border[2],
            255,
        ),
        panel.get_rect(),
        width=width,
        border_radius=PANEL_CORNER_RADIUS,
    )

    surface.blit(
        panel,
        rect.topleft,
    )


def draw_progress_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    progress: float,
    *,
    colour: tuple[int, int, int] = CYAN,
) -> None:

    progress = clamp(
        progress,
        0.0,
        1.0,
    )

    pygame.draw.rect(
        surface,
        (
            20,
            24,
            36,
        ),
        rect,
        border_radius=8,
    )

    inner = rect.inflate(
        -4,
        -4,
    )

    if progress > 0.0:

        filled = inner.copy()

        filled.width = max(
            1,
            round(
                inner.width
                * progress
            ),
        )

        pygame.draw.rect(
            surface,
            colour,
            filled,
            border_radius=6,
        )

    pygame.draw.rect(
        surface,
        LIGHT_GREY,
        rect,
        width=2,
        border_radius=8,
    )


# ============================================================
# BUTTON
# ============================================================

class Button:

    def __init__(
        self,
        rect,
        text: str,
        font: pygame.font.Font,
        *,
        accent=CYAN,
        enabled=True,
    ):

        self.rect = pygame.Rect(
            rect
        )

        self.text = text

        self.font = font

        self.accent = accent

        self.enabled = enabled

        self.hovered = False

    def update(
        self,
        mouse_position,
    ):

        self.hovered = (
            self.enabled
            and self.rect.collidepoint(
                mouse_position
            )
        )

    def clicked(
        self,
        event,
    ):

        return (
            self.enabled
            and event.type
            == pygame.MOUSEBUTTONDOWN
            and getattr(
                event,
                "button",
                0,
            )
            == 1
            and self.rect.collidepoint(
                event.pos
            )
        )

    def draw(
        self,
        surface,
    ):

        if not self.enabled:

            fill = (
                25,
                28,
                42,
            )

            border = (
                65,
                70,
                90,
            )

            text_colour = (
                100,
                108,
                125,
            )

        elif self.hovered:

            fill = self.accent
            border = WHITE
            text_colour = BLACK

        else:

            fill = (
                12,
                24,
                52,
            )

            border = self.accent
            text_colour = WHITE

        pygame.draw.rect(
            surface,
            BLACK,
            self.rect.move(
                0,
                5,
            ),
            border_radius=BUTTON_CORNER_RADIUS,
        )

        pygame.draw.rect(
            surface,
            fill,
            self.rect,
            border_radius=BUTTON_CORNER_RADIUS,
        )

        pygame.draw.rect(
            surface,
            border,
            self.rect,
            width=2,
            border_radius=BUTTON_CORNER_RADIUS,
        )

        draw_text(
            surface,
            self.font,
            self.text,
            text_colour,
            self.rect.centerx,
            self.rect.centery,
            center=True,
        )


# ============================================================
# CRASH PARTICLE
# ============================================================

class CrashParticle:

    def __init__(
        self,
        position: Vec2,
    ):

        angle = random.uniform(
            0.0,
            math.tau,
        )

        speed = random.uniform(
            80.0,
            300.0,
        )

        self.position = (
            position.copy()
        )

        self.velocity = Vec2(
            math.cos(
                angle
            )
            * speed,

            math.sin(
                angle
            )
            * speed,
        )

        self.life = random.uniform(
            0.3,
            0.7,
        )

        self.maximum_life = (
            self.life
        )

        self.radius = random.randint(
            2,
            4,
        )

    def update(
        self,
        delta_time,
    ):

        self.life -= delta_time

        self.position += (
            self.velocity
            * delta_time
        )

        self.velocity *= max(
            0.0,
            1.0
            - 2.4
            * delta_time,
        )

    @property
    def alive(
        self,
    ):

        return (
            self.life
            > 0.0
        )


# ============================================================
# TUNNEL CACHE
# ============================================================

class TunnelCacheChunk:

    def __init__(
        self,
        start_z: float,
        end_z: float,
        mesh: Mesh3D,
    ):

        self.start_z = start_z
        self.end_z = end_z
        self.mesh = mesh


class TunnelMeshCache:

    def __init__(
        self,
    ):

        self.chunks: list[
            TunnelCacheChunk
        ] = []

        self.next_z = 0.0

        self.theme_name = ""

    def clear(
        self,
    ):

        self.chunks.clear()

        self.next_z = 0.0

        self.theme_name = ""

    def reset(
        self,
        camera_z,
        theme_name,
    ):

        self.chunks.clear()

        self.theme_name = (
            theme_name
        )

        section = (
            PERFORMANCE_TUNNEL_SECTION_LENGTH
        )

        self.next_z = max(
            0.0,

            math.floor(
                camera_z
                / section
            )
            * section,
        )

    def _create_chunk(
        self,
        start_z,
        end_z,
        theme_name,
    ):

        theme = get_theme(
            theme_name
        )

        mesh = (
            create_tunnel_section_mesh(
                start_z,
                end_z,

                radius=TUNNEL_RADIUS,

                segments=(
                    PERFORMANCE_TUNNEL_SEGMENTS
                ),

                start_rotation=0.0,

                end_rotation=0.0,

                primary_colour=(
                    theme.tunnel_primary
                ),

                secondary_colour=(
                    theme.tunnel_secondary
                ),

                line_colour=(
                    theme.tunnel_lines
                ),

                draw_outlines=False,
            )
        )

        return TunnelCacheChunk(
            start_z,
            end_z,
            mesh,
        )

    def update(
        self,
        camera_z,
        theme_name,
    ):

        if (
            not self.chunks
            or theme_name
            != self.theme_name
        ):

            self.reset(
                camera_z,
                theme_name,
            )

        remove_before = (
            camera_z
            - TUNNEL_CACHE_REMOVE_BEHIND
        )

        self.chunks = [
            chunk

            for chunk
            in self.chunks

            if (
                chunk.end_z
                >= remove_before
            )
        ]

        target_z = (
            camera_z
            + TUNNEL_RENDER_DISTANCE
            + TUNNEL_CACHE_EXTRA_AHEAD
        )

        section = (
            PERFORMANCE_TUNNEL_SECTION_LENGTH
        )

        while (
            self.next_z
            < target_z
            and len(
                self.chunks
            )
            < TUNNEL_CACHE_MAX_CHUNKS
        ):

            start_z = (
                self.next_z
            )

            end_z = (
                start_z
                + section
            )

            self.chunks.append(
                self._create_chunk(
                    start_z,
                    end_z,
                    theme_name,
                )
            )

            self.next_z = (
                end_z
            )

    def visible_meshes(
        self,
        camera_z,
    ):

        maximum_z = (
            camera_z
            + TUNNEL_RENDER_DISTANCE
        )

        return [
            chunk.mesh

            for chunk
            in self.chunks

            if (
                chunk.end_z
                >= camera_z
                - 2.0

                and chunk.start_z
                <= maximum_z
            )
        ]


# ============================================================
# GAME
# ============================================================

class TunnelRunnerGame:

    def __init__(
        self,
    ):

        pygame.init()
        pygame.font.init()

        self.running = True

        self.storage = (
            StorageManager()
        )

        self.fullscreen = bool(
            self.storage.get_setting(
                "fullscreen",
                START_FULLSCREEN,
            )
        )

        if not ALLOW_FULLSCREEN:
            self.fullscreen = False

        self.display_surface = (
            self._create_display()
        )

        pygame.display.set_caption(
            WINDOW_TITLE
        )

        self.game_surface = (
            pygame.Surface(
                (
                    GAME_WIDTH,
                    GAME_HEIGHT,
                )
            ).convert()
        )

        self.display_scale = 1.0

        self.display_rect = pygame.Rect(
            0,
            0,
            GAME_WIDTH,
            GAME_HEIGHT,
        )

        self._recalculate_display()

        self.clock = (
            pygame.time.Clock()
        )

        # ====================================================
        # FONTS
        # ====================================================

        self.title_font = pygame.font.Font(
            None,
            88,
        )

        self.large_font = pygame.font.Font(
            None,
            LARGE_FONT_SIZE,
        )

        self.heading_font = pygame.font.Font(
            None,
            HEADING_FONT_SIZE,
        )

        self.normal_font = pygame.font.Font(
            None,
            NORMAL_FONT_SIZE,
        )

        self.small_font = pygame.font.Font(
            None,
            SMALL_FONT_SIZE,
        )

        self.tiny_font = pygame.font.Font(
            None,
            TINY_FONT_SIZE,
        )

        self.version_font = pygame.font.Font(
            None,
            VERSION_FONT_SIZE,
        )

        self.title_font.set_bold(
            True
        )

        self.heading_font.set_bold(
            True
        )

        # ====================================================
        # LOW RES 3D
        # ====================================================

        self.quality_level = 0

        self.world_scale = (
            WORLD_SCALE_HIGH
        )

        self.world_surface = None
        self.camera = None
        self.renderer = None

        self._rebuild_world_renderer(
            self.world_scale
        )

        self.tunnel_cache = (
            TunnelMeshCache()
        )

        self.obstacles = (
            ObstacleManager()
        )

        self.endless_generator = (
            EndlessGenerator()
        )

        # ====================================================
        # ACCOUNT
        # ====================================================

        self.session_manager = (
            PlayerSessionManager()
        )

        self.session_manager.begin_loading()

        # ====================================================
        # STATE
        # ====================================================

        self.state = (
            STATE_LOADING
        )

        self.game_mode = (
            MODE_LEVELS
        )

        self.selected_level_number = 1

        self.current_level = None

        self.player_angle = (
            PLAYER_START_ANGLE
        )

        self.player_rotation_velocity = 0.0

        self.current_speed = 0.0

        self.maximum_speed_this_run = 0.0

        self.run_start_z = 0.0

        self.run_start_ticks = 0

        self.run_end_ticks = 0

        self.paused_at_ticks = 0

        self.total_paused_ms = 0

        self.run_recorded = False

        self.last_run_distance = 0.0

        self.last_run_time = 0.0

        self.last_run_new_best = False

        self.last_run_new_level_time = False

        self.last_crash_obstacle = ""

        # ====================================================
        # FREEZE SCREEN
        # ====================================================

        self.frozen_game_frame = None

        # ====================================================
        # PERFORMANCE MONITOR
        # ====================================================

        self.performance_timer = 0.0

        self.performance_stable_timer = 0.0

        # ====================================================
        # PARTICLES
        # ====================================================

        self.crash_particles = []

        self.shake_time = 0.0
        self.shake_strength = 0.0

        # ====================================================
        # ONLINE
        # ====================================================

        self.online_personal_best = 0

        self.leaderboard = []

        self.leaderboard_message = (
            "Leaderboard not loaded."
        )

        self.submit_message = ""

        self.personal_best_task = None
        self.leaderboard_task = None
        self.submit_task = None

        # ====================================================
        # ACHIEVEMENTS
        # ====================================================

        self.achievement_queue = []

        self.current_achievement = ""

        self.achievement_started = 0

        # ====================================================
        # MENU
        # ====================================================

        self.level_page = 0

        self.menu_time = 0.0

        self.menu_stars = [
            (
                random.uniform(
                    0,
                    GAME_WIDTH,
                ),

                random.uniform(
                    0,
                    GAME_HEIGHT,
                ),

                random.uniform(
                    8,
                    32,
                ),

                random.choice(
                    (
                        1,
                        1,
                        1,
                        2,
                    )
                ),
            )

            for _ in range(
                90
            )
        ]

        self._build_buttons()

        # We control garbage collection ourselves at safe times.

        gc.collect()
        gc.disable()

    # ========================================================
    # WORLD RENDERER
    # ========================================================

    def _rebuild_world_renderer(
        self,
        scale,
    ):

        old_position = (
            self.camera.position
            if self.camera
            else Vec3()
        )

        old_rotation = (
            self.camera.rotation
            if self.camera
            else Vec3()
        )

        width = max(
            480,
            int(
                GAME_WIDTH
                * scale
            ),
        )

        height = max(
            270,
            int(
                GAME_HEIGHT
                * scale
            ),
        )

        self.world_scale = (
            scale
        )

        self.world_surface = (
            pygame.Surface(
                (
                    width,
                    height,
                )
            ).convert()
        )

        self.camera = Camera3D(
            width=width,
            height=height,
        )

        self.camera.position = (
            old_position
        )

        self.camera.rotation = (
            old_rotation
        )

        self.renderer = (
            SceneRenderer3D(
                self.camera
            )
        )

    # ========================================================
    # AUTO QUALITY
    # ========================================================

    def update_auto_quality(
        self,
        delta_time,
    ):

        if not AUTO_QUALITY:
            return

        if (
            self.state
            != STATE_PLAYING
        ):
            return

        self.performance_timer += (
            delta_time
        )

        self.performance_stable_timer += (
            delta_time
        )

        if (
            self.performance_timer
            < FPS_CHECK_SECONDS
        ):
            return

        self.performance_timer = 0.0

        fps = (
            self.clock.get_fps()
        )

        if fps <= 1:
            return

        if (
            fps
            < FPS_DROP_THRESHOLD
        ):

            self.performance_stable_timer = 0.0

            if (
                self.quality_level
                == 0
            ):

                self.quality_level = 1

                self._rebuild_world_renderer(
                    WORLD_SCALE_MEDIUM
                )

            elif (
                self.quality_level
                == 1
            ):

                self.quality_level = 2

                self._rebuild_world_renderer(
                    WORLD_SCALE_LOW
                )

            return

        if (
            fps
            >= FPS_RECOVER_THRESHOLD
            and self.performance_stable_timer
            >= QUALITY_RECOVER_SECONDS
        ):

            if (
                self.quality_level
                == 2
            ):

                self.quality_level = 1

                self._rebuild_world_renderer(
                    WORLD_SCALE_MEDIUM
                )

                self.performance_stable_timer = 0.0

            elif (
                self.quality_level
                == 1
            ):

                self.quality_level = 0

                self._rebuild_world_renderer(
                    WORLD_SCALE_HIGH
                )

                self.performance_stable_timer = 0.0

    # ========================================================
    # DISPLAY
    # ========================================================

    def _create_display(
        self,
    ):

        if (
            self.fullscreen
            and ALLOW_FULLSCREEN
        ):

            info = pygame.display.Info()

            return pygame.display.set_mode(
                (
                    max(
                        GAME_WIDTH,
                        info.current_w,
                    ),

                    max(
                        GAME_HEIGHT,
                        info.current_h,
                    ),
                ),

                pygame.FULLSCREEN,
            )

        return pygame.display.set_mode(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),

            pygame.RESIZABLE
            if ALLOW_RESIZING
            else 0,
        )

    def _recalculate_display(
        self,
    ):

        width = max(
            1,
            self.display_surface.get_width(),
        )

        height = max(
            1,
            self.display_surface.get_height(),
        )

        scale = min(
            width
            / GAME_WIDTH,

            height
            / GAME_HEIGHT,
        )

        self.display_scale = max(
            0.05,
            scale,
        )

        scaled_width = max(
            1,
            round(
                GAME_WIDTH
                * self.display_scale
            ),
        )

        scaled_height = max(
            1,
            round(
                GAME_HEIGHT
                * self.display_scale
            ),
        )

        self.display_rect = pygame.Rect(
            (
                width
                - scaled_width
            )
            // 2,

            (
                height
                - scaled_height
            )
            // 2,

            scaled_width,

            scaled_height,
        )

    def display_to_game(
        self,
        position,
    ):

        if not self.display_rect.collidepoint(
            position
        ):

            return (
                -10000,
                -10000,
            )

        return (
            round(
                (
                    position[0]
                    - self.display_rect.x
                )
                / self.display_scale
            ),

            round(
                (
                    position[1]
                    - self.display_rect.y
                )
                / self.display_scale
            ),
        )

    def _convert_event(
        self,
        event,
    ):

        if not hasattr(
            event,
            "pos",
        ):
            return event

        data = dict(
            event.dict
        )

        data["pos"] = (
            self.display_to_game(
                event.pos
            )
        )

        return pygame.event.Event(
            event.type,
            data,
        )

    def toggle_fullscreen(
        self,
    ):

        if not ALLOW_FULLSCREEN:
            return

        self.fullscreen = (
            not self.fullscreen
        )

        self.storage.set_setting(
            "fullscreen",
            self.fullscreen,
        )

        self.display_surface = (
            self._create_display()
        )

        self._recalculate_display()

    def present(
        self,
    ):

        self.display_surface.fill(
            LETTERBOX_COLOUR
        )

        if (
            self.display_rect.size
            == (
                GAME_WIDTH,
                GAME_HEIGHT,
            )
        ):

            frame = (
                self.game_surface
            )

        else:

            # Normal scale is much cheaper than smoothscale.

            frame = pygame.transform.scale(
                self.game_surface,
                self.display_rect.size,
            )

        self.display_surface.blit(
            frame,
            self.display_rect.topleft,
        )

        pygame.display.flip()

    # ========================================================
    # BUTTONS
    # ========================================================

    def _build_buttons(
        self,
    ):

        x = (
            GAME_WIDTH
            // 2
            - BUTTON_WIDTH
            // 2
        )

        self.levels_button = Button(
            (
                x,
                310,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
            ),
            "50 LEVELS",
            self.normal_font,
            accent=LIGHT_BLUE,
        )

        self.endless_button = Button(
            (
                x,
                400,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
            ),
            "ENDLESS",
            self.normal_font,
            accent=CYAN,
        )

        self.leaderboard_button = Button(
            (
                x,
                490,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
            ),
            "LEADERBOARD",
            self.normal_font,
            accent=YELLOW,
        )

        self.settings_button = Button(
            (
                30,
                GAME_HEIGHT - 65,
                170,
                42,
            ),
            "SETTINGS",
            self.small_font,
            accent=PURPLE,
        )

        self.stats_button = Button(
            (
                215,
                GAME_HEIGHT - 65,
                170,
                42,
            ),
            "STATISTICS",
            self.small_font,
            accent=GREEN,
        )

        self.achievements_button = Button(
            (
                400,
                GAME_HEIGHT - 65,
                205,
                42,
            ),
            "ACHIEVEMENTS",
            self.small_font,
            accent=ORANGE,
        )

        self.help_button = Button(
            (
                GAME_WIDTH - 200,
                GAME_HEIGHT - 65,
                170,
                42,
            ),
            "HELP",
            self.small_font,
            accent=LIGHT_BLUE,
        )

        self.back_button = Button(
            (
                25,
                25,
                145,
                44,
            ),
            "BACK",
            self.small_font,
            accent=LIGHT_BLUE,
        )

        self.pause_resume_button = Button(
            (
                GAME_CENTER_X - 170,
                310,
                340,
                60,
            ),
            "RESUME",
            self.normal_font,
            accent=GREEN,
        )

        self.pause_restart_button = Button(
            (
                GAME_CENTER_X - 170,
                390,
                340,
                60,
            ),
            "RESTART",
            self.normal_font,
            accent=YELLOW,
        )

        self.pause_menu_button = Button(
            (
                GAME_CENTER_X - 170,
                470,
                340,
                60,
            ),
            "MAIN MENU",
            self.normal_font,
            accent=RED,
        )

        self.retry_button = Button(
            (
                GAME_CENTER_X - 170,
                475,
                340,
                60,
            ),
            "TRY AGAIN",
            self.normal_font,
            accent=CYAN,
        )

        self.game_over_menu_button = Button(
            (
                GAME_CENTER_X - 170,
                550,
                340,
                60,
            ),
            "MAIN MENU",
            self.normal_font,
            accent=LIGHT_BLUE,
        )

        self.next_level_button = Button(
            (
                GAME_CENTER_X - 170,
                475,
                340,
                60,
            ),
            "NEXT LEVEL",
            self.normal_font,
            accent=GREEN,
        )

        self.level_select_button = Button(
            (
                GAME_CENTER_X - 170,
                550,
                340,
                60,
            ),
            "LEVEL SELECT",
            self.normal_font,
            accent=LIGHT_BLUE,
        )

    def _level_buttons(
        self,
    ):

        buttons = []

        start = (
            self.level_page
            * 10
            + 1
        )

        end = min(
            TOTAL_LEVELS,
            start + 9,
        )

        for index, level_number in enumerate(
            range(
                start,
                end + 1,
            )
        ):

            column = (
                index
                % 5
            )

            row = (
                index
                // 5
            )

            button = Button(
                (
                    150
                    + column
                    * 200,

                    255
                    + row
                    * 160,

                    160,

                    92,
                ),

                str(
                    level_number
                ),

                self.heading_font,

                accent=(
                    GREEN

                    if self.storage.is_level_completed(
                        level_number
                    )

                    else CYAN
                ),

                enabled=(
                    self.storage.is_level_unlocked(
                        level_number
                    )
                ),
            )

            buttons.append(
                (
                    level_number,
                    button,
                )
            )

        return buttons

    def _visible_buttons(
        self,
    ):

        if (
            self.state
            == STATE_MAIN_MENU
        ):

            return [
                self.levels_button,
                self.endless_button,
                self.leaderboard_button,
                self.settings_button,
                self.stats_button,
                self.achievements_button,
                self.help_button,
            ]

        if (
            self.state
            == STATE_LEVEL_SELECT
        ):

            return [
                self.back_button,

                *[
                    button

                    for _level, button
                    in self._level_buttons()
                ],
            ]

        if (
            self.state
            == STATE_PAUSED
        ):

            return [
                self.pause_resume_button,
                self.pause_restart_button,
                self.pause_menu_button,
            ]

        if (
            self.state
            == STATE_GAME_OVER
        ):

            return [
                self.retry_button,
                self.game_over_menu_button,
            ]

        if (
            self.state
            == STATE_LEVEL_COMPLETE
        ):

            return [
                self.next_level_button,
                self.level_select_button,
            ]

        if self.state in (
            STATE_LEADERBOARD,
            STATE_SETTINGS,
            STATE_HELP,
            STATE_STATISTICS,
            STATE_ACHIEVEMENTS,
        ):

            return [
                self.back_button
            ]

        return []

    def update_button_hovers(
        self,
    ):

        mouse = self.display_to_game(
            pygame.mouse.get_pos()
        )

        for button in (
            self._visible_buttons()
        ):

            button.update(
                mouse
            )

    # ========================================================
    # ACCOUNT
    # ========================================================

    def update_session(
        self,
    ):

        if not self.session_manager.update():
            return

        if (
            self.session_manager.signed_in
        ):

            self.state = (
                STATE_MAIN_MENU
            )

            self.start_personal_best_load()

            self.start_leaderboard_load()

        else:

            self.state = (
                STATE_SIGN_IN_REQUIRED
            )

    # ========================================================
    # ONLINE
    # ========================================================

    def start_personal_best_load(
        self,
    ):

        if not self.session_manager.signed_in:
            return

        if self.session_manager.desktop_test_account:
            return

        if (
            self.personal_best_task
            and not self.personal_best_task.done()
        ):
            return

        self.personal_best_task = asyncio.create_task(
            load_personal_best(
                self.session_manager.user_id,
                self.session_manager.access_token,
            )
        )

    def start_leaderboard_load(
        self,
    ):

        if (
            self.leaderboard_task
            and not self.leaderboard_task.done()
        ):
            return

        self.leaderboard_message = (
            "Loading leaderboard..."
        )

        self.leaderboard_task = asyncio.create_task(
            load_global_leaderboard()
        )

    def submit_endless_score(
        self,
        distance,
    ):

        if not self.session_manager.signed_in:
            return

        if self.session_manager.desktop_test_account:

            self.submit_message = (
                "Desktop test scores are not uploaded."
            )

            return

        if (
            self.submit_task
            and not self.submit_task.done()
        ):
            return

        self.submit_message = (
            "Saving score..."
        )

        self.submit_task = asyncio.create_task(
            submit_endless_distance(
                self.session_manager.username,
                distance,
                self.session_manager.user_id,
                self.session_manager.access_token,
            )
        )

    def update_online_tasks(
        self,
    ):

        if (
            self.personal_best_task
            and self.personal_best_task.done()
        ):

            try:

                distance, _message = (
                    self.personal_best_task.result()
                )

                self.online_personal_best = max(
                    0,
                    int(
                        distance
                    ),
                )

            except Exception:
                pass

            self.personal_best_task = None

        if (
            self.leaderboard_task
            and self.leaderboard_task.done()
        ):

            try:

                entries, message = (
                    self.leaderboard_task.result()
                )

                self.leaderboard = (
                    keep_best_score_per_user(
                        entries
                    )
                )

                self.leaderboard_message = (
                    message
                )

            except Exception as error:

                self.leaderboard = []

                self.leaderboard_message = (
                    f"Leaderboard error: {error}"
                )

            self.leaderboard_task = None

        if (
            self.submit_task
            and self.submit_task.done()
        ):

            try:

                (
                    success,
                    message,
                    stored_best,
                    new_best,
                ) = self.submit_task.result()

                self.submit_message = (
                    message
                )

                if success:

                    self.online_personal_best = max(
                        self.online_personal_best,
                        stored_best,
                    )

                    self.last_run_new_best = (
                        self.last_run_new_best
                        or new_best
                    )

                    self.start_leaderboard_load()

            except Exception as error:

                self.submit_message = (
                    f"Score error: {error}"
                )

            self.submit_task = None

    @property
    def displayed_personal_best(
        self,
    ):

        return max(
            self.storage.endless_best_distance,
            self.online_personal_best,
        )

    # ========================================================
    # RUN
    # ========================================================

    def reset_run_state(
        self,
    ):

        self.camera.position = Vec3(
            0,
            0,
            0,
        )

        self.camera.rotation = Vec3(
            0,
            0,
            PLAYER_START_ANGLE,
        )

        self.camera.shake_offset = Vec2()

        self.player_angle = (
            PLAYER_START_ANGLE
        )

        self.player_rotation_velocity = 0.0

        self.maximum_speed_this_run = 0.0

        self.run_start_z = 0.0

        self.run_start_ticks = (
            pygame.time.get_ticks()
        )

        self.run_end_ticks = 0

        self.paused_at_ticks = 0

        self.total_paused_ms = 0

        self.run_recorded = False

        self.last_run_distance = 0.0

        self.last_run_time = 0.0

        self.last_run_new_best = False

        self.last_run_new_level_time = False

        self.last_crash_obstacle = ""

        self.frozen_game_frame = None

        self.crash_particles.clear()

        self.shake_time = 0.0

        self.tunnel_cache.clear()

        self.performance_timer = 0.0

        self.performance_stable_timer = 0.0

    def start_level(
        self,
        level_number,
    ):

        if not self.storage.is_level_unlocked(
            level_number
        ):
            return

        generated = (
            generate_campaign_level(
                level_number
            )
        )

        self.obstacles.clear()

        self.obstacles.extend(
            generated.obstacles
        )

        self.game_mode = (
            MODE_LEVELS
        )

        self.selected_level_number = (
            level_number
        )

        self.current_level = (
            generated.definition
        )

        self.reset_run_state()

        self.player_angle = (
            generated.starting_angle
        )

        self.camera.rotation.z = (
            self.player_angle
        )

        self.current_speed = (
            self.current_level.speed
        )

        self.storage.record_level_start(
            level_number
        )

        gc.enable()
        gc.collect()
        gc.disable()

        self.state = (
            STATE_PLAYING
        )

    def start_endless(
        self,
    ):

        self.game_mode = (
            MODE_ENDLESS
        )

        self.current_level = None

        self.reset_run_state()

        prepare_endless(
            self.obstacles,
            self.endless_generator,
        )

        self.current_speed = (
            endless_speed_at_distance(
                0
            )
        )

        self.storage.record_endless_start()

        gc.enable()
        gc.collect()
        gc.disable()

        self.state = (
            STATE_PLAYING
        )

    def restart_current_run(
        self,
    ):

        if (
            self.game_mode
            == MODE_LEVELS
        ):

            self.start_level(
                self.selected_level_number
            )

        else:

            self.start_endless()

    @property
    def run_distance(
        self,
    ):

        return max(
            0.0,

            self.camera.position.z
            - self.run_start_z,
        )

    def run_time_seconds(
        self,
    ):

        end = (
            self.run_end_ticks

            if self.run_end_ticks

            else pygame.time.get_ticks()
        )

        milliseconds = max(
            0,

            end
            - self.run_start_ticks
            - self.total_paused_ms,
        )

        return (
            milliseconds
            / 1000
        )

    # ========================================================
    # CRASH / COMPLETE
    # ========================================================

    def trigger_crash(
        self,
        obstacle_type,
    ):

        if self.run_recorded:
            return

        self.frozen_game_frame = (
            self.game_surface.copy()
        )

        self.run_recorded = True

        self.run_end_ticks = (
            pygame.time.get_ticks()
        )

        self.last_run_distance = (
            self.run_distance
        )

        self.last_run_time = (
            self.run_time_seconds()
        )

        self.last_crash_obstacle = (
            obstacle_type
        )

        if (
            self.game_mode
            == MODE_ENDLESS
        ):

            _best, new_best = (
                self.storage.record_endless_run(
                    distance=(
                        self.last_run_distance
                    ),

                    play_time_seconds=(
                        self.last_run_time
                    ),

                    maximum_speed=(
                        self.maximum_speed_this_run
                    ),
                )
            )

            self.last_run_new_best = (
                new_best
            )

            self.submit_endless_score(
                self.last_run_distance
            )

        else:

            self.storage.record_level_crash(
                self.selected_level_number,

                distance=(
                    self.last_run_distance
                ),

                play_time_seconds=(
                    self.last_run_time
                ),

                maximum_speed=(
                    self.maximum_speed_this_run
                ),
            )

        self._collect_achievements()

        self._spawn_crash_particles()

        self.state = (
            STATE_GAME_OVER
        )

    def trigger_level_complete(
        self,
    ):

        if (
            self.run_recorded
            or self.current_level
            is None
        ):
            return

        self.frozen_game_frame = (
            self.game_surface.copy()
        )

        self.run_recorded = True

        self.run_end_ticks = (
            pygame.time.get_ticks()
        )

        self.last_run_distance = (
            self.current_level.length
        )

        self.last_run_time = (
            self.run_time_seconds()
        )

        _first, new_best = (
            self.storage.record_level_completion(
                self.selected_level_number,

                distance=(
                    self.last_run_distance
                ),

                play_time_seconds=(
                    self.last_run_time
                ),

                maximum_speed=(
                    self.maximum_speed_this_run
                ),
            )
        )

        self.last_run_new_level_time = (
            new_best
        )

        self._collect_achievements()

        self.state = (
            STATE_LEVEL_COMPLETE
        )

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    def _collect_achievements(
        self,
    ):

        for achievement in (
            self.storage.consume_new_achievements()
        ):

            if (
                achievement
                not in self.achievement_queue
            ):

                self.achievement_queue.append(
                    achievement
                )

    def update_achievement_popup(
        self,
        current_time,
    ):

        if (
            not self.current_achievement
            and self.achievement_queue
        ):

            self.current_achievement = (
                self.achievement_queue.pop(
                    0
                )
            )

            self.achievement_started = (
                current_time
            )

        if (
            self.current_achievement
            and current_time
            - self.achievement_started
            > 3200
        ):

            self.current_achievement = ""

    # ========================================================
    # EVENTS
    # ========================================================

    def handle_event(
        self,
        raw_event,
    ):

        event = self._convert_event(
            raw_event
        )

        if (
            event.type
            == pygame.QUIT
        ):

            self.running = False
            return

        if (
            event.type
            == pygame.VIDEORESIZE
            and not self.fullscreen
            and ALLOW_RESIZING
        ):

            self.display_surface = (
                pygame.display.set_mode(
                    event.size,
                    pygame.RESIZABLE,
                )
            )

            self._recalculate_display()

            return

        if (
            event.type
            == pygame.KEYDOWN
        ):

            if (
                event.key
                == pygame.K_F11
            ):

                self.toggle_fullscreen()
                return

            if (
                event.key
                == pygame.K_ESCAPE
            ):

                if (
                    self.state
                    == STATE_PLAYING
                ):

                    self.frozen_game_frame = (
                        self.game_surface.copy()
                    )

                    self.paused_at_ticks = (
                        pygame.time.get_ticks()
                    )

                    self.state = (
                        STATE_PAUSED
                    )

                    return

                if (
                    self.state
                    == STATE_PAUSED
                ):

                    self.total_paused_ms += (
                        pygame.time.get_ticks()
                        - self.paused_at_ticks
                    )

                    self.paused_at_ticks = 0

                    self.frozen_game_frame = None

                    self.state = (
                        STATE_PLAYING
                    )

                    return

                if self.state in (
                    STATE_LEVEL_SELECT,
                    STATE_LEADERBOARD,
                    STATE_SETTINGS,
                    STATE_HELP,
                    STATE_STATISTICS,
                    STATE_ACHIEVEMENTS,
                ):

                    self.state = (
                        STATE_MAIN_MENU
                    )

                    return

        if self.state in (
            STATE_LOADING,
            STATE_SIGN_IN_REQUIRED,
        ):
            return

        if (
            self.state
            == STATE_MAIN_MENU
        ):

            if self.levels_button.clicked(
                event
            ):

                self.state = (
                    STATE_LEVEL_SELECT
                )

            elif self.endless_button.clicked(
                event
            ):

                self.start_endless()

            elif self.leaderboard_button.clicked(
                event
            ):

                self.state = (
                    STATE_LEADERBOARD
                )

                self.start_leaderboard_load()

            elif self.settings_button.clicked(
                event
            ):

                self.state = (
                    STATE_SETTINGS
                )

            elif self.stats_button.clicked(
                event
            ):

                self.state = (
                    STATE_STATISTICS
                )

            elif self.achievements_button.clicked(
                event
            ):

                self.state = (
                    STATE_ACHIEVEMENTS
                )

            elif self.help_button.clicked(
                event
            ):

                self.state = (
                    STATE_HELP
                )

        elif (
            self.state
            == STATE_LEVEL_SELECT
        ):

            if self.back_button.clicked(
                event
            ):

                self.state = (
                    STATE_MAIN_MENU
                )

                return

            if (
                event.type
                == pygame.KEYDOWN
            ):

                if event.key in (
                    pygame.K_LEFT,
                    pygame.K_PAGEUP,
                ):

                    self.level_page = max(
                        0,
                        self.level_page - 1,
                    )

                elif event.key in (
                    pygame.K_RIGHT,
                    pygame.K_PAGEDOWN,
                ):

                    self.level_page = min(
                        4,
                        self.level_page + 1,
                    )

            for level, button in (
                self._level_buttons()
            ):

                if button.clicked(
                    event
                ):

                    self.start_level(
                        level
                    )

                    return

        elif (
            self.state
            == STATE_PAUSED
        ):

            if self.pause_resume_button.clicked(
                event
            ):

                self.total_paused_ms += (
                    pygame.time.get_ticks()
                    - self.paused_at_ticks
                )

                self.paused_at_ticks = 0

                self.frozen_game_frame = None

                self.state = (
                    STATE_PLAYING
                )

            elif self.pause_restart_button.clicked(
                event
            ):

                self.restart_current_run()

            elif self.pause_menu_button.clicked(
                event
            ):

                self.state = (
                    STATE_MAIN_MENU
                )

        elif (
            self.state
            == STATE_GAME_OVER
        ):

            if self.retry_button.clicked(
                event
            ):

                self.restart_current_run()

            elif self.game_over_menu_button.clicked(
                event
            ):

                self.state = (
                    STATE_MAIN_MENU
                )

        elif (
            self.state
            == STATE_LEVEL_COMPLETE
        ):

            next_level = get_next_level(
                self.selected_level_number
            )

            self.next_level_button.enabled = (
                next_level
                is not None
            )

            if (
                next_level
                and self.next_level_button.clicked(
                    event
                )
            ):

                self.start_level(
                    next_level.number
                )

            elif self.level_select_button.clicked(
                event
            ):

                self.state = (
                    STATE_LEVEL_SELECT
                )

        elif (
            self.state
            == STATE_LEADERBOARD
        ):

            if self.back_button.clicked(
                event
            ):

                self.state = (
                    STATE_MAIN_MENU
                )

            elif (
                event.type
                == pygame.KEYDOWN
                and event.key
                == pygame.K_r
            ):

                self.start_leaderboard_load()

        elif (
            self.state
            == STATE_SETTINGS
        ):

            self._handle_settings_event(
                event
            )

        elif self.state in (
            STATE_HELP,
            STATE_STATISTICS,
            STATE_ACHIEVEMENTS,
        ):

            if self.back_button.clicked(
                event
            ):

                self.state = (
                    STATE_MAIN_MENU
                )

    # ========================================================
    # SETTINGS
    # ========================================================

    def _settings_rows(
        self,
    ):

        rows = (
            (
                "fullscreen",
                "Fullscreen",
            ),

            (
                "screen_shake",
                "Screen Shake",
            ),

            (
                "particles",
                "Particles",
            ),

            (
                "speed_lines",
                "Speed Lines",
            ),

            (
                "glow",
                "Glow",
            ),

            (
                "show_fps",
                "Show FPS",
            ),
        )

        return [
            (
                key,
                label,

                pygame.Rect(
                    350,
                    205
                    + index
                    * 66,
                    580,
                    50,
                ),
            )

            for index, (
                key,
                label,
            )
            in enumerate(
                rows
            )
        ]

    def _handle_settings_event(
        self,
        event,
    ):

        if self.back_button.clicked(
            event
        ):

            self.state = (
                STATE_MAIN_MENU
            )

            return

        if (
            event.type
            != pygame.MOUSEBUTTONDOWN
            or getattr(
                event,
                "button",
                0,
            )
            != 1
        ):
            return

        for key, _label, rect in (
            self._settings_rows()
        ):

            if not rect.collidepoint(
                event.pos
            ):
                continue

            if (
                key
                == "fullscreen"
            ):

                self.toggle_fullscreen()

            else:

                self.storage.toggle_setting(
                    key
                )

            return

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        delta_time,
        current_time,
    ):

        self.update_session()

        self.update_online_tasks()

        self.update_button_hovers()

        self.update_achievement_popup(
            current_time
        )

        self._update_particles(
            delta_time
        )

        self.update_auto_quality(
            delta_time
        )

        if (
            self.state
            != STATE_PLAYING
        ):

            self.camera.shake_offset = (
                Vec2()
            )

            return

        self._update_player_movement(
            delta_time
        )

        distance = (
            self.run_distance
        )

        if (
            self.game_mode
            == MODE_ENDLESS
        ):

            self.current_speed = (
                endless_speed_at_distance(
                    distance
                )
            )

            self.endless_generator.update(
                self.obstacles,
                self.camera.position.z,
            )

        else:

            self.current_speed = (
                campaign_speed_at_distance(
                    self.selected_level_number,
                    distance,
                )
            )

        self.maximum_speed_this_run = max(
            self.maximum_speed_this_run,
            self.current_speed,
        )

        self.camera.position.z += (
            self.current_speed
            * delta_time
        )

        self.camera.rotation.z = (
            self.player_angle
        )

        self.obstacles.update(
            delta_time,
            self.camera.position.z,
        )

        collision = (
            self.obstacles.check_collision(
                self.camera.position.z,
                self.player_angle,
            )
        )

        if collision:

            self.trigger_crash(
                collision.obstacle_type
            )

            return

        if (
            self.game_mode
            == MODE_LEVELS
            and self.obstacles.reached_finish(
                self.camera.position.z
            )
        ):

            self.trigger_level_complete()
            return

        self.tunnel_cache.update(
            self.camera.position.z,
            self._current_theme_name(),
        )

    # ========================================================
    # MOVEMENT
    # ========================================================

    def _update_player_movement(
        self,
        delta_time,
    ):

        keys = pygame.key.get_pressed()

        direction = 0

        if (
            keys[
                pygame.K_a
            ]
            or keys[
                pygame.K_LEFT
            ]
        ):

            direction -= 1

        if (
            keys[
                pygame.K_d
            ]
            or keys[
                pygame.K_RIGHT
            ]
        ):

            direction += 1

        if direction:

            target = (
                direction
                * PLAYER_MAX_ROTATION_SPEED
            )

            change = (
                PLAYER_ROTATION_ACCELERATION
                * delta_time
            )

            if (
                self.player_rotation_velocity
                < target
            ):

                self.player_rotation_velocity = min(
                    target,
                    self.player_rotation_velocity
                    + change,
                )

            else:

                self.player_rotation_velocity = max(
                    target,
                    self.player_rotation_velocity
                    - change,
                )

        else:

            change = (
                PLAYER_ROTATION_DECELERATION
                * delta_time
            )

            if (
                self.player_rotation_velocity
                > 0
            ):

                self.player_rotation_velocity = max(
                    0,
                    self.player_rotation_velocity
                    - change,
                )

            elif (
                self.player_rotation_velocity
                < 0
            ):

                self.player_rotation_velocity = min(
                    0,
                    self.player_rotation_velocity
                    + change,
                )

        self.player_angle = (
            self.player_angle
            + self.player_rotation_velocity
            * delta_time
        ) % 360

    # ========================================================
    # PARTICLES
    # ========================================================

    def _spawn_crash_particles(
        self,
    ):

        if not self.storage.particles_enabled:
            return

        center = Vec2(
            GAME_CENTER_X,
            GAME_CENTER_Y,
        )

        # Reduced from 55.
        for _ in range(
            28
        ):

            self.crash_particles.append(
                CrashParticle(
                    center
                )
            )

    def _update_particles(
        self,
        delta_time,
    ):

        if not self.crash_particles:
            return

        for particle in (
            self.crash_particles
        ):

            particle.update(
                delta_time
            )

        self.crash_particles = [
            particle

            for particle
            in self.crash_particles

            if particle.alive
        ]

    # ========================================================
    # THEME
    # ========================================================

    def _current_theme_name(
        self,
    ):

        if (
            self.game_mode
            == MODE_LEVELS
            and self.current_level
            is not None
        ):

            return (
                self.current_level.theme_name
            )

        distance = self.run_distance

        if distance < 1000:
            return "blue"

        if distance < 2200:
            return "cyan"

        if distance < 4000:
            return "purple"

        if distance < 6500:
            return "orange"

        if distance < 9000:
            return "red"

        return "white"

    # ========================================================
    # 3D DRAW
    # ========================================================

    def draw_3d_world(
        self,
    ):

        theme_name = (
            self._current_theme_name()
        )

        theme = get_theme(
            theme_name
        )

        self.world_surface.fill(
            theme.background
        )

        self.renderer.clear()

        self.renderer.fog_colour = (
            theme.background
        )

        self.renderer.use_lighting = (
            False
        )

        self.tunnel_cache.update(
            self.camera.position.z,
            theme_name,
        )

        self.renderer.add_meshes(
            self.tunnel_cache.visible_meshes(
                self.camera.position.z
            )
        )

        self.renderer.add_meshes(
            self.obstacles.build_visible_meshes(
                self.camera.position.z,
                OBSTACLE_RENDER_DISTANCE,
            )
        )

        self.renderer.draw(
            self.world_surface
        )

        # Cheap upscale into full resolution.

        pygame.transform.scale(
            self.world_surface,
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            self.game_surface,
        )

        self._draw_speed_lines(
            theme.glow
        )

    def _draw_speed_lines(
        self,
        colour,
    ):

        if not self.storage.speed_lines_enabled:
            return

        if self.current_speed < 34:
            return

        intensity = clamp(
            (
                self.current_speed
                - 34
            )
            / 34,
            0,
            1,
        )

        count = round(
            5
            + 10
            * intensity
        )

        for index in range(
            count
        ):

            angle = (
                index
                / count
                * math.tau
            )

            radius = (
                190
                + (
                    index
                    * 43
                    + int(
                        self.camera.position.z
                        * 4
                    )
                )
                % 270
            )

            x1 = (
                GAME_CENTER_X
                + math.cos(
                    angle
                )
                * radius
            )

            y1 = (
                GAME_CENTER_Y
                + math.sin(
                    angle
                )
                * radius
            )

            x2 = (
                GAME_CENTER_X
                + math.cos(
                    angle
                )
                * (
                    radius
                    + 24
                )
            )

            y2 = (
                GAME_CENTER_Y
                + math.sin(
                    angle
                )
                * (
                    radius
                    + 24
                )
            )

            pygame.draw.line(
                self.game_surface,
                colour,
                (
                    round(
                        x1
                    ),
                    round(
                        y1
                    ),
                ),
                (
                    round(
                        x2
                    ),
                    round(
                        y2
                    ),
                ),
                1,
            )

    # ========================================================
    # MENU BACKGROUND
    # ========================================================

    def draw_menu_background(
        self,
        delta_time,
    ):

        self.menu_time += (
            delta_time
        )

        self.game_surface.fill(
            BACKGROUND_COLOUR
        )

        for (
            x,
            y,
            speed,
            radius,
        ) in self.menu_stars:

            shifted_y = (
                y
                + self.menu_time
                * speed
            ) % GAME_HEIGHT

            pygame.draw.circle(
                self.game_surface,
                (
                    120,
                    150,
                    210,
                ),
                (
                    round(
                        x
                    ),
                    round(
                        shifted_y
                    ),
                ),
                radius,
            )

    # ========================================================
    # HUD
    # ========================================================

    def draw_hud(
        self,
    ):

        if SHOW_DISTANCE:

            draw_panel(
                self.game_surface,

                pygame.Rect(
                    HUD_MARGIN,
                    HUD_MARGIN,
                    HUD_WIDTH,
                    HUD_HEIGHT,
                ),

                border=CYAN,

                alpha=190,
            )

            draw_text(
                self.game_surface,
                self.heading_font,
                format_distance(
                    self.run_distance
                ),
                WHITE,
                HUD_MARGIN + 18,
                HUD_MARGIN + 14,
            )

            if SHOW_SPEED:

                draw_text(
                    self.game_surface,
                    self.small_font,
                    (
                        "Speed "
                        f"{self.current_speed:.1f}"
                    ),
                    LIGHT_BLUE,
                    HUD_MARGIN + 18,
                    HUD_MARGIN + 65,
                )

        rect = pygame.Rect(
            GAME_WIDTH
            - HUD_MARGIN
            - HUD_WIDTH,

            HUD_MARGIN,

            HUD_WIDTH,

            HUD_HEIGHT,
        )

        if (
            SHOW_LEVEL
            and self.game_mode
            == MODE_LEVELS
            and self.current_level
        ):

            draw_panel(
                self.game_surface,
                rect,
                border=GREEN,
                alpha=190,
            )

            draw_text(
                self.game_surface,
                self.heading_font,
                (
                    "LEVEL "
                    f"{self.selected_level_number}"
                ),
                GREEN,
                rect.right - 18,
                rect.top + 14,
                right=True,
            )

            progress = (
                level_completion_percentage(
                    self.selected_level_number,
                    self.run_distance,
                )
                / 100
            )

            draw_progress_bar(
                self.game_surface,
                pygame.Rect(
                    rect.left + 18,
                    rect.top + 70,
                    rect.width - 36,
                    15,
                ),
                progress,
                colour=GREEN,
            )

        elif (
            self.game_mode
            == MODE_ENDLESS
        ):

            draw_panel(
                self.game_surface,
                rect,
                border=YELLOW,
                alpha=190,
            )

            draw_text(
                self.game_surface,
                self.heading_font,
                "ENDLESS",
                YELLOW,
                rect.right - 18,
                rect.top + 14,
                right=True,
            )

            draw_text(
                self.game_surface,
                self.small_font,
                (
                    "Best "
                    f"{format_distance(self.displayed_personal_best)}"
                ),
                LIGHT_BLUE,
                rect.right - 18,
                rect.top + 66,
                right=True,
            )

    # ========================================================
    # DRAW MASTER
    # ========================================================

    def draw(
        self,
        current_time,
        delta_time,
    ):

        if (
            self.state
            == STATE_PLAYING
        ):

            self.draw_3d_world()

            self.draw_hud()

        elif self.state in (
            STATE_PAUSED,
            STATE_GAME_OVER,
            STATE_LEVEL_COMPLETE,
        ):

            if (
                self.frozen_game_frame
                is not None
            ):

                self.game_surface.blit(
                    self.frozen_game_frame,
                    (
                        0,
                        0,
                    ),
                )

            else:

                self.draw_3d_world()

                self.draw_hud()

        else:

            self.draw_menu_background(
                delta_time
            )

        if (
            self.state
            == STATE_LOADING
        ):

            self.draw_loading()

        elif (
            self.state
            == STATE_SIGN_IN_REQUIRED
        ):

            self.draw_sign_in_required()

        elif (
            self.state
            == STATE_MAIN_MENU
        ):

            self.draw_main_menu()

        elif (
            self.state
            == STATE_LEVEL_SELECT
        ):

            self.draw_level_select()

        elif (
            self.state
            == STATE_PAUSED
        ):

            self.draw_pause()

        elif (
            self.state
            == STATE_GAME_OVER
        ):

            self.draw_game_over()

        elif (
            self.state
            == STATE_LEVEL_COMPLETE
        ):

            self.draw_level_complete()

        elif (
            self.state
            == STATE_LEADERBOARD
        ):

            self.draw_leaderboard()

        elif (
            self.state
            == STATE_SETTINGS
        ):

            self.draw_settings()

        elif (
            self.state
            == STATE_HELP
        ):

            self.draw_help()

        elif (
            self.state
            == STATE_STATISTICS
        ):

            self.draw_statistics()

        elif (
            self.state
            == STATE_ACHIEVEMENTS
        ):

            self.draw_achievements()

        self.draw_crash_particles()

        self.draw_achievement_popup()

        if self.storage.show_fps:

            draw_text(
                self.game_surface,
                self.small_font,
                (
                    f"{self.clock.get_fps():.0f} FPS"
                    f"  Q{self.quality_level}"
                ),
                GREEN,
                10,
                8,
            )

    # ========================================================
    # SIMPLE SCREENS
    # ========================================================

    def draw_loading(
        self,
    ):

        draw_text(
            self.game_surface,
            self.title_font,
            GAME_TITLE.upper(),
            WHITE,
            GAME_CENTER_X,
            250,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.normal_font,
            "CHECKING ACCOUNT...",
            CYAN,
            GAME_CENTER_X,
            360,
            center=True,
        )

    def draw_sign_in_required(
        self,
    ):

        draw_text(
            self.game_surface,
            self.title_font,
            "SIGN IN REQUIRED",
            RED,
            GAME_CENTER_X,
            250,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.small_font,
            self.session_manager.message,
            WHITE,
            GAME_CENTER_X,
            350,
            center=True,
        )

    def draw_main_menu(
        self,
    ):

        draw_text(
            self.game_surface,
            self.title_font,
            GAME_TITLE.upper(),
            WHITE,
            GAME_CENTER_X,
            90,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.normal_font,
            (
                "Signed in as "
                f"{self.session_manager.username}"
            ),
            LIGHT_BLUE,
            GAME_CENTER_X,
            160,
            center=True,
        )

        self.levels_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.small_font,
            (
                "All-Time Endless Best: "
                f"{format_distance(self.displayed_personal_best)}"
            ),
            YELLOW,
            GAME_CENTER_X,
            380,
            center=True,
        )

        self.endless_button.draw(
            self.game_surface
        )

        self.leaderboard_button.draw(
            self.game_surface
        )

        self.settings_button.draw(
            self.game_surface
        )

        self.stats_button.draw(
            self.game_surface
        )

        self.achievements_button.draw(
            self.game_surface
        )

        self.help_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.version_font,
            format_version(),
            LIGHT_GREY,
            GAME_WIDTH - 18,
            GAME_HEIGHT - 26,
            right=True,
        )

    def draw_level_select(
        self,
    ):

        self.back_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.title_font,
            "SELECT LEVEL",
            WHITE,
            GAME_CENTER_X,
            78,
            center=True,
        )

        for level_number, button in (
            self._level_buttons()
        ):

            button.draw(
                self.game_surface
            )

            definition = get_level(
                level_number
            )

            draw_text(
                self.game_surface,
                self.tiny_font,
                definition.name,
                (
                    WHITE
                    if button.enabled
                    else GREY
                ),
                button.rect.centerx,
                button.rect.bottom + 18,
                center=True,
            )

        draw_text(
            self.game_surface,
            self.small_font,
            (
                f"Page {self.level_page + 1}/5"
            ),
            LIGHT_GREY,
            GAME_CENTER_X,
            620,
            center=True,
        )

    def _draw_dark_overlay(
        self,
    ):

        overlay = pygame.Surface(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                0,
                0,
                0,
                180,
            )
        )

        self.game_surface.blit(
            overlay,
            (
                0,
                0,
            ),
        )

    def draw_pause(
        self,
    ):

        self._draw_dark_overlay()

        draw_text(
            self.game_surface,
            self.title_font,
            "PAUSED",
            WHITE,
            GAME_CENTER_X,
            205,
            center=True,
        )

        self.pause_resume_button.draw(
            self.game_surface
        )

        self.pause_restart_button.draw(
            self.game_surface
        )

        self.pause_menu_button.draw(
            self.game_surface
        )

    def draw_game_over(
        self,
    ):

        self._draw_dark_overlay()

        draw_text(
            self.game_surface,
            self.title_font,
            "CRASHED",
            RED,
            GAME_CENTER_X,
            140,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.large_font,
            format_distance(
                self.last_run_distance
            ),
            WHITE,
            GAME_CENTER_X,
            245,
            center=True,
        )

        if (
            self.game_mode
            == MODE_ENDLESS
        ):

            draw_text(
                self.game_surface,
                self.normal_font,
                (
                    "All-Time Best: "
                    f"{format_distance(self.displayed_personal_best)}"
                ),
                YELLOW,
                GAME_CENTER_X,
                325,
                center=True,
            )

        else:

            draw_text(
                self.game_surface,
                self.normal_font,
                (
                    f"Level {self.selected_level_number}"
                ),
                LIGHT_BLUE,
                GAME_CENTER_X,
                325,
                center=True,
            )

        self.retry_button.draw(
            self.game_surface
        )

        self.game_over_menu_button.draw(
            self.game_surface
        )

    def draw_level_complete(
        self,
    ):

        self._draw_dark_overlay()

        draw_text(
            self.game_surface,
            self.title_font,
            "LEVEL COMPLETE",
            GREEN,
            GAME_CENTER_X,
            130,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.large_font,
            (
                f"Level {self.selected_level_number}"
            ),
            WHITE,
            GAME_CENTER_X,
            225,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.normal_font,
            (
                "Time: "
                f"{format_level_time(self.last_run_time)}"
            ),
            LIGHT_BLUE,
            GAME_CENTER_X,
            310,
            center=True,
        )

        next_level = get_next_level(
            self.selected_level_number
        )

        self.next_level_button.enabled = (
            next_level
            is not None
        )

        self.next_level_button.draw(
            self.game_surface
        )

        self.level_select_button.draw(
            self.game_surface
        )

    # ========================================================
    # LEADERBOARD
    # ========================================================

    def draw_leaderboard(
        self,
    ):

        self.back_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.title_font,
            "ENDLESS LEADERBOARD",
            WHITE,
            GAME_CENTER_X,
            75,
            center=True,
        )

        panel = pygame.Rect(
            220,
            175,
            840,
            455,
        )

        draw_panel(
            self.game_surface,
            panel,
            border=CYAN,
        )

        if not self.leaderboard:

            draw_text(
                self.game_surface,
                self.normal_font,
                self.leaderboard_message,
                LIGHT_GREY,
                panel.centerx,
                panel.centery,
                center=True,
            )

            return

        rank = get_player_rank(
            self.leaderboard,
            self.session_manager.user_id,
        )

        if rank:

            draw_text(
                self.game_surface,
                self.small_font,
                f"Your rank: #{rank}",
                GREEN,
                panel.centerx,
                panel.top + 20,
                center=True,
            )

        for index, entry in enumerate(
            self.leaderboard[
                :MAX_LEADERBOARD_ENTRIES
            ]
        ):

            y = (
                panel.top
                + 55
                + index
                * 37
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                (
                    f"{index + 1}."
                ),
                WHITE,
                panel.left + 35,
                y,
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                leaderboard_entry_name(
                    entry
                ),
                WHITE,
                panel.left + 105,
                y,
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                format_leaderboard_distance(
                    leaderboard_entry_distance(
                        entry
                    )
                ),
                YELLOW,
                panel.right - 35,
                y,
                right=True,
            )

    # ========================================================
    # SETTINGS / HELP / STATS / ACHIEVEMENTS
    # ========================================================

    def draw_settings(
        self,
    ):

        self.back_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.title_font,
            "SETTINGS",
            WHITE,
            GAME_CENTER_X,
            78,
            center=True,
        )

        for key, label, rect in (
            self._settings_rows()
        ):

            enabled = bool(
                self.storage.get_setting(
                    key,
                    False,
                )
            )

            pygame.draw.rect(
                self.game_surface,
                (
                    15,
                    28,
                    55,
                ),
                rect,
                border_radius=12,
            )

            pygame.draw.rect(
                self.game_surface,
                (
                    GREEN
                    if enabled
                    else RED
                ),
                rect,
                width=2,
                border_radius=12,
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                label,
                WHITE,
                rect.left + 18,
                rect.top + 10,
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                (
                    "ON"
                    if enabled
                    else "OFF"
                ),
                (
                    GREEN
                    if enabled
                    else RED
                ),
                rect.right - 18,
                rect.top + 10,
                right=True,
            )

    def draw_help(
        self,
    ):

        self.back_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.title_font,
            "HOW TO PLAY",
            WHITE,
            GAME_CENTER_X,
            75,
            center=True,
        )

        lines = (
            "A / D or Left / Right — rotate around the tunnel.",
            "You automatically travel forward.",
            "Move into openings before obstacles reach you.",
            "Rotating hazards continue moving while approaching.",
            "Levels get faster and harder.",
            "Endless distance counts toward the leaderboard.",
            "Escape pauses. F11 toggles fullscreen.",
        )

        for index, line in enumerate(
            lines
        ):

            draw_text(
                self.game_surface,
                self.normal_font,
                line,
                WHITE,
                GAME_CENTER_X,
                200
                + index
                * 58,
                center=True,
            )

    def draw_statistics(
        self,
    ):

        self.back_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.title_font,
            "STATISTICS",
            WHITE,
            GAME_CENTER_X,
            75,
            center=True,
        )

        rows = (
            (
                "Endless Best",
                format_distance(
                    self.displayed_personal_best
                ),
            ),

            (
                "Highest Level",
                (
                    f"{self.storage.highest_unlocked_level}"
                    f" / {TOTAL_LEVELS}"
                ),
            ),

            (
                "Total Runs",
                str(
                    self.storage.total_runs()
                ),
            ),

            (
                "Total Crashes",
                str(
                    self.storage.total_crashes()
                ),
            ),

            (
                "Total Distance",
                format_distance(
                    self.storage.total_distance()
                ),
            ),

            (
                "Play Time",
                format_play_time(
                    self.storage.total_play_time_seconds()
                ),
            ),
        )

        for index, (
            label,
            value,
        ) in enumerate(
            rows
        ):

            y = (
                190
                + index
                * 65
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                label,
                LIGHT_GREY,
                350,
                y,
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                value,
                WHITE,
                930,
                y,
                right=True,
            )

    def draw_achievements(
        self,
    ):

        from config import (
            ACHIEVEMENT_DEFINITIONS,
        )

        self.back_button.draw(
            self.game_surface
        )

        draw_text(
            self.game_surface,
            self.title_font,
            "ACHIEVEMENTS",
            WHITE,
            GAME_CENTER_X,
            70,
            center=True,
        )

        unlocked = set(
            self.storage.unlocked_achievements
        )

        all_ids = list(
            ACHIEVEMENT_DEFINITIONS.keys()
        )

        for index, achievement_id in enumerate(
            all_ids
        ):

            column = index % 2
            row = index // 2

            x = (
                180
                + column
                * 500
            )

            y = (
                165
                + row
                * 85
            )

            is_unlocked = (
                achievement_id
                in unlocked
            )

            hidden = (
                achievement_is_hidden(
                    achievement_id
                )
            )

            if hidden and not is_unlocked:

                name = "???"
                description = "Hidden achievement"

            else:

                name = get_achievement_name(
                    achievement_id
                )

                description = (
                    get_achievement_description(
                        achievement_id
                    )
                )

            draw_text(
                self.game_surface,
                self.small_font,
                (
                    "✓ "
                    if is_unlocked
                    else "○ "
                )
                + name,
                (
                    GREEN
                    if is_unlocked
                    else GREY
                ),
                x,
                y,
            )

            draw_text(
                self.game_surface,
                self.tiny_font,
                description,
                LIGHT_GREY,
                x,
                y + 30,
            )

    # ========================================================
    # EFFECT DRAW
    # ========================================================

    def draw_crash_particles(
        self,
    ):

        for particle in (
            self.crash_particles
        ):

            pygame.draw.circle(
                self.game_surface,
                ORANGE,
                particle.position.int_tuple(),
                particle.radius,
            )

    def draw_achievement_popup(
        self,
    ):

        if not self.current_achievement:
            return

        rect = pygame.Rect(
            GAME_WIDTH - 390,
            88,
            350,
            108,
        )

        draw_panel(
            self.game_surface,
            rect,
            border=YELLOW,
        )

        draw_text(
            self.game_surface,
            self.small_font,
            "ACHIEVEMENT UNLOCKED",
            YELLOW,
            rect.centerx,
            rect.top + 22,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.normal_font,
            get_achievement_name(
                self.current_achievement
            ),
            WHITE,
            rect.centerx,
            rect.top + 57,
            center=True,
        )

    # ========================================================
    # LOOP
    # ========================================================

    async def run(
        self,
    ):

        while self.running:

            delta_time = min(
                0.05,

                self.clock.tick(
                    TARGET_FPS
                )
                / 1000,
            )

            current_time = (
                pygame.time.get_ticks()
            )

            for event in (
                pygame.event.get()
            ):

                self.handle_event(
                    event
                )

            self.update(
                delta_time,
                current_time,
            )

            self.draw(
                current_time,
                delta_time,
            )

            self.present()

            await asyncio.sleep(
                0
            )

        gc.enable()

        self.storage.save_all()

        pygame.quit()


async def main():

    game = TunnelRunnerGame()

    await game.run()


if __name__ == "__main__":

    asyncio.run(
        main()
    )