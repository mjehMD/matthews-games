from __future__ import annotations

import asyncio
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import pygame

from config import (
    ACCOUNT_LOADING_MESSAGE,
    ACCOUNT_REQUIRED_MESSAGE,
    BACKGROUND_STAR_COUNT,
    BLACK,
    BLUE,
    BUTTON_CORNER_RADIUS,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
    CYAN,
    CYLINDER_BASE_COLOUR,
    CYLINDER_CENTER_X,
    CYLINDER_DARK_COLOUR,
    CYLINDER_FAR_RADIUS,
    CYLINDER_GLOW_COLOUR,
    CYLINDER_HORIZON_Y,
    CYLINDER_LANE_COLOUR,
    CYLINDER_LANE_COUNT,
    CYLINDER_NEAR_RADIUS,
    CYLINDER_PLAYER_Y,
    CYLINDER_RING_COLOUR,
    CYLINDER_RING_COUNT,
    CYLINDER_RING_SPACING,
    DARK_BLUE,
    DARK_GREY,
    DEEP_BLUE,
    DEFAULT_SAVE_DATA,
    DEFAULT_SETTINGS_DATA,
    ENABLE_GLOW_EFFECTS,
    ENDLESS_GENERATION_AHEAD_DISTANCE,
    ENDLESS_MAX_ACTIVE_OBSTACLES,
    ENDLESS_REMOVE_BEHIND_DISTANCE,
    ENDLESS_SAFE_START_DISTANCE,
    FPS,
    GAME_HEIGHT,
    GAME_TITLE,
    GAME_VERSION,
    GAME_WIDTH,
    GREEN,
    HEADING_FONT_SIZE,
    HUD_DISTANCE_POSITION,
    HUD_LEVEL_POSITION,
    HUD_SPEED_POSITION,
    LETTERBOX_COLOUR,
    LIGHT_BLUE,
    LIGHT_GREY,
    MAX_LEADERBOARD_ENTRIES,
    MODE_ENDLESS,
    MODE_LEVELS,
    NORMAL_FONT_SIZE,
    ORANGE,
    PANEL_BLUE,
    PANEL_CORNER_RADIUS,
    PLAYER_STARTING_ANGLE,
    PURPLE,
    RED,
    SAVE_FILE,
    SETTINGS_FILE,
    SHOW_VERSION_ON_MAIN_MENU,
    SMALL_FONT_SIZE,
    SPACE_BLACK,
    STATE_ACCOUNT_LOADING,
    STATE_ACCOUNT_REQUIRED,
    STATE_GAME_OVER,
    STATE_LEADERBOARD,
    STATE_LEVEL_COMPLETE,
    STATE_LEVEL_SELECT,
    STATE_MAIN_MENU,
    STATE_MODE_SELECT,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_SETTINGS,
    TINY_FONT_SIZE,
    TITLE_FONT_SIZE,
    TOTAL_LEVELS,
    UI_PANEL_ALPHA,
    VERSION_FONT_SIZE,
    WHITE,
    WINDOW_TITLE,
    YELLOW,
    calculate_endless_difficulty,
    calculate_endless_gap,
    calculate_endless_speed,
    ensure_project_directories,
    format_distance,
    format_version,
)
from entities import (
    Collectible,
    CylinderObstacle,
    EndlessObstacleFactory,
    GameplayWorld,
)
from levels import (
    CAMPAIGN_LEVELS,
    LevelDefinition,
    all_level_obstacles,
    get_level,
    get_next_level,
    is_level_unlocked,
    level_completion_percentage,
    unlock_level_after_completion,
)
from online_leaderboard import (
    leaderboard_distance_text,
    load_online_leaderboard,
    load_player_best_distance,
    submit_endless_distance,
)
from player_session import (
    PlayerSession,
    load_player_session,
)


IS_WEB = sys.platform in ("emscripten", "wasi")


# ============================================================
# DRAWING HELPERS
# ============================================================

def clamp_int(value: float, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


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


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: tuple[int, int, int] = DEEP_BLUE,
    border: tuple[int, int, int] = CYAN,
    border_width: int = 2,
    alpha: int = UI_PANEL_ALPHA,
) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(
        panel,
        (*fill, alpha),
        panel.get_rect(),
        border_radius=PANEL_CORNER_RADIUS,
    )
    pygame.draw.rect(
        panel,
        (*border, min(255, alpha + 10)),
        panel.get_rect(),
        width=border_width,
        border_radius=PANEL_CORNER_RADIUS,
    )
    surface.blit(panel, rect.topleft)


class Button:
    def __init__(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
        text: str,
        font: pygame.font.Font,
        *,
        accent: tuple[int, int, int] = CYAN,
        shortcut: str = "",
        enabled: bool = True,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.accent = accent
        self.shortcut = shortcut
        self.enabled = enabled
        self.hovered = False

    def update(self, mouse_position: tuple[int, int]) -> None:
        self.hovered = (
            self.enabled
            and self.rect.collidepoint(mouse_position)
        )

    def clicked(self, event: pygame.event.Event) -> bool:
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled:
            fill = DARK_GREY
            border = (75, 88, 115)
            text_colour = (135, 145, 165)
        elif self.hovered:
            fill = self.accent
            border = WHITE
            text_colour = SPACE_BLACK
        else:
            fill = PANEL_BLUE
            border = self.accent
            text_colour = WHITE

        shadow = self.rect.move(0, 7)
        pygame.draw.rect(
            surface,
            BLACK,
            shadow,
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

        if self.shortcut:
            draw_text(
                surface,
                pygame.font.Font(None, 17),
                self.shortcut,
                text_colour,
                self.rect.right - 10,
                self.rect.bottom - 20,
                right=True,
            )


# ============================================================
# SAVE MANAGER
# ============================================================

class SaveManager:
    def __init__(self):
        ensure_project_directories()
        self.data = dict(DEFAULT_SAVE_DATA)
        self.settings = dict(DEFAULT_SETTINGS_DATA)
        self.load()

    def _read_json(self, path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                result = dict(fallback)
                result.update(value)
                return result
        except (OSError, json.JSONDecodeError):
            pass
        return dict(fallback)

    def _write_json(self, path: Path, value: dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(value, indent=4),
                encoding="utf-8",
            )
        except OSError:
            pass

    def load(self) -> None:
        self.data = self._read_json(SAVE_FILE, DEFAULT_SAVE_DATA)
        self.settings = self._read_json(
            SETTINGS_FILE,
            DEFAULT_SETTINGS_DATA,
        )

    def save(self) -> None:
        self._write_json(SAVE_FILE, self.data)
        self._write_json(SETTINGS_FILE, self.settings)

    @property
    def highest_unlocked_level(self) -> int:
        try:
            return max(1, min(TOTAL_LEVELS, int(
                self.data.get("highest_unlocked_level", 1)
            )))
        except (TypeError, ValueError):
            return 1

    @property
    def endless_best_distance(self) -> int:
        try:
            return max(0, int(
                self.data.get("endless_best_distance", 0)
            ))
        except (TypeError, ValueError):
            return 0

    def record_endless_run(self, distance: float) -> int:
        cleaned = max(0, round(distance))

        self.data["total_runs"] = (
            int(self.data.get("total_runs", 0)) + 1
        )
        self.data["total_crashes"] = (
            int(self.data.get("total_crashes", 0)) + 1
        )
        self.data["total_distance"] = (
            int(self.data.get("total_distance", 0)) + cleaned
        )

        best = max(self.endless_best_distance, cleaned)
        self.data["endless_best_distance"] = best
        self.save()
        return best

    def record_level_completion(
        self,
        level_number: int,
        distance: float,
    ) -> None:
        completed = list(self.data.get("completed_levels", []))

        if level_number not in completed:
            completed.append(level_number)
            completed.sort()

        self.data["completed_levels"] = completed
        self.data["highest_unlocked_level"] = (
            unlock_level_after_completion(
                level_number,
                self.highest_unlocked_level,
            )
        )

        best_scores = dict(self.data.get("level_best_scores", {}))
        key = str(level_number)
        best_scores[key] = max(
            int(best_scores.get(key, 0)),
            round(distance),
        )
        self.data["level_best_scores"] = best_scores

        self.data["total_runs"] = (
            int(self.data.get("total_runs", 0)) + 1
        )
        self.data["total_distance"] = (
            int(self.data.get("total_distance", 0)) + round(distance)
        )
        self.save()


# ============================================================
# ENDLESS GENERATOR
# ============================================================

class EndlessManager:
    def __init__(self):
        self.factory = EndlessObstacleFactory()
        self.next_section_distance = ENDLESS_SAFE_START_DISTANCE
        self.section_count = 0

    def reset(self) -> None:
        self.factory.reset()
        self.next_section_distance = ENDLESS_SAFE_START_DISTANCE
        self.section_count = 0

    def update(self, world: GameplayWorld) -> None:
        furthest_distance = max(
            [obstacle.world_distance for obstacle in world.obstacles]
            + [0.0]
        )

        target = ENDLESS_GENERATION_AHEAD_DISTANCE

        while (
            furthest_distance < target
            and len(world.obstacles) < ENDLESS_MAX_ACTIVE_OBSTACLES
        ):
            difficulty = calculate_endless_difficulty(world.distance)

            section = self.factory.create_random_section(
                start_distance=max(
                    self.next_section_distance,
                    furthest_distance + calculate_endless_gap(world.distance),
                ),
                difficulty=difficulty,
                allow_moving=world.distance >= 350,
                allow_rotating=world.distance >= 650,
                allow_fake_gaps=world.distance >= 1000,
                allow_chasers=world.distance >= 2000,
            )

            for obstacle in section.obstacles:
                world.add_obstacle(obstacle)

            for collectible in section.collectibles:
                world.add_collectible(collectible)

            self.section_count += 1
            self.next_section_distance = (
                section.start_distance
                + section.length
                + calculate_endless_gap(world.distance)
            )
            furthest_distance = self.next_section_distance

        world.obstacles = [
            obstacle
            for obstacle in world.obstacles
            if obstacle.world_distance >= -ENDLESS_REMOVE_BEHIND_DISTANCE
        ]


# ============================================================
# MAIN GAME
# ============================================================

class OrbitRush:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.running = True
        self.fullscreen = False

        self.display_surface = pygame.display.set_mode(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT)
        ).convert()

        self.display_rect = pygame.Rect(
            0,
            0,
            GAME_WIDTH,
            GAME_HEIGHT,
        )
        self.display_scale = 1.0
        self.update_display_layout()

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.heading_font = pygame.font.Font(None, HEADING_FONT_SIZE)
        self.normal_font = pygame.font.Font(None, NORMAL_FONT_SIZE)
        self.small_font = pygame.font.Font(None, SMALL_FONT_SIZE)
        self.tiny_font = pygame.font.Font(None, TINY_FONT_SIZE)
        self.version_font = pygame.font.Font(None, VERSION_FONT_SIZE)

        self.title_font.set_bold(True)
        self.heading_font.set_bold(True)
        self.normal_font.set_bold(True)

        self.save_manager = SaveManager()

        self.session = PlayerSession(
            message=ACCOUNT_LOADING_MESSAGE
        )
        self.session_task: asyncio.Task | None = asyncio.create_task(
            load_player_session()
        )

        self.state = STATE_ACCOUNT_LOADING
        self.previous_state = STATE_MAIN_MENU

        self.game_mode = MODE_ENDLESS
        self.selected_level_number = 1
        self.current_level: LevelDefinition | None = None

        self.world = GameplayWorld()
        self.endless_manager = EndlessManager()

        self.run_started_at = 0
        self.run_finished_at = 0

        self.status_message = ""
        self.status_until = 0

        self.personal_best = self.save_manager.endless_best_distance
        self.personal_best_task: asyncio.Task | None = None

        self.leaderboard: list[dict[str, Any]] = []
        self.leaderboard_task: asyncio.Task | None = None
        self.score_submit_task: asyncio.Task | None = None
        self.leaderboard_status = "Leaderboard not loaded."

        self.level_page = 0
        self.levels_per_page = 10

        self.stars = [
            (
                random.randrange(GAME_WIDTH),
                random.randrange(GAME_HEIGHT),
                random.choice((1, 1, 1, 2)),
                random.uniform(8.0, 32.0),
            )
            for _ in range(BACKGROUND_STAR_COUNT)
        ]

        self.create_buttons()

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    def update_display_layout(self) -> None:
        width = max(1, self.display_surface.get_width())
        height = max(1, self.display_surface.get_height())

        scale = min(
            width / GAME_WIDTH,
            height / GAME_HEIGHT,
        )

        self.display_scale = max(0.1, scale)

        rendered_size = (
            max(1, round(GAME_WIDTH * self.display_scale)),
            max(1, round(GAME_HEIGHT * self.display_scale)),
        )

        self.display_rect = pygame.Rect(
            (width - rendered_size[0]) // 2,
            (height - rendered_size[1]) // 2,
            rendered_size[0],
            rendered_size[1],
        )

    def display_to_game_position(
        self,
        position: tuple[int, int],
    ) -> tuple[int, int]:
        if not self.display_rect.collidepoint(position):
            return (-10000, -10000)

        return (
            round(
                (position[0] - self.display_rect.x)
                / self.display_scale
            ),
            round(
                (position[1] - self.display_rect.y)
                / self.display_scale
            ),
        )

    def convert_mouse_event(
        self,
        event: pygame.event.Event,
    ) -> pygame.event.Event:
        if not hasattr(event, "pos"):
            return event

        event_data = dict(event.dict)
        event_data["pos"] = self.display_to_game_position(event.pos)
        return pygame.event.Event(event.type, event_data)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            info = pygame.display.Info()
            self.display_surface = pygame.display.set_mode(
                (info.current_w, info.current_h),
                pygame.FULLSCREEN,
            )
        else:
            self.display_surface = pygame.display.set_mode(
                (GAME_WIDTH, GAME_HEIGHT),
                pygame.RESIZABLE,
            )

        self.update_display_layout()

    def present(self) -> None:
        self.display_surface.fill(LETTERBOX_COLOUR)

        if self.display_rect.size == (GAME_WIDTH, GAME_HEIGHT):
            image = self.screen
        else:
            image = pygame.transform.smoothscale(
                self.screen,
                self.display_rect.size,
            )

        shaken_rect = self.display_rect.move(
            round(self.world.screen_shake.offset.x * self.display_scale),
            round(self.world.screen_shake.offset.y * self.display_scale),
        )

        self.display_surface.blit(image, shaken_rect.topleft)
        pygame.display.flip()

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    def create_buttons(self) -> None:
        center_x = GAME_WIDTH // 2 - BUTTON_WIDTH // 2

        self.levels_button = Button(
            (center_x, 360, BUTTON_WIDTH, BUTTON_HEIGHT),
            "LEVELS",
            self.normal_font,
            accent=LIGHT_BLUE,
            shortcut="L",
        )

        self.endless_button = Button(
            (center_x, 480, BUTTON_WIDTH, BUTTON_HEIGHT),
            "ENDLESS",
            self.normal_font,
            accent=CYAN,
            shortcut="E",
        )

        self.leaderboard_button = Button(
            (center_x, 575, BUTTON_WIDTH, BUTTON_HEIGHT),
            "LEADERBOARD",
            self.normal_font,
            accent=YELLOW,
            shortcut="B",
        )

        self.settings_button = Button(
            (36, GAME_HEIGHT - 82, 210, 50),
            "SETTINGS",
            self.small_font,
            accent=PURPLE,
        )

        self.back_button = Button(
            (30, 28, 170, 48),
            "BACK",
            self.small_font,
            accent=LIGHT_BLUE,
            shortcut="ESC",
        )

        self.pause_resume_button = Button(
            (GAME_WIDTH // 2 - 165, 330, 330, 62),
            "RESUME",
            self.normal_font,
            accent=GREEN,
        )

        self.pause_restart_button = Button(
            (GAME_WIDTH // 2 - 165, 420, 330, 62),
            "RESTART",
            self.normal_font,
            accent=YELLOW,
        )

        self.pause_menu_button = Button(
            (GAME_WIDTH // 2 - 165, 510, 330, 62),
            "MAIN MENU",
            self.normal_font,
            accent=RED,
        )

        self.retry_button = Button(
            (GAME_WIDTH // 2 - 165, 470, 330, 62),
            "TRY AGAIN",
            self.normal_font,
            accent=CYAN,
        )

        self.game_over_menu_button = Button(
            (GAME_WIDTH // 2 - 165, 555, 330, 62),
            "MAIN MENU",
            self.normal_font,
            accent=LIGHT_BLUE,
        )

        self.next_level_button = Button(
            (GAME_WIDTH // 2 - 165, 470, 330, 62),
            "NEXT LEVEL",
            self.normal_font,
            accent=GREEN,
        )

        self.level_complete_menu_button = Button(
            (GAME_WIDTH // 2 - 165, 555, 330, 62),
            "LEVEL SELECT",
            self.normal_font,
            accent=LIGHT_BLUE,
        )

    def all_buttons(self) -> list[Button]:
        buttons = [
            self.levels_button,
            self.endless_button,
            self.leaderboard_button,
            self.settings_button,
            self.back_button,
            self.pause_resume_button,
            self.pause_restart_button,
            self.pause_menu_button,
            self.retry_button,
            self.game_over_menu_button,
            self.next_level_button,
            self.level_complete_menu_button,
        ]

        buttons.extend(self.level_buttons())
        return buttons

    def level_buttons(self) -> list[Button]:
        buttons: list[Button] = []

        start = self.level_page * self.levels_per_page
        end = min(TOTAL_LEVELS, start + self.levels_per_page)

        for index, level_number in enumerate(range(start + 1, end + 1)):
            column = index % 5
            row = index // 5

            rect = pygame.Rect(
                120 + column * 195,
                265 + row * 150,
                165,
                105,
            )

            level = get_level(level_number)
            unlocked = is_level_unlocked(
                level_number,
                self.save_manager.highest_unlocked_level,
            )

            buttons.append(
                Button(
                    rect,
                    f"{level_number}",
                    self.heading_font,
                    accent=(
                        GREEN
                        if level_number in self.save_manager.data.get(
                            "completed_levels",
                            []
                        )
                        else CYAN
                    ),
                    enabled=unlocked,
                )
            )

        return buttons

    def update_button_hovers(self) -> None:
        mouse = self.display_to_game_position(
            pygame.mouse.get_pos()
        )

        for button in self.all_buttons():
            button.update(mouse)

    # --------------------------------------------------------
    # ACCOUNT / ONLINE TASKS
    # --------------------------------------------------------

    def update_account_task(self) -> None:
        if self.session_task is None or not self.session_task.done():
            return

        try:
            self.session = self.session_task.result()
        except Exception as error:
            self.session = PlayerSession(
                message=f"Account error: {error}"
            )

        self.session_task = None

        if self.session.signed_in:
            self.state = STATE_MAIN_MENU
            self.start_personal_best_load()
            self.start_leaderboard_load()
        else:
            self.state = STATE_ACCOUNT_REQUIRED

    def start_personal_best_load(self) -> None:
        if not self.session.signed_in:
            return

        if (
            self.personal_best_task is not None
            and not self.personal_best_task.done()
        ):
            return

        self.personal_best_task = asyncio.create_task(
            load_player_best_distance(
                self.session.user_id,
                self.session.access_token,
            )
        )

    def start_leaderboard_load(self) -> None:
        if (
            self.leaderboard_task is not None
            and not self.leaderboard_task.done()
        ):
            return

        self.leaderboard_status = "Loading leaderboard..."
        self.leaderboard_task = asyncio.create_task(
            load_online_leaderboard()
        )

    def start_score_submit(self, distance: float) -> None:
        if not self.session.signed_in:
            return

        if (
            self.score_submit_task is not None
            and not self.score_submit_task.done()
        ):
            return

        self.leaderboard_status = "Saving distance online..."

        self.score_submit_task = asyncio.create_task(
            submit_endless_distance(
                self.session.username,
                distance,
                self.session.user_id,
                self.session.access_token,
            )
        )

    def update_online_tasks(self) -> None:
        if (
            self.personal_best_task is not None
            and self.personal_best_task.done()
        ):
            try:
                distance, _message = self.personal_best_task.result()
                self.personal_best = max(
                    self.personal_best,
                    distance,
                )
            except Exception:
                pass

            self.personal_best_task = None

        if (
            self.leaderboard_task is not None
            and self.leaderboard_task.done()
        ):
            try:
                scores, message = self.leaderboard_task.result()
                self.leaderboard = scores
                self.leaderboard_status = message
            except Exception as error:
                self.leaderboard_status = f"Leaderboard error: {error}"

            self.leaderboard_task = None

        if (
            self.score_submit_task is not None
            and self.score_submit_task.done()
        ):
            try:
                success, message, saved_best = (
                    self.score_submit_task.result()
                )
                self.leaderboard_status = message

                if success:
                    self.personal_best = max(
                        self.personal_best,
                        saved_best,
                    )
                    self.start_leaderboard_load()
            except Exception as error:
                self.leaderboard_status = f"Save error: {error}"

            self.score_submit_task = None

    # --------------------------------------------------------
    # GAME START / END
    # --------------------------------------------------------

    def start_endless(self) -> None:
        self.game_mode = MODE_ENDLESS
        self.current_level = None
        self.world.reset(calculate_endless_speed(0))
        self.endless_manager.reset()
        self.endless_manager.update(self.world)
        self.run_started_at = pygame.time.get_ticks()
        self.state = STATE_PLAYING

    def start_level(self, level_number: int) -> None:
        if not is_level_unlocked(
            level_number,
            self.save_manager.highest_unlocked_level,
        ):
            return

        self.game_mode = MODE_LEVELS
        self.selected_level_number = level_number
        self.current_level = get_level(level_number)

        self.world.reset(
            self.current_level.starting_speed,
            PLAYER_STARTING_ANGLE,
        )

        for absolute_distance, pattern_obstacle in all_level_obstacles(
            level_number
        ):
            self.world.add_pattern_obstacle(
                pattern_obstacle,
                absolute_distance,
            )

        self.run_started_at = pygame.time.get_ticks()
        self.state = STATE_PLAYING

    def restart_current_run(self) -> None:
        if self.game_mode == MODE_ENDLESS:
            self.start_endless()
        else:
            self.start_level(self.selected_level_number)

    def finish_crash(self) -> None:
        if self.state != STATE_PLAYING:
            return

        self.run_finished_at = pygame.time.get_ticks()

        if self.game_mode == MODE_ENDLESS:
            self.personal_best = self.save_manager.record_endless_run(
                self.world.distance
            )
            self.start_score_submit(self.world.distance)

        self.state = STATE_GAME_OVER

    def finish_level(self) -> None:
        if self.state != STATE_PLAYING or self.current_level is None:
            return

        self.run_finished_at = pygame.time.get_ticks()

        self.save_manager.record_level_completion(
            self.current_level.number,
            self.world.distance,
        )

        self.state = STATE_LEVEL_COMPLETE

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        event = self.convert_mouse_event(event)

        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.display_surface = pygame.display.set_mode(
                event.size,
                pygame.RESIZABLE,
            )
            self.update_display_layout()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
                return

            if event.key == pygame.K_ESCAPE:
                if self.state == STATE_PLAYING:
                    self.previous_state = self.state
                    self.state = STATE_PAUSED
                    return

                if self.state == STATE_PAUSED:
                    self.state = STATE_PLAYING
                    return

                if self.state in (
                    STATE_LEVEL_SELECT,
                    STATE_LEADERBOARD,
                    STATE_SETTINGS,
                ):
                    self.state = STATE_MAIN_MENU
                    return

        if self.state in (
            STATE_ACCOUNT_LOADING,
            STATE_ACCOUNT_REQUIRED,
        ):
            return

        if self.state == STATE_MAIN_MENU:
            self.handle_main_menu(event)
        elif self.state == STATE_LEVEL_SELECT:
            self.handle_level_select(event)
        elif self.state == STATE_PLAYING:
            self.handle_playing(event)
        elif self.state == STATE_PAUSED:
            self.handle_paused(event)
        elif self.state == STATE_GAME_OVER:
            self.handle_game_over(event)
        elif self.state == STATE_LEVEL_COMPLETE:
            self.handle_level_complete(event)
        elif self.state == STATE_LEADERBOARD:
            self.handle_leaderboard(event)
        elif self.state == STATE_SETTINGS:
            self.handle_settings(event)

    def handle_main_menu(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                self.state = STATE_LEVEL_SELECT
            elif event.key == pygame.K_e:
                self.start_endless()
            elif event.key == pygame.K_b:
                self.state = STATE_LEADERBOARD
                self.start_leaderboard_load()

        if self.levels_button.clicked(event):
            self.state = STATE_LEVEL_SELECT
        elif self.endless_button.clicked(event):
            self.start_endless()
        elif self.leaderboard_button.clicked(event):
            self.state = STATE_LEADERBOARD
            self.start_leaderboard_load()
        elif self.settings_button.clicked(event):
            self.state = STATE_SETTINGS

    def handle_level_select(self, event: pygame.event.Event) -> None:
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEUP:
                self.level_page = max(0, self.level_page - 1)
            elif event.key == pygame.K_PAGEDOWN:
                self.level_page = min(4, self.level_page + 1)
            elif event.key == pygame.K_LEFT:
                self.level_page = max(0, self.level_page - 1)
            elif event.key == pygame.K_RIGHT:
                self.level_page = min(4, self.level_page + 1)

        start = self.level_page * self.levels_per_page

        for index, button in enumerate(self.level_buttons()):
            if button.clicked(event):
                self.start_level(start + index + 1)
                break

    def handle_playing(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_p,
            pygame.K_ESCAPE,
        ):
            self.state = STATE_PAUSED

    def handle_paused(self, event: pygame.event.Event) -> None:
        if self.pause_resume_button.clicked(event):
            self.state = STATE_PLAYING
        elif self.pause_restart_button.clicked(event):
            self.restart_current_run()
        elif self.pause_menu_button.clicked(event):
            self.state = STATE_MAIN_MENU

    def handle_game_over(self, event: pygame.event.Event) -> None:
        if self.retry_button.clicked(event):
            self.restart_current_run()
        elif self.game_over_menu_button.clicked(event):
            self.state = STATE_MAIN_MENU

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.restart_current_run()
            elif event.key == pygame.K_m:
                self.state = STATE_MAIN_MENU

    def handle_level_complete(self, event: pygame.event.Event) -> None:
        next_level = (
            get_next_level(self.selected_level_number)
            if self.current_level is not None
            else None
        )

        self.next_level_button.enabled = next_level is not None

        if self.next_level_button.clicked(event) and next_level is not None:
            self.start_level(next_level.number)
        elif self.level_complete_menu_button.clicked(event):
            self.state = STATE_LEVEL_SELECT

    def handle_leaderboard(self, event: pygame.event.Event) -> None:
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.start_leaderboard_load()

    def handle_settings(self, event: pygame.event.Event) -> None:
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU

    # --------------------------------------------------------
    # UPDATES
    # --------------------------------------------------------

    def update(self, delta_time: float, current_time: int) -> None:
        self.update_account_task()
        self.update_online_tasks()
        self.update_button_hovers()

        if self.state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()

        direction = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction += 1

        self.world.set_rotation_input(direction)

        if self.game_mode == MODE_ENDLESS:
            self.world.forward_speed = calculate_endless_speed(
                self.world.distance
            )
            self.endless_manager.update(self.world)
        elif self.current_level is not None:
            self.world.forward_speed = min(
                self.current_level.maximum_speed,
                self.current_level.starting_speed
                + self.current_level.acceleration
                * self.world.distance,
            )

        events = self.world.update(
            delta_time,
            current_time,
        )

        for gameplay_event in events:
            event_type = gameplay_event.get("type")

            if event_type == "crash":
                self.finish_crash()
                break

            if event_type == "finish":
                self.finish_level()
                break

    # --------------------------------------------------------
    # BACKGROUND / CYLINDER
    # --------------------------------------------------------

    def draw_background(self, current_time: int) -> None:
        self.screen.fill(SPACE_BLACK)

        for index, star in enumerate(self.stars):
            x, y, radius, speed = star

            shifted_y = (
                y
                + current_time
                * 0.001
                * speed
            ) % GAME_HEIGHT

            brightness = 110 + (index * 17) % 145

            pygame.draw.circle(
                self.screen,
                (brightness, brightness, min(255, brightness + 20)),
                (round(x), round(shifted_y)),
                radius,
            )

        pygame.draw.circle(
            self.screen,
            (16, 34, 78),
            (GAME_WIDTH // 2, CYLINDER_HORIZON_Y - 10),
            165,
        )
        pygame.draw.circle(
            self.screen,
            (36, 88, 160),
            (GAME_WIDTH // 2, CYLINDER_HORIZON_Y - 10),
            165,
            width=3,
        )

    def draw_cylinder(self) -> None:
        projector = self.world.projector

        # Filled cylinder bands.
        band_points: list[list[tuple[int, int]]] = []

        samples = 48

        for ring_index in range(CYLINDER_RING_COUNT):
            distance = min(
                projector.visible_distance,
                ring_index * CYLINDER_RING_SPACING,
            )

            points: list[tuple[int, int]] = []

            for sample in range(samples + 1):
                angle = sample / samples * 360.0
                projection = projector.project(angle, distance)

                points.append(
                    (round(projection.x), round(projection.y))
                )

            band_points.append(points)

        for index in range(len(band_points) - 1, 0, -1):
            first = band_points[index]
            second = band_points[index - 1]

            colour = (
                CYLINDER_DARK_COLOUR
                if index % 2
                else CYLINDER_BASE_COLOUR
            )

            for sample in range(samples):
                polygon = [
                    first[sample],
                    first[sample + 1],
                    second[sample + 1],
                    second[sample],
                ]
                pygame.draw.polygon(self.screen, colour, polygon)

        # Rings.
        for ring_index, points in enumerate(band_points):
            colour = (
                CYLINDER_GLOW_COLOUR
                if ring_index % 5 == 0
                else CYLINDER_RING_COLOUR
            )
            width = 2 if ring_index % 5 == 0 else 1
            pygame.draw.lines(
                self.screen,
                colour,
                False,
                points,
                width=width,
            )

        # Lane lines.
        for lane in range(CYLINDER_LANE_COUNT):
            points: list[tuple[int, int]] = []

            for ring_index in range(CYLINDER_RING_COUNT):
                distance = min(
                    projector.visible_distance,
                    ring_index * CYLINDER_RING_SPACING,
                )
                projection = projector.project_lane(lane, distance)
                points.append((round(projection.x), round(projection.y)))

            pygame.draw.lines(
                self.screen,
                CYLINDER_LANE_COLOUR,
                False,
                points,
                width=2 if lane % 3 == 0 else 1,
            )

        if ENABLE_GLOW_EFFECTS:
            pygame.draw.ellipse(
                self.screen,
                CYLINDER_GLOW_COLOUR,
                pygame.Rect(
                    CYLINDER_CENTER_X - round(CYLINDER_FAR_RADIUS),
                    CYLINDER_HORIZON_Y - 12,
                    round(CYLINDER_FAR_RADIUS * 2),
                    24,
                ),
                width=2,
            )

    # --------------------------------------------------------
    # STATE DRAWING
    # --------------------------------------------------------

    def draw(self, current_time: int) -> None:
        self.draw_background(current_time)

        if self.state in (
            STATE_PLAYING,
            STATE_PAUSED,
            STATE_GAME_OVER,
            STATE_LEVEL_COMPLETE,
        ):
            self.draw_cylinder()
            self.world.draw_entities(
                self.screen,
                self.tiny_font,
                current_time,
            )
            self.draw_hud(current_time)

        if self.state == STATE_ACCOUNT_LOADING:
            self.draw_account_screen(True)
        elif self.state == STATE_ACCOUNT_REQUIRED:
            self.draw_account_screen(False)
        elif self.state == STATE_MAIN_MENU:
            self.draw_main_menu()
        elif self.state == STATE_LEVEL_SELECT:
            self.draw_level_select()
        elif self.state == STATE_PAUSED:
            self.draw_pause()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        elif self.state == STATE_LEVEL_COMPLETE:
            self.draw_level_complete()
        elif self.state == STATE_LEADERBOARD:
            self.draw_leaderboard()
        elif self.state == STATE_SETTINGS:
            self.draw_settings()

    def draw_account_screen(self, loading: bool) -> None:
        panel = pygame.Rect(
            GAME_WIDTH // 2 - 390,
            GAME_HEIGHT // 2 - 180,
            780,
            360,
        )

        draw_panel(
            self.screen,
            panel,
            fill=DEEP_BLUE,
            border=CYAN if loading else RED,
            border_width=3,
        )

        draw_text(
            self.screen,
            self.title_font,
            GAME_TITLE,
            WHITE,
            GAME_WIDTH // 2,
            panel.top + 75,
            center=True,
        )

        draw_text(
            self.screen,
            self.heading_font,
            "CHECKING ACCOUNT" if loading else "SIGN IN REQUIRED",
            CYAN if loading else YELLOW,
            GAME_WIDTH // 2,
            panel.top + 150,
            center=True,
        )

        draw_text(
            self.screen,
            self.normal_font,
            self.session.message,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            panel.top + 225,
            center=True,
        )

        if not loading:
            draw_text(
                self.screen,
                self.small_font,
                ACCOUNT_REQUIRED_MESSAGE,
                WHITE,
                GAME_WIDTH // 2,
                panel.top + 285,
                center=True,
            )

    def draw_main_menu(self) -> None:
        draw_text(
            self.screen,
            self.title_font,
            GAME_TITLE.upper(),
            WHITE,
            GAME_WIDTH // 2,
            105,
            center=True,
        )

        draw_text(
            self.screen,
            self.normal_font,
            f"Runner: {self.session.username}",
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            180,
            center=True,
        )

        draw_text(
            self.screen,
            self.small_font,
            "Rotate the cylinder. Avoid everything. Keep running.",
            LIGHT_GREY,
            GAME_WIDTH // 2,
            225,
            center=True,
        )

        self.levels_button.draw(self.screen)

        draw_text(
            self.screen,
            self.small_font,
            f"Your All-Time Best: {format_distance(self.personal_best)}",
            YELLOW,
            GAME_WIDTH // 2,
            self.endless_button.rect.top - 25,
            center=True,
        )

        self.endless_button.draw(self.screen)
        self.leaderboard_button.draw(self.screen)
        self.settings_button.draw(self.screen)

        draw_text(
            self.screen,
            self.tiny_font,
            "A / D or Left / Right to rotate",
            LIGHT_GREY,
            GAME_WIDTH // 2,
            680,
            center=True,
        )

        if SHOW_VERSION_ON_MAIN_MENU:
            draw_text(
                self.screen,
                self.version_font,
                format_version(),
                LIGHT_GREY,
                GAME_WIDTH - 18,
                GAME_HEIGHT - 28,
                right=True,
            )

    def draw_level_select(self) -> None:
        self.back_button.draw(self.screen)

        draw_text(
            self.screen,
            self.title_font,
            "SELECT LEVEL",
            WHITE,
            GAME_WIDTH // 2,
            90,
            center=True,
        )

        draw_text(
            self.screen,
            self.small_font,
            (
                f"Unlocked: {self.save_manager.highest_unlocked_level}"
                f" / {TOTAL_LEVELS}"
            ),
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            160,
            center=True,
        )

        page_start = self.level_page * self.levels_per_page + 1
        page_end = min(TOTAL_LEVELS, page_start + 9)

        draw_text(
            self.screen,
            self.small_font,
            f"Levels {page_start}-{page_end}",
            LIGHT_GREY,
            GAME_WIDTH // 2,
            205,
            center=True,
        )

        for button in self.level_buttons():
            button.draw(self.screen)

            level_number = (
                self.level_page * self.levels_per_page
                + self.level_buttons().index(button)
                + 1
            )

            level = get_level(level_number)

            draw_text(
                self.screen,
                self.tiny_font,
                level.name,
                LIGHT_GREY if button.enabled else DARK_GREY,
                button.rect.centerx,
                button.rect.bottom + 19,
                center=True,
            )

        draw_text(
            self.screen,
            self.small_font,
            "Left / Right or Page Up / Page Down",
            LIGHT_GREY,
            GAME_WIDTH // 2,
            680,
            center=True,
        )

    def draw_hud(self, current_time: int) -> None:
        panel = pygame.Rect(18, 16, 320, 112)
        draw_panel(
            self.screen,
            panel,
            fill=(6, 18, 44),
            border=CYAN,
            alpha=215,
        )

        draw_text(
            self.screen,
            self.normal_font,
            format_distance(self.world.distance),
            WHITE,
            *HUD_DISTANCE_POSITION,
        )

        draw_text(
            self.screen,
            self.small_font,
            f"Speed: {self.world.forward_speed:.1f}",
            LIGHT_BLUE,
            *HUD_SPEED_POSITION,
        )

        if self.game_mode == MODE_LEVELS and self.current_level is not None:
            draw_text(
                self.screen,
                self.normal_font,
                f"Level {self.current_level.number}",
                WHITE,
                HUD_LEVEL_POSITION[0],
                HUD_LEVEL_POSITION[1],
                right=True,
            )

            completion_percentage = level_completion_percentage(
                self.world.distance,
                self.current_level.number,
            )

            draw_text(
                self.screen,
                self.small_font,
                f"{completion_percentage:.0f}%",
                LIGHT_BLUE,
                HUD_LEVEL_POSITION[0],
                HUD_LEVEL_POSITION[1] + 40,
                right=True,
            )
        else:
            draw_text(
                self.screen,
                self.normal_font,
                "ENDLESS",
                YELLOW,
                HUD_LEVEL_POSITION[0],
                HUD_LEVEL_POSITION[1],
                right=True,
            )

            draw_text(
                self.screen,
                self.small_font,
                f"Best: {format_distance(self.personal_best)}",
                LIGHT_BLUE,
                HUD_LEVEL_POSITION[0],
                HUD_LEVEL_POSITION[1] + 40,
                right=True,
            )

    def draw_pause(self) -> None:
        overlay = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        draw_text(
            self.screen,
            self.title_font,
            "PAUSED",
            WHITE,
            GAME_WIDTH // 2,
            210,
            center=True,
        )

        self.pause_resume_button.draw(self.screen)
        self.pause_restart_button.draw(self.screen)
        self.pause_menu_button.draw(self.screen)

    def draw_game_over(self) -> None:
        overlay = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        draw_text(
            self.screen,
            self.title_font,
            "RUN ENDED",
            RED,
            GAME_WIDTH // 2,
            160,
            center=True,
        )

        draw_text(
            self.screen,
            self.heading_font,
            format_distance(self.world.distance),
            WHITE,
            GAME_WIDTH // 2,
            260,
            center=True,
        )

        if self.game_mode == MODE_ENDLESS:
            draw_text(
                self.screen,
                self.normal_font,
                f"All-Time Best: {format_distance(self.personal_best)}",
                YELLOW,
                GAME_WIDTH // 2,
                335,
                center=True,
            )
        elif self.current_level is not None:
            draw_text(
                self.screen,
                self.normal_font,
                f"Level {self.current_level.number}: {self.current_level.name}",
                LIGHT_BLUE,
                GAME_WIDTH // 2,
                335,
                center=True,
            )

        self.retry_button.draw(self.screen)
        self.game_over_menu_button.draw(self.screen)

    def draw_level_complete(self) -> None:
        overlay = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        draw_text(
            self.screen,
            self.title_font,
            "LEVEL COMPLETE",
            GREEN,
            GAME_WIDTH // 2,
            150,
            center=True,
        )

        if self.current_level is not None:
            draw_text(
                self.screen,
                self.heading_font,
                f"Level {self.current_level.number}: {self.current_level.name}",
                WHITE,
                GAME_WIDTH // 2,
                250,
                center=True,
            )

            draw_text(
                self.screen,
                self.normal_font,
                format_distance(self.current_level.length),
                LIGHT_BLUE,
                GAME_WIDTH // 2,
                320,
                center=True,
            )

        self.next_level_button.draw(self.screen)
        self.level_complete_menu_button.draw(self.screen)

    def draw_leaderboard(self) -> None:
        self.back_button.draw(self.screen)

        draw_text(
            self.screen,
            self.title_font,
            "ENDLESS LEADERBOARD",
            WHITE,
            GAME_WIDTH // 2,
            80,
            center=True,
        )

        draw_text(
            self.screen,
            self.small_font,
            f"Your Best: {format_distance(self.personal_best)}",
            YELLOW,
            GAME_WIDTH // 2,
            145,
            center=True,
        )

        panel = pygame.Rect(180, 190, 840, 450)
        draw_panel(
            self.screen,
            panel,
            fill=(7, 20, 50),
            border=CYAN,
        )

        if not self.leaderboard:
            draw_text(
                self.screen,
                self.normal_font,
                self.leaderboard_status,
                LIGHT_GREY,
                panel.centerx,
                panel.centery,
                center=True,
            )
            return

        for rank, entry in enumerate(
            self.leaderboard[:MAX_LEADERBOARD_ENTRIES],
            start=1,
        ):
            y = panel.top + 34 + (rank - 1) * 39

            rank_colour = (
                YELLOW
                if rank == 1
                else LIGHT_BLUE
                if rank <= 3
                else WHITE
            )

            draw_text(
                self.screen,
                self.normal_font,
                f"{rank}.",
                rank_colour,
                panel.left + 35,
                y,
            )

            draw_text(
                self.screen,
                self.normal_font,
                str(entry.get("name", "Player")),
                WHITE,
                panel.left + 105,
                y,
            )

            draw_text(
                self.screen,
                self.normal_font,
                leaderboard_distance_text(
                    entry.get("distance", 0)
                ),
                rank_colour,
                panel.right - 40,
                y,
                right=True,
            )

        draw_text(
            self.screen,
            self.tiny_font,
            "Press R to refresh",
            LIGHT_GREY,
            GAME_WIDTH // 2,
            675,
            center=True,
        )

    def draw_settings(self) -> None:
        self.back_button.draw(self.screen)

        draw_text(
            self.screen,
            self.title_font,
            "SETTINGS",
            WHITE,
            GAME_WIDTH // 2,
            110,
            center=True,
        )

        panel = pygame.Rect(
            GAME_WIDTH // 2 - 360,
            205,
            720,
            390,
        )
        draw_panel(self.screen, panel)

        draw_text(
            self.screen,
            self.heading_font,
            "Controls",
            CYAN,
            panel.centerx,
            panel.top + 60,
            center=True,
        )

        lines = (
            "A / Left Arrow: Rotate left",
            "D / Right Arrow: Rotate right",
            "Escape / P: Pause",
            "F11: Fullscreen",
            "Endless Mode alone counts toward the leaderboard",
        )

        for index, line in enumerate(lines):
            draw_text(
                self.screen,
                self.normal_font,
                line,
                WHITE if index < 4 else YELLOW,
                panel.centerx,
                panel.top + 125 + index * 52,
                center=True,
            )

        draw_text(
            self.screen,
            self.version_font,
            format_version(),
            LIGHT_GREY,
            GAME_WIDTH - 18,
            GAME_HEIGHT - 28,
            right=True,
        )

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    async def run(self) -> None:
        while self.running:
            delta_time = min(
                0.05,
                self.clock.tick(FPS) / 1000.0,
            )
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(delta_time, current_time)
            self.draw(current_time)
            self.present()

            await asyncio.sleep(0)

        self.save_manager.save()
        pygame.quit()


async def main() -> None:
    game = OrbitRush()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
