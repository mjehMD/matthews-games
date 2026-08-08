from __future__ import annotations

import asyncio
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
    USE_SMOOTH_SCALING,
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
# MAIN GAME
# VERSION 0.1.1
# ============================================================


IS_WEB = sys.platform in (
    "emscripten",
    "wasi",
)


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

TUNNEL_CACHE_BEHIND = 12.0

TUNNEL_CACHE_AHEAD = (
    TUNNEL_VISIBLE_LENGTH
    + 24.0
)

TUNNEL_CACHE_REMOVE_BEHIND = 24.0

TUNNEL_CACHE_EXTRA_AHEAD = 30.0

TUNNEL_CACHE_MAX_CHUNKS = 48

TUNNEL_RENDER_DISTANCE = (
    TUNNEL_VISIBLE_LENGTH
)

PERFORMANCE_TUNNEL_SEGMENTS = max(
    12,
    min(
        TUNNEL_SEGMENTS,
        16,
    ),
)

PERFORMANCE_TUNNEL_SECTION_LENGTH = max(
    7.5,
    TUNNEL_SECTION_LENGTH,
)


# ============================================================
# UI HELPERS
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
        rect: pygame.Rect | tuple[int, int, int, int],
        text: str,
        font: pygame.font.Font,
        *,
        accent: tuple[int, int, int] = CYAN,
        enabled: bool = True,
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
        mouse_position: tuple[int, int],
    ) -> None:
        self.hovered = (
            self.enabled
            and self.rect.collidepoint(
                mouse_position
            )
        )

    def clicked(
        self,
        event: pygame.event.Event,
    ) -> bool:
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
        surface: pygame.Surface,
    ) -> None:
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
            340.0,
        )

        self.position = position.copy()

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
            0.35,
            0.8,
        )

        self.maximum_life = (
            self.life
        )

        self.radius = random.randint(
            2,
            5,
        )

    def update(
        self,
        delta_time: float,
    ) -> None:
        self.life -= delta_time

        self.position = (
            self.position
            + self.velocity
            * delta_time
        )

        self.velocity = (
            self.velocity
            * max(
                0.0,
                1.0
                - 2.4
                * delta_time,
            )
        )

    @property
    def alive(
        self,
    ) -> bool:
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
        self.start_z = (
            start_z
        )

        self.end_z = (
            end_z
        )

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
    ) -> None:
        self.chunks.clear()

        self.next_z = 0.0

        self.theme_name = ""

    def reset(
        self,
        camera_z: float,
        theme_name: str,
    ) -> None:
        self.chunks.clear()

        self.theme_name = (
            theme_name
        )

        section_length = (
            PERFORMANCE_TUNNEL_SECTION_LENGTH
        )

        start_z = max(
            0.0,
            math.floor(
                (
                    camera_z
                    - TUNNEL_CACHE_BEHIND
                )
                / section_length
            )
            * section_length,
        )

        self.next_z = (
            start_z
        )

    def _create_chunk(
        self,
        start_z: float,
        end_z: float,
        theme_name: str,
    ) -> TunnelCacheChunk:
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

                draw_outlines=True,
            )
        )

        return TunnelCacheChunk(
            start_z,
            end_z,
            mesh,
        )

    def update(
        self,
        camera_z: float,
        theme_name: str,
    ) -> None:
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
            + TUNNEL_CACHE_AHEAD
            + TUNNEL_CACHE_EXTRA_AHEAD
        )

        section_length = (
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
                + section_length
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
        camera_z: float,
    ) -> list[
        Mesh3D
    ]:
        minimum_z = (
            camera_z
            - 2.0
        )

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
                >= minimum_z

                and chunk.start_z
                <= maximum_z
            )
        ]


# ============================================================
# MAIN GAME
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

        self.display_rect = pygame.Rect(
            0,
            0,
            GAME_WIDTH,
            GAME_HEIGHT,
        )

        self.display_scale = 1.0

        self._recalculate_display()

        self.clock = (
            pygame.time.Clock()
        )

        # ====================================================
        # FONTS
        # ====================================================

        self.title_font = (
            pygame.font.Font(
                None,
                88,
            )
        )

        self.large_font = (
            pygame.font.Font(
                None,
                LARGE_FONT_SIZE,
            )
        )

        self.heading_font = (
            pygame.font.Font(
                None,
                HEADING_FONT_SIZE,
            )
        )

        self.normal_font = (
            pygame.font.Font(
                None,
                NORMAL_FONT_SIZE,
            )
        )

        self.small_font = (
            pygame.font.Font(
                None,
                SMALL_FONT_SIZE,
            )
        )

        self.tiny_font = (
            pygame.font.Font(
                None,
                TINY_FONT_SIZE,
            )
        )

        self.version_font = (
            pygame.font.Font(
                None,
                VERSION_FONT_SIZE,
            )
        )

        self.title_font.set_bold(
            True
        )

        self.heading_font.set_bold(
            True
        )

        # ====================================================
        # 3D
        # ====================================================

        self.camera = Camera3D(
            width=GAME_WIDTH,
            height=GAME_HEIGHT,
        )

        self.renderer = SceneRenderer3D(
            self.camera
        )

        self.obstacles = (
            ObstacleManager()
        )

        self.endless_generator = (
            EndlessGenerator()
        )

        self.tunnel_cache = (
            TunnelMeshCache()
        )

        # ====================================================
        # ACCOUNT
        # ====================================================

        self.session_manager = (
            PlayerSessionManager()
        )

        self.session_manager.begin_loading()

        # ====================================================
        # GAME STATE
        # ====================================================

        self.state = STATE_LOADING

        self.game_mode = MODE_LEVELS

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

        self.last_run_distance = 0.0

        self.last_run_time = 0.0

        self.last_run_new_best = False

        self.last_run_new_level_time = False

        self.last_crash_obstacle = ""

        self.run_recorded = False

        self.shake_time = 0.0

        self.shake_strength = 0.0

        self.crash_particles: list[
            CrashParticle
        ] = []

        # ====================================================
        # ONLINE
        # ====================================================

        self.online_personal_best = 0

        self.leaderboard: list[
            dict[str, Any]
        ] = []

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

        self.achievement_queue: list[
            str
        ] = []

        self.current_achievement = ""

        self.achievement_started = 0

        self.level_page = 0

        # ====================================================
        # MENU BACKGROUND
        # ====================================================

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
                    8.0,
                    36.0,
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
                130
            )
        ]

        self._build_buttons()

    # ========================================================
    # DISPLAY
    # ========================================================

    def _create_display(
        self,
    ) -> pygame.Surface:
        if (
            self.fullscreen
            and ALLOW_FULLSCREEN
        ):
            info = (
                pygame.display.Info()
            )

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

        flags = (
            pygame.RESIZABLE
            if ALLOW_RESIZING
            else 0
        )

        return pygame.display.set_mode(
            (
                GAME_WIDTH,
                GAME_HEIGHT,
            ),
            flags,
        )

    def _recalculate_display(
        self,
    ) -> None:
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
        position: tuple[int, int],
    ) -> tuple[int, int]:
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
        event: pygame.event.Event,
    ) -> pygame.event.Event:
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
    ) -> None:
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
    ) -> None:
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

        elif USE_SMOOTH_SCALING:
            frame = pygame.transform.smoothscale(
                self.game_surface,
                self.display_rect.size,
            )

        else:
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
    ) -> None:
        center_x = (
            GAME_WIDTH
            // 2
            - BUTTON_WIDTH
            // 2
        )

        self.levels_button = Button(
            (
                center_x,
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
                center_x,
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
                center_x,
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

    # ========================================================
    # LEVEL BUTTONS
    # ========================================================

    def _level_buttons(
        self,
    ) -> list[
        tuple[int, Button]
    ]:
        result = []

        start = (
            self.level_page
            * 10
            + 1
        )

        end = min(
            TOTAL_LEVELS,
            start + 9,
        )

        for (
            index,
            level_number,
        ) in enumerate(
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

            x = (
                150
                + column
                * 200
            )

            y = (
                255
                + row
                * 160
            )

            unlocked = (
                self.storage.is_level_unlocked(
                    level_number
                )
            )

            completed = (
                self.storage.is_level_completed(
                    level_number
                )
            )

            button = Button(
                (
                    x,
                    y,
                    160,
                    92,
                ),

                str(
                    level_number
                ),

                self.heading_font,

                accent=(
                    GREEN
                    if completed
                    else CYAN
                ),

                enabled=unlocked,
            )

            result.append(
                (
                    level_number,
                    button,
                )
            )

        return result

    def _visible_buttons(
        self,
    ) -> list[Button]:
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

                    for (
                        _,
                        button,
                    ) in self._level_buttons()
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
    ) -> None:
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
    # SESSION
    # ========================================================

    def update_session(
        self,
    ) -> None:
        if not self.session_manager.update():
            return

        if self.session_manager.signed_in:
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
    ) -> None:
        if not self.session_manager.signed_in:
            return

        if self.session_manager.desktop_test_account:
            return

        if (
            self.personal_best_task
            is not None
            and not self.personal_best_task.done()
        ):
            return

        self.personal_best_task = (
            asyncio.create_task(
                load_personal_best(
                    self.session_manager.user_id,
                    self.session_manager.access_token,
                )
            )
        )

    def start_leaderboard_load(
        self,
    ) -> None:
        if (
            self.leaderboard_task
            is not None
            and not self.leaderboard_task.done()
        ):
            return

        self.leaderboard_message = (
            "Loading leaderboard..."
        )

        self.leaderboard_task = (
            asyncio.create_task(
                load_global_leaderboard()
            )
        )

    def submit_endless_score(
        self,
        distance: float,
    ) -> None:
        if not self.session_manager.signed_in:
            return

        if self.session_manager.desktop_test_account:
            self.submit_message = (
                "Desktop test scores are not uploaded."
            )

            return

        if (
            self.submit_task
            is not None
            and not self.submit_task.done()
        ):
            return

        self.submit_message = (
            "Saving score..."
        )

        self.submit_task = (
            asyncio.create_task(
                submit_endless_distance(
                    self.session_manager.username,
                    distance,
                    self.session_manager.user_id,
                    self.session_manager.access_token,
                )
            )
        )

    def update_online_tasks(
        self,
    ) -> None:
        if (
            self.personal_best_task
            is not None
            and self.personal_best_task.done()
        ):
            try:
                (
                    distance,
                    _message,
                ) = (
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
            is not None
            and self.leaderboard_task.done()
        ):
            try:
                (
                    entries,
                    message,
                ) = (
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
            is not None
            and self.submit_task.done()
        ):
            try:
                (
                    success,
                    message,
                    stored_best,
                    new_best,
                ) = (
                    self.submit_task.result()
                )

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
    ) -> int:
        return max(
            self.storage.endless_best_distance,
            self.online_personal_best,
        )

    # ========================================================
    # RUN SETUP
    # ========================================================

    def reset_run_state(
        self,
    ) -> None:
        self.camera.position = Vec3(
            0.0,
            0.0,
            0.0,
        )

        self.camera.rotation = Vec3(
            0.0,
            0.0,
            PLAYER_START_ANGLE,
        )

        self.camera.shake_offset = (
            Vec2()
        )

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

        self.last_run_distance = 0.0

        self.last_run_time = 0.0

        self.last_run_new_best = False

        self.last_run_new_level_time = False

        self.last_crash_obstacle = ""

        self.run_recorded = False

        self.shake_time = 0.0

        self.shake_strength = 0.0

        self.crash_particles.clear()

        self.submit_message = ""

        self.tunnel_cache.clear()

    def start_level(
        self,
        level_number: int,
    ) -> None:
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

        self.state = (
            STATE_PLAYING
        )

    def start_endless(
        self,
    ) -> None:
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
                0.0
            )
        )

        self.storage.record_endless_start()

        self.state = (
            STATE_PLAYING
        )

    def restart_current_run(
        self,
    ) -> None:
        if (
            self.game_mode
            == MODE_LEVELS
        ):
            self.start_level(
                self.selected_level_number
            )

        else:
            self.start_endless()

    # ========================================================
    # RUN INFO
    # ========================================================

    @property
    def run_distance(
        self,
    ) -> float:
        return max(
            0.0,
            self.camera.position.z
            - self.run_start_z,
        )

    def run_time_seconds(
        self,
    ) -> float:
        end_ticks = (
            self.run_end_ticks
            if self.run_end_ticks > 0
            else pygame.time.get_ticks()
        )

        elapsed_ms = max(
            0,

            end_ticks
            - self.run_start_ticks
            - self.total_paused_ms,
        )

        return (
            elapsed_ms
            / 1000.0
        )

    # ========================================================
    # CRASH
    # ========================================================

    def trigger_crash(
        self,
        obstacle_type: str,
    ) -> None:
        if self.run_recorded:
            return

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
            (
                _best,
                new_best,
            ) = (
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

        self.shake_time = (
            CAMERA_SHAKE_DURATION
        )

        self.shake_strength = (
            CAMERA_SHAKE_AMOUNT
        )

        self._spawn_crash_particles()

        self.state = (
            STATE_GAME_OVER
        )

    # ========================================================
    # LEVEL COMPLETE
    # ========================================================

    def trigger_level_complete(
        self,
    ) -> None:
        if (
            self.run_recorded
            or self.current_level is None
        ):
            return

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

        (
            _first_completion,
            new_best_time,
        ) = (
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
            new_best_time
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
    ) -> None:
        for achievement_id in (
            self.storage.consume_new_achievements()
        ):
            if (
                achievement_id
                not in self.achievement_queue
            ):
                self.achievement_queue.append(
                    achievement_id
                )

    def update_achievement_popup(
        self,
        current_time: int,
    ) -> None:
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
            >= 3200
        ):
            self.current_achievement = ""

    # ========================================================
    # EVENT HANDLING
    # ========================================================

    def handle_event(
        self,
        raw_event: pygame.event.Event,
    ) -> None:
        event = (
            self._convert_event(
                raw_event
            )
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
                    if (
                        self.paused_at_ticks
                        > 0
                    ):
                        self.total_paused_ms += (
                            pygame.time.get_ticks()
                            - self.paused_at_ticks
                        )

                    self.paused_at_ticks = 0

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
            self._handle_main_menu_event(
                event
            )

        elif (
            self.state
            == STATE_LEVEL_SELECT
        ):
            self._handle_level_select_event(
                event
            )

        elif (
            self.state
            == STATE_PAUSED
        ):
            self._handle_pause_event(
                event
            )

        elif (
            self.state
            == STATE_GAME_OVER
        ):
            self._handle_game_over_event(
                event
            )

        elif (
            self.state
            == STATE_LEVEL_COMPLETE
        ):
            self._handle_level_complete_event(
                event
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

    def _handle_main_menu_event(
        self,
        event: pygame.event.Event,
    ) -> None:
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

    def _handle_level_select_event(
        self,
        event: pygame.event.Event,
    ) -> None:
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
                return

            if event.key in (
                pygame.K_RIGHT,
                pygame.K_PAGEDOWN,
            ):
                self.level_page = min(
                    4,
                    self.level_page + 1,
                )
                return

        for (
            level_number,
            button,
        ) in self._level_buttons():
            if button.clicked(
                event
            ):
                self.start_level(
                    level_number
                )
                return

    def _handle_pause_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        if self.pause_resume_button.clicked(
            event
        ):
            if (
                self.paused_at_ticks
                > 0
            ):
                self.total_paused_ms += (
                    pygame.time.get_ticks()
                    - self.paused_at_ticks
                )

            self.paused_at_ticks = 0

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

    def _handle_game_over_event(
        self,
        event: pygame.event.Event,
    ) -> None:
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
            event.type
            == pygame.KEYDOWN
            and event.key
            == pygame.K_r
        ):
            self.restart_current_run()

    def _handle_level_complete_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        next_level = (
            get_next_level(
                self.selected_level_number
            )
        )

        self.next_level_button.enabled = (
            next_level is not None
        )

        if (
            self.next_level_button.clicked(
                event
            )
            and next_level is not None
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

            for (
                index,
                (
                    key,
                    label,
                ),
            ) in enumerate(
                rows
            )
        ]

    def _handle_settings_event(
        self,
        event: pygame.event.Event,
    ) -> None:
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

        for (
            key,
            _label,
            rect,
        ) in self._settings_rows():
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
        delta_time: float,
        current_time: int,
    ) -> None:
        self.update_session()

        self.update_online_tasks()

        self.update_button_hovers()

        self.update_achievement_popup(
            current_time
        )

        self._update_particles(
            delta_time
        )

        if (
            self.shake_time
            > 0.0
        ):
            self.shake_time = max(
                0.0,
                self.shake_time
                - delta_time,
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

        if collision is not None:
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

        self._update_camera_shake()

        self.tunnel_cache.update(
            self.camera.position.z,
            self._current_theme_name(),
        )

    # ========================================================
    # PLAYER MOVEMENT
    # ========================================================

    def _update_player_movement(
        self,
        delta_time: float,
    ) -> None:
        keys = (
            pygame.key.get_pressed()
        )

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

        if (
            direction
            != 0
        ):
            target_velocity = (
                direction
                * PLAYER_MAX_ROTATION_SPEED
            )

            change = (
                PLAYER_ROTATION_ACCELERATION
                * delta_time
            )

            if (
                self.player_rotation_velocity
                < target_velocity
            ):
                self.player_rotation_velocity = min(
                    target_velocity,
                    self.player_rotation_velocity
                    + change,
                )

            else:
                self.player_rotation_velocity = max(
                    target_velocity,
                    self.player_rotation_velocity
                    - change,
                )

        else:
            deceleration = (
                PLAYER_ROTATION_DECELERATION
                * delta_time
            )

            if (
                self.player_rotation_velocity
                > 0.0
            ):
                self.player_rotation_velocity = max(
                    0.0,
                    self.player_rotation_velocity
                    - deceleration,
                )

            elif (
                self.player_rotation_velocity
                < 0.0
            ):
                self.player_rotation_velocity = min(
                    0.0,
                    self.player_rotation_velocity
                    + deceleration,
                )

        self.player_angle = (
            self.player_angle
            + self.player_rotation_velocity
            * delta_time
        ) % 360.0

    # ========================================================
    # SHAKE
    # ========================================================

    def _update_camera_shake(
        self,
    ) -> None:
        if (
            not self.storage.screen_shake_enabled
            or self.shake_time
            <= 0.0
        ):
            self.camera.shake_offset = (
                Vec2()
            )
            return

        ratio = clamp(
            self.shake_time
            / max(
                0.001,
                CAMERA_SHAKE_DURATION,
            ),
            0.0,
            1.0,
        )

        strength = (
            35.0
            * self.shake_strength
            * ratio
        )

        self.camera.shake_offset = Vec2(
            random.uniform(
                -strength,
                strength,
            ),

            random.uniform(
                -strength,
                strength,
            ),
        )

    # ========================================================
    # PARTICLES
    # ========================================================

    def _spawn_crash_particles(
        self,
    ) -> None:
        if not self.storage.particles_enabled:
            return

        center = Vec2(
            GAME_CENTER_X,
            GAME_CENTER_Y,
        )

        for _ in range(
            55
        ):
            self.crash_particles.append(
                CrashParticle(
                    center
                )
            )

    def _update_particles(
        self,
        delta_time: float,
    ) -> None:
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
    ) -> str:
        if (
            self.game_mode
            == MODE_LEVELS
            and self.current_level
            is not None
        ):
            return (
                self.current_level.theme_name
            )

        distance = (
            self.run_distance
        )

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
    # 3D WORLD
    # ========================================================

    def draw_3d_world(
        self,
    ) -> None:
        theme_name = (
            self._current_theme_name()
        )

        theme = get_theme(
            theme_name
        )

        self.game_surface.fill(
            theme.background
        )

        self.renderer.clear()

        self.renderer.fog_colour = (
            theme.background
        )

        self.renderer.use_lighting = False

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
                TUNNEL_VISIBLE_LENGTH,
            )
        )

        self.renderer.draw(
            self.game_surface
        )

        self._draw_speed_lines(
            theme.glow
        )

    # ========================================================
    # SPEED LINES
    # ========================================================

    def _draw_speed_lines(
        self,
        colour: tuple[int, int, int],
    ) -> None:
        if not self.storage.speed_lines_enabled:
            return

        if (
            self.current_speed
            < 34.0
        ):
            return

        intensity = clamp(
            (
                self.current_speed
                - 34.0
            )
            / 34.0,
            0.0,
            1.0,
        )

        count = round(
            8
            + 18
            * intensity
        )

        for index in range(
            count
        ):
            angle = (
                index
                / max(
                    1,
                    count,
                )
                * math.tau
                + self.menu_time
                * 0.7
            )

            radius = (
                170
                + (
                    index
                    * 31
                    + int(
                        self.camera.position.z
                        * 5
                    )
                )
                % 300
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
                    + 18
                    + 25
                    * intensity
                )
            )

            y2 = (
                GAME_CENTER_Y
                + math.sin(
                    angle
                )
                * (
                    radius
                    + 18
                    + 25
                    * intensity
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
        delta_time: float,
    ) -> None:
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

        for index in range(
            7
        ):
            radius = (
                70
                + (
                    self.menu_time
                    * 70
                    + index
                    * 110
                )
                % 720
            )

            pygame.draw.circle(
                self.game_surface,
                (
                    20,
                    65,
                    110,
                ),
                (
                    GAME_CENTER_X,
                    GAME_CENTER_Y,
                ),
                round(
                    radius
                ),
                width=2,
            )

    # ========================================================
    # HUD
    # ========================================================

    def draw_hud(
        self,
    ) -> None:
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

        if (
            SHOW_LEVEL
            and self.game_mode
            == MODE_LEVELS
            and self.current_level
            is not None
        ):
            rect = pygame.Rect(
                GAME_WIDTH
                - HUD_MARGIN
                - HUD_WIDTH,
                HUD_MARGIN,
                HUD_WIDTH,
                HUD_HEIGHT,
            )

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
                / 100.0
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
            rect = pygame.Rect(
                GAME_WIDTH
                - HUD_MARGIN
                - HUD_WIDTH,
                HUD_MARGIN,
                HUD_WIDTH,
                HUD_HEIGHT,
            )

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
    # DRAW STATE
    # ========================================================

    def draw(
        self,
        current_time: int,
        delta_time: float,
    ) -> None:
        if self.state in (
            STATE_PLAYING,
            STATE_PAUSED,
            STATE_GAME_OVER,
            STATE_LEVEL_COMPLETE,
        ):
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
                self.tiny_font,
                (
                    f"{self.clock.get_fps():.0f}"
                    " FPS"
                ),
                GREEN,
                10,
                8,
            )

    # ========================================================
    # LOADING
    # ========================================================

    def draw_loading(
        self,
    ) -> None:
        panel = pygame.Rect(
            GAME_CENTER_X - 370,
            GAME_CENTER_Y - 135,
            740,
            270,
        )

        draw_panel(
            self.game_surface,
            panel,
            border=CYAN,
            width=3,
        )

        draw_text(
            self.game_surface,
            self.title_font,
            GAME_TITLE.upper(),
            WHITE,
            panel.centerx,
            panel.top + 65,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.normal_font,
            "CHECKING ACCOUNT",
            CYAN,
            panel.centerx,
            panel.top + 145,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.small_font,
            self.session_manager.message,
            LIGHT_GREY,
            panel.centerx,
            panel.top + 205,
            center=True,
        )

    # ========================================================
    # SIGN IN
    # ========================================================

    def draw_sign_in_required(
        self,
    ) -> None:
        panel = pygame.Rect(
            GAME_CENTER_X - 400,
            GAME_CENTER_Y - 160,
            800,
            320,
        )

        draw_panel(
            self.game_surface,
            panel,
            border=RED,
            width=3,
        )

        draw_text(
            self.game_surface,
            self.title_font,
            GAME_TITLE.upper(),
            WHITE,
            panel.centerx,
            panel.top + 65,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.heading_font,
            "SIGN IN REQUIRED",
            YELLOW,
            panel.centerx,
            panel.top + 145,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.small_font,
            self.session_manager.message,
            LIGHT_GREY,
            panel.centerx,
            panel.top + 215,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.small_font,
            (
                "Return to Matthew's Games, "
                "sign in, then reopen Tunnel Runner."
            ),
            WHITE,
            panel.centerx,
            panel.top + 260,
            center=True,
        )

    # ========================================================
    # MAIN MENU
    # ========================================================

    def draw_main_menu(
        self,
    ) -> None:
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

        draw_text(
            self.game_surface,
            self.small_font,
            (
                "A / D or Left / Right • "
                "Avoid the 3D barriers • "
                "Survive the tunnel"
            ),
            LIGHT_GREY,
            GAME_CENTER_X,
            215,
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

    # ========================================================
    # LEVEL SELECT
    # ========================================================

    def draw_level_select(
        self,
    ) -> None:
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

        draw_text(
            self.game_surface,
            self.small_font,
            (
                "Unlocked "
                f"{self.storage.highest_unlocked_level}"
                f" / {TOTAL_LEVELS}"
            ),
            LIGHT_BLUE,
            GAME_CENTER_X,
            145,
            center=True,
        )

        for (
            level_number,
            button,
        ) in self._level_buttons():
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

            if self.storage.is_level_completed(
                level_number
            ):
                draw_text(
                    self.game_surface,
                    self.tiny_font,
                    "COMPLETED",
                    GREEN,
                    button.rect.centerx,
                    button.rect.bottom + 39,
                    center=True,
                )

        draw_text(
            self.game_surface,
            self.small_font,
            (
                f"Page {self.level_page + 1}/5 "
                "• Left/Right changes page"
            ),
            LIGHT_GREY,
            GAME_CENTER_X,
            620,
            center=True,
        )

    # ========================================================
    # PAUSE
    # ========================================================

    def draw_pause(
        self,
    ) -> None:
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
                175,
            )
        )

        self.game_surface.blit(
            overlay,
            (
                0,
                0,
            ),
        )

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

    # ========================================================
    # GAME OVER
    # ========================================================

    def draw_game_over(
        self,
    ) -> None:
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

            if self.last_run_new_best:
                draw_text(
                    self.game_surface,
                    self.heading_font,
                    "NEW PERSONAL BEST!",
                    GREEN,
                    GAME_CENTER_X,
                    385,
                    center=True,
                )

            elif self.submit_message:
                draw_text(
                    self.game_surface,
                    self.tiny_font,
                    self.submit_message,
                    LIGHT_GREY,
                    GAME_CENTER_X,
                    385,
                    center=True,
                )

        else:
            draw_text(
                self.game_surface,
                self.normal_font,
                (
                    "Level "
                    f"{self.selected_level_number}"
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

    # ========================================================
    # LEVEL COMPLETE
    # ========================================================

    def draw_level_complete(
        self,
    ) -> None:
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
                175,
            )
        )

        self.game_surface.blit(
            overlay,
            (
                0,
                0,
            ),
        )

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
                "Level "
                f"{self.selected_level_number}"
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

        if self.last_run_new_level_time:
            draw_text(
                self.game_surface,
                self.heading_font,
                "NEW BEST TIME!",
                YELLOW,
                GAME_CENTER_X,
                370,
                center=True,
            )

        next_level = (
            get_next_level(
                self.selected_level_number
            )
        )

        self.next_level_button.enabled = (
            next_level is not None
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
    ) -> None:
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

        draw_text(
            self.game_surface,
            self.small_font,
            (
                "Your Best: "
                f"{format_distance(self.displayed_personal_best)}"
            ),
            YELLOW,
            GAME_CENTER_X,
            137,
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

        else:
            rank = get_player_rank(
                self.leaderboard,
                self.session_manager.user_id,
            )

            if rank is not None:
                draw_text(
                    self.game_surface,
                    self.tiny_font,
                    (
                        "Your Top 10 rank: "
                        f"#{rank}"
                    ),
                    GREEN,
                    panel.centerx,
                    panel.top + 20,
                    center=True,
                )

            for (
                index,
                entry,
            ) in enumerate(
                self.leaderboard[
                    :MAX_LEADERBOARD_ENTRIES
                ]
            ):
                y = (
                    panel.top
                    + 52
                    + index
                    * 37
                )

                rank_number = (
                    index + 1
                )

                colour = (
                    YELLOW
                    if rank_number == 1
                    else LIGHT_BLUE
                    if rank_number <= 3
                    else WHITE
                )

                draw_text(
                    self.game_surface,
                    self.normal_font,
                    f"{rank_number}.",
                    colour,
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
                    colour,
                    panel.right - 35,
                    y,
                    right=True,
                )

        draw_text(
            self.game_surface,
            self.tiny_font,
            "Press R to refresh.",
            LIGHT_GREY,
            GAME_CENTER_X,
            665,
            center=True,
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def draw_settings(
        self,
    ) -> None:
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

        for (
            key,
            label,
            rect,
        ) in self._settings_rows():
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

    # ========================================================
    # HELP
    # ========================================================

    def draw_help(
        self,
    ) -> None:
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

        panel = pygame.Rect(
            165,
            155,
            950,
            500,
        )

        draw_panel(
            self.game_surface,
            panel,
            border=LIGHT_BLUE,
        )

        lines = (
            (
                "A / Left Arrow",
                "Move around the tunnel to the left.",
            ),

            (
                "D / Right Arrow",
                "Move around the tunnel to the right.",
            ),

            (
                "Automatic movement",
                "You are always flying forward.",
            ),

            (
                "Barriers",
                "Move into the opening before the barrier reaches you.",
            ),

            (
                "Rotating hazards",
                "Watch where the safe space will be when you arrive.",
            ),

            (
                "50 Levels",
                "Each level introduces harder layouts and faster hazards.",
            ),

            (
                "Endless",
                "Run as far as possible. Your metres count on the leaderboard.",
            ),

            (
                "Escape",
                "Pause the current run.",
            ),

            (
                "F11",
                "Toggle fullscreen.",
            ),
        )

        for (
            index,
            (
                control,
                text,
            ),
        ) in enumerate(
            lines
        ):
            y = (
                panel.top
                + 30
                + index
                * 48
            )

            draw_text(
                self.game_surface,
                self.small_font,
                control,
                CYAN,
                panel.left + 28,
                y,
            )

            draw_text(
                self.game_surface,
                self.small_font,
                text,
                WHITE,
                panel.left + 255,
                y,
            )

    # ========================================================
    # STATISTICS
    # ========================================================

    def draw_statistics(
        self,
    ) -> None:
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
                "Levels Completed",
                str(
                    len(
                        self.storage.completed_levels
                    )
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

            (
                "Maximum Speed",
                (
                    f"{self.storage.maximum_speed_reached():.1f}"
                ),
            ),
        )

        panel = pygame.Rect(
            260,
            165,
            760,
            470,
        )

        draw_panel(
            self.game_surface,
            panel,
            border=GREEN,
        )

        for (
            index,
            (
                label,
                value,
            ),
        ) in enumerate(
            rows
        ):
            y = (
                panel.top
                + 35
                + index
                * 51
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                label,
                LIGHT_GREY,
                panel.left + 30,
                y,
            )

            draw_text(
                self.game_surface,
                self.normal_font,
                value,
                WHITE,
                panel.right - 30,
                y,
                right=True,
            )

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    def draw_achievements(
        self,
    ) -> None:
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
            72,
            center=True,
        )

        unlocked = set(
            self.storage.unlocked_achievements
        )

        draw_text(
            self.game_surface,
            self.small_font,
            (
                f"{len(unlocked)}"
                " / "
                f"{len(ACHIEVEMENT_DEFINITIONS)}"
                " unlocked"
            ),
            LIGHT_BLUE,
            GAME_CENTER_X,
            130,
            center=True,
        )

        panel = pygame.Rect(
            150,
            155,
            980,
            505,
        )

        draw_panel(
            self.game_surface,
            panel,
            border=ORANGE,
        )

        all_ids = list(
            ACHIEVEMENT_DEFINITIONS.keys()
        )

        for (
            index,
            achievement_id,
        ) in enumerate(
            all_ids
        ):
            column = (
                index
                % 2
            )

            row = (
                index
                // 2
            )

            rect = pygame.Rect(
                panel.left
                + 25
                + column
                * 470,

                panel.top
                + 25
                + row
                * 86,

                440,

                68,
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

            if (
                hidden
                and not is_unlocked
            ):
                name = "???"

                description = (
                    "Hidden achievement"
                )

            else:
                name = (
                    get_achievement_name(
                        achievement_id
                    )
                )

                description = (
                    get_achievement_description(
                        achievement_id
                    )
                )

            pygame.draw.rect(
                self.game_surface,
                (
                    18,
                    28,
                    52,
                ),
                rect,
                border_radius=10,
            )

            pygame.draw.rect(
                self.game_surface,
                (
                    GREEN
                    if is_unlocked
                    else GREY
                ),
                rect,
                width=2,
                border_radius=10,
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
                    else LIGHT_GREY
                ),
                rect.left + 12,
                rect.top + 9,
            )

            draw_text(
                self.game_surface,
                self.tiny_font,
                description,
                (
                    WHITE
                    if is_unlocked
                    else GREY
                ),
                rect.left + 12,
                rect.top + 39,
            )

    # ========================================================
    # PARTICLES
    # ========================================================

    def draw_crash_particles(
        self,
    ) -> None:
        for particle in (
            self.crash_particles
        ):
            alpha_ratio = clamp(
                particle.life
                / max(
                    0.001,
                    particle.maximum_life,
                ),
                0.0,
                1.0,
            )

            colour = (
                255,

                round(
                    100
                    + 155
                    * alpha_ratio
                ),

                60,
            )

            pygame.draw.circle(
                self.game_surface,
                colour,
                particle.position.int_tuple(),
                particle.radius,
            )

    # ========================================================
    # ACHIEVEMENT POPUP
    # ========================================================

    def draw_achievement_popup(
        self,
    ) -> None:
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
            fill=(
                35,
                26,
                8,
            ),
            border=YELLOW,
            width=3,
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
            rect.top + 56,
            center=True,
        )

        draw_text(
            self.game_surface,
            self.tiny_font,
            get_achievement_description(
                self.current_achievement
            ),
            LIGHT_GREY,
            rect.centerx,
            rect.top + 87,
            center=True,
        )

    # ========================================================
    # MAIN LOOP
    # ========================================================

    async def run(
        self,
    ) -> None:
        while self.running:
            delta_time = min(
                0.05,

                self.clock.tick(
                    FPS
                )
                / 1000.0,
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

        self.storage.save_all()

        pygame.quit()


# ============================================================
# ENTRY POINT
# ============================================================

async def main(
) -> None:
    game = (
        TunnelRunnerGame()
    )

    await game.run()


if __name__ == "__main__":
    asyncio.run(
        main()
    )