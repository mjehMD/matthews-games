from __future__ import annotations

import asyncio
import math
import random
import sys
from typing import Any

import pygame

from config import (
    BLACK, BLUE, CAMPAIGN_LEVELS, CYAN, DEEP_BLUE, DEFAULT_SETTINGS,
    ENDLESS_GENERATE_AHEAD, ENDLESS_MAX_SPEED, ENDLESS_SPEED_PER_100M,
    ENDLESS_START_SPEED, FPS, GAME_HEIGHT, GAME_TITLE, GAME_VERSION, GAME_WIDTH,
    GREEN, GREY, LIGHT_GREY, MAX_ACTIVE_OBSTACLES, MAX_LEADERBOARD_ENTRIES,
    ORANGE, PANEL, PANEL_2, PINK, PURPLE, RED, SPACE, TUNNEL_CENTER_X,
    TUNNEL_CENTER_Y, TUNNEL_FAR_RADIUS, TUNNEL_NEAR_RADIUS, TUNNEL_SIDES,
    TUNNEL_THEMES, VISIBLE_DISTANCE, WHITE, WINDOW_TITLE, YELLOW, clamp,
    colour_lerp, format_distance, normalize_angle,
)
from entities import TunnelObstacle, TunnelWorld
from levels import CAMPAIGN, EndlessGenerator, get_level, instantiate_level
from online_leaderboard import (
    load_online_leaderboard,
    load_player_best_distance,
    submit_endless_distance,
)
from player_session import PlayerSession, load_player_session
from storage import SaveManager

IS_WEB = sys.platform in ("emscripten", "wasi")

STATE_ACCOUNT_LOADING = "account_loading"
STATE_ACCOUNT_REQUIRED = "account_required"
STATE_MENU = "menu"
STATE_LEVEL_SELECT = "level_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_LEADERBOARD = "leaderboard"
STATE_HELP = "help"
STATE_SETTINGS = "settings"

MODE_LEVELS = "levels"
MODE_ENDLESS = "endless"


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
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
    fill: tuple[int, int, int] = PANEL,
    border: tuple[int, int, int] = CYAN,
    alpha: int = 235,
    border_width: int = 2,
) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*fill, alpha), panel.get_rect(), border_radius=18)
    pygame.draw.rect(
        panel,
        (*border, min(255, alpha + 10)),
        panel.get_rect(),
        width=border_width,
        border_radius=18,
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
        enabled: bool = True,
        shortcut: str = "",
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.accent = accent
        self.enabled = enabled
        self.shortcut = shortcut
        self.hovered = False

    def update(self, mouse_position: tuple[int, int]) -> None:
        self.hovered = self.enabled and self.rect.collidepoint(mouse_position)

    def clicked(self, event: pygame.event.Event) -> bool:
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled:
            fill = (45, 50, 65)
            border = (85, 92, 110)
            text_colour = (130, 138, 155)
        elif self.hovered:
            fill = self.accent
            border = WHITE
            text_colour = BLACK
        else:
            fill = PANEL_2
            border = self.accent
            text_colour = WHITE

        pygame.draw.rect(surface, BLACK, self.rect.move(0, 6), border_radius=14)
        pygame.draw.rect(surface, fill, self.rect, border_radius=14)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=14)
        draw_text(
            surface,
            self.text,
            self.font,
            text_colour,
            self.rect.centerx,
            self.rect.centery,
            center=True,
        )
        if self.shortcut:
            draw_text(
                surface,
                self.shortcut,
                pygame.font.Font(None, 17),
                text_colour,
                self.rect.right - 10,
                self.rect.bottom - 19,
                right=True,
            )


class OrbitRush:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()

        self.running = True
        self.fullscreen = False
        self.display_surface = pygame.display.set_mode(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT)).convert()
        self.display_rect = pygame.Rect(0, 0, GAME_WIDTH, GAME_HEIGHT)
        self.display_scale = 1.0
        self.update_display_layout()

        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 84)
        self.heading_font = pygame.font.Font(None, 48)
        self.normal_font = pygame.font.Font(None, 31)
        self.small_font = pygame.font.Font(None, 23)
        self.tiny_font = pygame.font.Font(None, 18)
        self.title_font.set_bold(True)
        self.heading_font.set_bold(True)
        self.normal_font.set_bold(True)

        self.save = SaveManager()
        self.settings = self.save.settings
        self.world = TunnelWorld()
        self.endless = EndlessGenerator()

        self.state = STATE_ACCOUNT_LOADING
        self.mode = MODE_ENDLESS
        self.current_level_number = 1
        self.current_level = None
        self.level_page = 0

        self.session = PlayerSession(message="Checking your Matthew's Games account...")
        self.session_task: asyncio.Task | None = asyncio.create_task(load_player_session())
        self.personal_best_task: asyncio.Task | None = None
        self.leaderboard_task: asyncio.Task | None = None
        self.submit_task: asyncio.Task | None = None

        self.personal_best = self.save.endless_best_distance
        self.leaderboard: list[dict[str, Any]] = []
        self.leaderboard_status = "Leaderboard not loaded."

        self.run_start_time = 0
        self.run_end_time = 0
        self.crash_delay_until = 0
        self.finish_delay_until = 0
        self.status_message = ""
        self.status_until = 0
        self.screen_shake = 0.0
        self.screen_shake_until = 0
        self.flash_alpha = 0

        self.stars = [
            (
                random.randrange(GAME_WIDTH),
                random.randrange(GAME_HEIGHT),
                random.choice((1, 1, 1, 2)),
                random.uniform(8.0, 28.0),
            )
            for _ in range(140)
        ]

        self.create_buttons()

    # ========================================================
    # DISPLAY
    # ========================================================

    def update_display_layout(self) -> None:
        width = max(1, self.display_surface.get_width())
        height = max(1, self.display_surface.get_height())
        self.display_scale = max(0.1, min(width / GAME_WIDTH, height / GAME_HEIGHT))
        rendered_width = max(1, round(GAME_WIDTH * self.display_scale))
        rendered_height = max(1, round(GAME_HEIGHT * self.display_scale))
        self.display_rect = pygame.Rect(
            (width - rendered_width) // 2,
            (height - rendered_height) // 2,
            rendered_width,
            rendered_height,
        )

    def display_to_game(self, position: tuple[int, int]) -> tuple[int, int]:
        if not self.display_rect.collidepoint(position):
            return (-10000, -10000)
        return (
            round((position[0] - self.display_rect.left) / self.display_scale),
            round((position[1] - self.display_rect.top) / self.display_scale),
        )

    def convert_event(self, event: pygame.event.Event) -> pygame.event.Event:
        if not hasattr(event, "pos"):
            return event
        values = dict(event.dict)
        values["pos"] = self.display_to_game(event.pos)
        return pygame.event.Event(event.type, values)

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
        self.display_surface.fill(BLACK)
        image = (
            self.screen
            if self.display_rect.size == (GAME_WIDTH, GAME_HEIGHT)
            else pygame.transform.smoothscale(self.screen, self.display_rect.size)
        )

        offset_x = 0
        offset_y = 0
        if pygame.time.get_ticks() < self.screen_shake_until:
            strength = max(0.0, self.screen_shake)
            offset_x = random.randint(-round(strength), round(strength))
            offset_y = random.randint(-round(strength), round(strength))

        self.display_surface.blit(
            image,
            (self.display_rect.left + offset_x, self.display_rect.top + offset_y),
        )
        pygame.display.flip()

    # ========================================================
    # BUTTONS
    # ========================================================

    def create_buttons(self) -> None:
        center_x = GAME_WIDTH // 2
        self.levels_button = Button(
            (center_x - 180, 330, 360, 68),
            "50 LEVELS",
            self.normal_font,
            accent=CYAN,
            shortcut="L",
        )
        self.endless_button = Button(
            (center_x - 180, 465, 360, 68),
            "ENDLESS",
            self.normal_font,
            accent=YELLOW,
            shortcut="E",
        )
        self.leaderboard_button = Button(
            (center_x - 180, 565, 360, 60),
            "LEADERBOARD",
            self.normal_font,
            accent=GREEN,
            shortcut="B",
        )
        self.help_button = Button(
            (35, GAME_HEIGHT - 75, 180, 46),
            "HOW TO PLAY",
            self.small_font,
            accent=BLUE,
        )
        self.settings_button = Button(
            (235, GAME_HEIGHT - 75, 160, 46),
            "SETTINGS",
            self.small_font,
            accent=PURPLE,
        )
        self.back_button = Button(
            (30, 25, 160, 48),
            "BACK",
            self.small_font,
            accent=CYAN,
            shortcut="ESC",
        )
        self.resume_button = Button(
            (GAME_WIDTH // 2 - 170, 330, 340, 62),
            "RESUME",
            self.normal_font,
            accent=GREEN,
        )
        self.restart_button = Button(
            (GAME_WIDTH // 2 - 170, 420, 340, 62),
            "RESTART",
            self.normal_font,
            accent=YELLOW,
        )
        self.menu_button = Button(
            (GAME_WIDTH // 2 - 170, 510, 340, 62),
            "MAIN MENU",
            self.normal_font,
            accent=RED,
        )
        self.retry_button = Button(
            (GAME_WIDTH // 2 - 170, 470, 340, 62),
            "TRY AGAIN",
            self.normal_font,
            accent=CYAN,
        )
        self.game_over_menu_button = Button(
            (GAME_WIDTH // 2 - 170, 555, 340, 62),
            "MAIN MENU",
            self.normal_font,
            accent=BLUE,
        )
        self.next_level_button = Button(
            (GAME_WIDTH // 2 - 170, 470, 340, 62),
            "NEXT LEVEL",
            self.normal_font,
            accent=GREEN,
        )
        self.level_select_button = Button(
            (GAME_WIDTH // 2 - 170, 555, 340, 62),
            "LEVEL SELECT",
            self.normal_font,
            accent=BLUE,
        )

    def level_buttons(self) -> list[Button]:
        buttons: list[Button] = []
        start = self.level_page * 10 + 1
        end = min(CAMPAIGN_LEVELS, start + 9)
        for index, level_number in enumerate(range(start, end + 1)):
            column = index % 5
            row = index // 5
            unlocked = level_number <= self.save.highest_unlocked_level
            complete = self.save.is_level_complete(level_number)
            buttons.append(Button(
                (100 + column * 205, 265 + row * 160, 175, 110),
                str(level_number),
                self.heading_font,
                accent=GREEN if complete else CYAN,
                enabled=unlocked,
            ))
        return buttons

    def active_buttons(self) -> list[Button]:
        if self.state == STATE_MENU:
            return [
                self.levels_button,
                self.endless_button,
                self.leaderboard_button,
                self.help_button,
                self.settings_button,
            ]
        if self.state == STATE_LEVEL_SELECT:
            return [self.back_button, *self.level_buttons()]
        if self.state == STATE_PAUSED:
            return [self.resume_button, self.restart_button, self.menu_button]
        if self.state == STATE_GAME_OVER:
            return [self.retry_button, self.game_over_menu_button]
        if self.state == STATE_LEVEL_COMPLETE:
            return [self.next_level_button, self.level_select_button]
        if self.state in (STATE_LEADERBOARD, STATE_HELP, STATE_SETTINGS):
            return [self.back_button]
        return []

    def update_button_hovers(self) -> None:
        mouse_position = self.display_to_game(pygame.mouse.get_pos())
        for button in self.active_buttons():
            button.update(mouse_position)

    # ========================================================
    # ONLINE TASKS
    # ========================================================

    def update_account_task(self) -> None:
        if self.session_task is None or not self.session_task.done():
            return
        try:
            self.session = self.session_task.result()
        except Exception as error:
            self.session = PlayerSession(message=f"Account error: {error}")
        self.session_task = None

        if self.session.signed_in:
            self.state = STATE_MENU
            self.start_personal_best_load()
            self.start_leaderboard_load()
        else:
            self.state = STATE_ACCOUNT_REQUIRED

    def start_personal_best_load(self) -> None:
        if not self.session.signed_in or not self.session.access_token:
            return
        if self.personal_best_task is not None and not self.personal_best_task.done():
            return
        self.personal_best_task = asyncio.create_task(
            load_player_best_distance(self.session.user_id, self.session.access_token)
        )

    def start_leaderboard_load(self) -> None:
        if self.leaderboard_task is not None and not self.leaderboard_task.done():
            return
        self.leaderboard_status = "Loading all-time distances..."
        self.leaderboard_task = asyncio.create_task(load_online_leaderboard())

    def submit_distance(self, distance: float) -> None:
        if not self.session.access_token:
            return
        if self.submit_task is not None and not self.submit_task.done():
            return
        self.leaderboard_status = "Saving your distance..."
        self.submit_task = asyncio.create_task(
            submit_endless_distance(
                self.session.username,
                distance,
                self.session.user_id,
                self.session.access_token,
            )
        )

    def update_online_tasks(self) -> None:
        if self.personal_best_task is not None and self.personal_best_task.done():
            try:
                score, _ = self.personal_best_task.result()
                self.personal_best = max(self.personal_best, score)
            except Exception:
                pass
            self.personal_best_task = None

        if self.leaderboard_task is not None and self.leaderboard_task.done():
            try:
                self.leaderboard, self.leaderboard_status = self.leaderboard_task.result()
            except Exception as error:
                self.leaderboard_status = f"Leaderboard error: {error}"
            self.leaderboard_task = None

        if self.submit_task is not None and self.submit_task.done():
            try:
                success, message, score = self.submit_task.result()
                self.leaderboard_status = message
                if success:
                    self.personal_best = max(self.personal_best, score)
                    self.start_leaderboard_load()
            except Exception as error:
                self.leaderboard_status = f"Save error: {error}"
            self.submit_task = None

    # ========================================================
    # GAME START / END
    # ========================================================

    def start_endless(self) -> None:
        self.mode = MODE_ENDLESS
        self.current_level = None
        self.world.reset(ENDLESS_START_SPEED)
        self.endless.reset()
        self.endless.next_distance = 70.0
        self.run_start_time = pygame.time.get_ticks()
        self.crash_delay_until = 0
        self.finish_delay_until = 0
        self.state = STATE_PLAYING
        self.generate_endless_if_needed()

    def start_level(self, level_number: int) -> None:
        if level_number > self.save.highest_unlocked_level:
            return
        self.mode = MODE_LEVELS
        self.current_level_number = level_number
        self.current_level = get_level(level_number)
        self.world.reset(self.current_level.start_speed)
        self.world.extend(instantiate_level(level_number))
        self.run_start_time = pygame.time.get_ticks()
        self.crash_delay_until = 0
        self.finish_delay_until = 0
        self.state = STATE_PLAYING

    def restart_current(self) -> None:
        if self.mode == MODE_ENDLESS:
            self.start_endless()
        else:
            self.start_level(self.current_level_number)

    def finish_crash(self) -> None:
        if self.crash_delay_until:
            return
        now = pygame.time.get_ticks()
        self.crash_delay_until = now + 850
        self.screen_shake = 12.0
        self.screen_shake_until = now + 520
        self.flash_alpha = 190

    def complete_crash_transition(self) -> None:
        if not self.crash_delay_until:
            return
        if pygame.time.get_ticks() < self.crash_delay_until:
            return
        self.crash_delay_until = 0
        if self.mode == MODE_ENDLESS:
            self.personal_best = self.save.record_crash(self.world.distance, True)
            self.submit_distance(self.world.distance)
        else:
            self.save.record_crash(self.world.distance, False)
        self.state = STATE_GAME_OVER

    def finish_level(self) -> None:
        if self.finish_delay_until:
            return
        now = pygame.time.get_ticks()
        self.finish_delay_until = now + 650
        self.run_end_time = now

    def complete_level_transition(self) -> None:
        if not self.finish_delay_until:
            return
        if pygame.time.get_ticks() < self.finish_delay_until:
            return
        self.finish_delay_until = 0
        elapsed = max(1, self.run_end_time - self.run_start_time)
        self.save.record_level_complete(
            self.current_level_number,
            self.world.distance,
            elapsed,
        )
        self.state = STATE_LEVEL_COMPLETE

    def generate_endless_if_needed(self) -> None:
        if self.mode != MODE_ENDLESS:
            return
        furthest = max(
            [obstacle.distance for obstacle in self.world.obstacles]
            + [0.0]
        )
        generated = 0
        while (
            furthest < ENDLESS_GENERATE_AHEAD
            and len(self.world.obstacles) < MAX_ACTIVE_OBSTACLES
            and generated < (1 if IS_WEB else 3)
        ):
            section = self.endless.generate_section(self.world.distance)
            self.world.extend(section)
            furthest = max(furthest, max(obstacle.distance for obstacle in section))
            generated += 1

    # ========================================================
    # EVENTS
    # ========================================================

    def handle_event(self, event: pygame.event.Event) -> None:
        event = self.convert_event(event)
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.display_surface = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self.update_display_layout()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
                return

            if event.key == pygame.K_ESCAPE:
                if self.state == STATE_PLAYING:
                    self.state = STATE_PAUSED
                    return
                if self.state == STATE_PAUSED:
                    self.state = STATE_PLAYING
                    return
                if self.state in (STATE_LEVEL_SELECT, STATE_LEADERBOARD, STATE_HELP, STATE_SETTINGS):
                    self.state = STATE_MENU
                    return

        if self.state in (STATE_ACCOUNT_LOADING, STATE_ACCOUNT_REQUIRED):
            return
        if self.state == STATE_MENU:
            self.handle_menu(event)
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
        elif self.state in (STATE_HELP, STATE_SETTINGS):
            if self.back_button.clicked(event):
                self.state = STATE_MENU

    def handle_menu(self, event: pygame.event.Event) -> None:
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
        elif self.help_button.clicked(event):
            self.state = STATE_HELP
        elif self.settings_button.clicked(event):
            self.state = STATE_SETTINGS

    def handle_level_select(self, event: pygame.event.Event) -> None:
        if self.back_button.clicked(event):
            self.state = STATE_MENU
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                self.level_page = min(4, self.level_page + 1)
            elif event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                self.level_page = max(0, self.level_page - 1)

        start = self.level_page * 10 + 1
        for index, button in enumerate(self.level_buttons()):
            if button.clicked(event):
                self.start_level(start + index)
                return

    def handle_playing(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.state = STATE_PAUSED

    def handle_paused(self, event: pygame.event.Event) -> None:
        if self.resume_button.clicked(event):
            self.state = STATE_PLAYING
        elif self.restart_button.clicked(event):
            self.restart_current()
        elif self.menu_button.clicked(event):
            self.state = STATE_MENU

    def handle_game_over(self, event: pygame.event.Event) -> None:
        if self.retry_button.clicked(event):
            self.restart_current()
        elif self.game_over_menu_button.clicked(event):
            self.state = STATE_MENU
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.restart_current()
            elif event.key == pygame.K_m:
                self.state = STATE_MENU

    def handle_level_complete(self, event: pygame.event.Event) -> None:
        next_number = self.current_level_number + 1
        self.next_level_button.enabled = next_number <= CAMPAIGN_LEVELS
        if self.next_level_button.clicked(event) and self.next_level_button.enabled:
            self.start_level(next_number)
        elif self.level_select_button.clicked(event):
            self.state = STATE_LEVEL_SELECT

    def handle_leaderboard(self, event: pygame.event.Event) -> None:
        if self.back_button.clicked(event):
            self.state = STATE_MENU
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.start_leaderboard_load()

    # ========================================================
    # UPDATE
    # ========================================================

    def update(self, dt: float) -> None:
        self.update_account_task()
        self.update_online_tasks()
        self.update_button_hovers()

        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - round(420 * dt))

        if self.state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction += 1
        self.world.player.set_input(direction)

        if self.mode == MODE_ENDLESS:
            self.world.speed = min(
                ENDLESS_MAX_SPEED,
                ENDLESS_START_SPEED + self.world.distance / 100.0 * ENDLESS_SPEED_PER_100M,
            )
            self.generate_endless_if_needed()
        elif self.current_level is not None:
            self.world.speed = min(
                self.current_level.max_speed,
                self.current_level.start_speed + self.current_level.acceleration * self.world.distance,
            )

        for event_type in self.world.update(dt):
            if event_type == "crash":
                self.finish_crash()
            elif event_type == "finish":
                self.finish_level()

        self.complete_crash_transition()
        self.complete_level_transition()

    # ========================================================
    # DRAWING
    # ========================================================

    def current_theme(self) -> dict[str, tuple[int, int, int]]:
        if self.mode == MODE_LEVELS and self.current_level is not None:
            return TUNNEL_THEMES[self.current_level.theme]
        theme_names = tuple(TUNNEL_THEMES)
        index = min(len(theme_names) - 1, int(self.world.distance // 850))
        return TUNNEL_THEMES[theme_names[index]]

    def draw_background(self, current_time: int) -> None:
        theme = self.current_theme()
        self.screen.fill(theme["background"])
        for index, (x, y, radius, speed) in enumerate(self.stars):
            shifted_y = (y + current_time * 0.001 * speed) % GAME_HEIGHT
            brightness = 90 + (index * 23) % 150
            pygame.draw.circle(
                self.screen,
                (brightness, brightness, min(255, brightness + 25)),
                (x, round(shifted_y)),
                radius,
            )

        glow = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*theme["accent"], 45),
            (TUNNEL_CENTER_X, TUNNEL_CENTER_Y),
            260,
        )
        self.screen.blit(glow, (0, 0))

    def draw_tunnel(self) -> None:
        theme = self.current_theme()
        rotation = -self.world.player.angle + 270.0
        ring_count = 16 if IS_WEB else 20
        segment_count = 36 if IS_WEB else 48

        ring_radii: list[float] = []
        for ring_index in range(ring_count):
            distance = ring_index / max(1, ring_count - 1) * VISIBLE_DISTANCE
            projection = self.world.projector.project_distance(distance)
            ring_radii.append(projection.radius)

        # Fill tunnel strips from far to near.
        for ring_index in range(ring_count - 1, 0, -1):
            outer = ring_radii[ring_index - 1]
            inner = ring_radii[ring_index]
            depth_amount = ring_index / max(1, ring_count - 1)
            base_colour = colour_lerp(theme["near"], theme["far"], depth_amount)

            for segment in range(segment_count):
                first_angle = rotation + segment * 360.0 / segment_count
                second_angle = rotation + (segment + 1) * 360.0 / segment_count
                points = [
                    self.world.projector.point(first_angle, outer),
                    self.world.projector.point(second_angle, outer),
                    self.world.projector.point(second_angle, inner),
                    self.world.projector.point(first_angle, inner),
                ]
                shade = 0.78 + 0.22 * ((segment % 2) == 0)
                colour = tuple(round(channel * shade) for channel in base_colour)
                pygame.draw.polygon(self.screen, colour, points)

        # Rings create motion.
        for ring_index, radius in enumerate(ring_radii):
            colour = theme["line"] if ring_index % 4 == 0 else colour_lerp(theme["line"], theme["far"], 0.45)
            pygame.draw.circle(
                self.screen,
                colour,
                (TUNNEL_CENTER_X, TUNNEL_CENTER_Y),
                max(1, round(radius)),
                2 if ring_index % 4 == 0 else 1,
            )

        # Tunnel side lines rotate with player movement.
        for side in range(TUNNEL_SIDES):
            angle = rotation + side * 360.0 / TUNNEL_SIDES
            start = self.world.projector.point(angle, TUNNEL_FAR_RADIUS)
            end = self.world.projector.point(angle, TUNNEL_NEAR_RADIUS)
            pygame.draw.line(
                self.screen,
                theme["line"],
                start,
                end,
                2 if side % 3 == 0 else 1,
            )

        # Center target dot helps the first-person perspective.
        pygame.draw.circle(self.screen, WHITE, (TUNNEL_CENTER_X, TUNNEL_CENTER_Y), 3)

    def draw_player_marker(self) -> None:
        angle = self.world.player.angle
        radians = math.radians(angle)
        radius = min(GAME_WIDTH, GAME_HEIGHT) * 0.43
        x = round(TUNNEL_CENTER_X + math.cos(radians) * radius)
        y = round(TUNNEL_CENTER_Y + math.sin(radians) * radius)
        tangent = pygame.Vector2(-math.sin(radians), math.cos(radians))
        radial = pygame.Vector2(math.cos(radians), math.sin(radians))
        center = pygame.Vector2(x, y)
        points = [
            center + radial * 15,
            center - radial * 10 + tangent * 12,
            center - radial * 10 - tangent * 12,
        ]
        pygame.draw.polygon(self.screen, CYAN, [(round(p.x), round(p.y)) for p in points])
        pygame.draw.polygon(self.screen, WHITE, [(round(p.x), round(p.y)) for p in points], 2)

    def draw_hud(self) -> None:
        draw_panel(
            self.screen,
            pygame.Rect(18, 16, 310, 104),
            fill=(5, 14, 38),
            border=CYAN,
            alpha=215,
        )
        draw_text(self.screen, format_distance(self.world.distance), self.normal_font, WHITE, 35, 30)
        draw_text(self.screen, f"Speed {self.world.speed:.1f}", self.small_font, CYAN, 35, 72)

        if self.mode == MODE_ENDLESS:
            draw_text(self.screen, "ENDLESS", self.normal_font, YELLOW, GAME_WIDTH - 25, 25, right=True)
            draw_text(
                self.screen,
                f"Best {format_distance(self.personal_best)}",
                self.small_font,
                LIGHT_GREY,
                GAME_WIDTH - 25,
                69,
                right=True,
            )
        elif self.current_level is not None:
            draw_text(
                self.screen,
                f"LEVEL {self.current_level.number}",
                self.normal_font,
                WHITE,
                GAME_WIDTH - 25,
                25,
                right=True,
            )
            progress = clamp(self.world.distance / self.current_level.length, 0.0, 1.0)
            draw_text(
                self.screen,
                f"{progress * 100:.0f}%",
                self.small_font,
                CYAN,
                GAME_WIDTH - 25,
                69,
                right=True,
            )

    def draw_gameplay(self) -> None:
        self.draw_tunnel()
        self.world.draw_obstacles(self.screen)
        self.draw_player_marker()
        self.draw_hud()
        if self.flash_alpha > 0:
            flash = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 65, 85, self.flash_alpha))
            self.screen.blit(flash, (0, 0))

    def draw_account(self, loading: bool) -> None:
        panel = pygame.Rect(GAME_WIDTH // 2 - 390, GAME_HEIGHT // 2 - 175, 780, 350)
        draw_panel(self.screen, panel, border=CYAN if loading else RED, border_width=3)
        draw_text(self.screen, GAME_TITLE, self.title_font, WHITE, panel.centerx, panel.top + 70, center=True)
        draw_text(
            self.screen,
            "CHECKING ACCOUNT" if loading else "SIGN IN REQUIRED",
            self.heading_font,
            CYAN if loading else YELLOW,
            panel.centerx,
            panel.top + 155,
            center=True,
        )
        draw_text(self.screen, self.session.message, self.normal_font, LIGHT_GREY, panel.centerx, panel.top + 235, center=True)
        if not loading:
            draw_text(
                self.screen,
                "Return to Matthew's Games, sign in, then reopen Orbit Rush.",
                self.small_font,
                WHITE,
                panel.centerx,
                panel.top + 295,
                center=True,
            )

    def draw_menu(self) -> None:
        draw_text(self.screen, GAME_TITLE.upper(), self.title_font, WHITE, GAME_WIDTH // 2, 88, center=True)
        draw_text(
            self.screen,
            "FIRST-PERSON TUNNEL RUNNER",
            self.normal_font,
            CYAN,
            GAME_WIDTH // 2,
            160,
            center=True,
        )
        draw_text(
            self.screen,
            f"Signed in as {self.session.username}",
            self.small_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            205,
            center=True,
        )
        draw_text(
            self.screen,
            "Rotate around the tunnel and line up with every opening.",
            self.small_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            245,
            center=True,
        )
        self.levels_button.draw(self.screen)
        draw_text(
            self.screen,
            f"Your All-Time Best: {format_distance(self.personal_best)}",
            self.small_font,
            YELLOW,
            GAME_WIDTH // 2,
            self.endless_button.rect.top - 24,
            center=True,
        )
        self.endless_button.draw(self.screen)
        self.leaderboard_button.draw(self.screen)
        self.help_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        draw_text(
            self.screen,
            f"Version {GAME_VERSION}",
            self.tiny_font,
            LIGHT_GREY,
            GAME_WIDTH - 18,
            GAME_HEIGHT - 27,
            right=True,
        )

    def draw_level_select(self) -> None:
        self.back_button.draw(self.screen)
        draw_text(self.screen, "SELECT LEVEL", self.title_font, WHITE, GAME_WIDTH // 2, 80, center=True)
        draw_text(
            self.screen,
            f"Unlocked {self.save.highest_unlocked_level} / {CAMPAIGN_LEVELS}",
            self.small_font,
            CYAN,
            GAME_WIDTH // 2,
            150,
            center=True,
        )
        start = self.level_page * 10 + 1
        end = min(CAMPAIGN_LEVELS, start + 9)
        draw_text(
            self.screen,
            f"Levels {start}-{end}   •   Left / Right changes page",
            self.small_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            200,
            center=True,
        )
        buttons = self.level_buttons()
        for index, button in enumerate(buttons):
            button.draw(self.screen)
            level = get_level(start + index)
            draw_text(
                self.screen,
                level.name,
                self.tiny_font,
                LIGHT_GREY if button.enabled else GREY,
                button.rect.centerx,
                button.rect.bottom + 19,
                center=True,
            )
        draw_text(
            self.screen,
            f"Page {self.level_page + 1} / 5",
            self.small_font,
            CYAN,
            GAME_WIDTH // 2,
            695,
            center=True,
        )

    def draw_pause(self) -> None:
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "PAUSED", self.title_font, WHITE, GAME_WIDTH // 2, 210, center=True)
        self.resume_button.draw(self.screen)
        self.restart_button.draw(self.screen)
        self.menu_button.draw(self.screen)

    def draw_game_over(self) -> None:
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "CRASHED", self.title_font, RED, GAME_WIDTH // 2, 150, center=True)
        draw_text(self.screen, format_distance(self.world.distance), self.heading_font, WHITE, GAME_WIDTH // 2, 260, center=True)
        if self.mode == MODE_ENDLESS:
            draw_text(
                self.screen,
                f"All-Time Best: {format_distance(self.personal_best)}",
                self.normal_font,
                YELLOW,
                GAME_WIDTH // 2,
                335,
                center=True,
            )
        elif self.current_level is not None:
            draw_text(
                self.screen,
                f"Level {self.current_level.number}: {self.current_level.name}",
                self.normal_font,
                CYAN,
                GAME_WIDTH // 2,
                335,
                center=True,
            )
        self.retry_button.draw(self.screen)
        self.game_over_menu_button.draw(self.screen)

    def draw_level_complete(self) -> None:
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "LEVEL COMPLETE", self.title_font, GREEN, GAME_WIDTH // 2, 145, center=True)
        if self.current_level is not None:
            draw_text(
                self.screen,
                f"Level {self.current_level.number}: {self.current_level.name}",
                self.heading_font,
                WHITE,
                GAME_WIDTH // 2,
                245,
                center=True,
            )
            elapsed = max(1, self.run_end_time - self.run_start_time)
            draw_text(
                self.screen,
                f"Time {elapsed / 1000:.2f}s   •   {format_distance(self.world.distance)}",
                self.normal_font,
                CYAN,
                GAME_WIDTH // 2,
                325,
                center=True,
            )
        self.next_level_button.draw(self.screen)
        self.level_select_button.draw(self.screen)

    def draw_leaderboard(self) -> None:
        self.back_button.draw(self.screen)
        draw_text(self.screen, "ENDLESS LEADERBOARD", self.title_font, WHITE, GAME_WIDTH // 2, 78, center=True)
        draw_text(
            self.screen,
            f"Your best: {format_distance(self.personal_best)}",
            self.small_font,
            YELLOW,
            GAME_WIDTH // 2,
            145,
            center=True,
        )
        board = pygame.Rect(185, 185, 830, 455)
        draw_panel(self.screen, board, fill=(6, 16, 42), border=CYAN)
        if not self.leaderboard:
            draw_text(self.screen, self.leaderboard_status, self.normal_font, LIGHT_GREY, board.centerx, board.centery, center=True)
        else:
            for rank, entry in enumerate(self.leaderboard[:MAX_LEADERBOARD_ENTRIES], 1):
                y = board.top + 30 + (rank - 1) * 41
                colour = YELLOW if rank == 1 else CYAN if rank <= 3 else WHITE
                draw_text(self.screen, f"{rank}.", self.normal_font, colour, board.left + 35, y)
                draw_text(self.screen, str(entry.get("name", "Player")), self.normal_font, WHITE, board.left + 105, y)
                draw_text(
                    self.screen,
                    format_distance(entry.get("distance", 0)),
                    self.normal_font,
                    colour,
                    board.right - 35,
                    y,
                    right=True,
                )
        draw_text(self.screen, "Press R to refresh", self.tiny_font, LIGHT_GREY, GAME_WIDTH // 2, 680, center=True)

    def draw_help(self) -> None:
        self.back_button.draw(self.screen)
        draw_text(self.screen, "HOW TO PLAY", self.title_font, WHITE, GAME_WIDTH // 2, 85, center=True)
        panel = pygame.Rect(150, 175, 900, 455)
        draw_panel(self.screen, panel)
        instructions = (
            ("Move", "Hold A / D or Left / Right to rotate around the tunnel."),
            ("Goal", "Line your marker up with every opening before it reaches you."),
            ("Levels", "Complete all 50 courses. Each group of ten changes theme and difficulty."),
            ("Endless", "Run forever through fair random patterns. Only Endless counts on the leaderboard."),
            ("Hazards", "Gates, double gaps, rotating bars, crosses, fans, shutters, sliders, and pulses."),
            ("Pause", "Press P or Escape. Press F11 to toggle fullscreen."),
        )
        y = panel.top + 48
        for title, description in instructions:
            draw_text(self.screen, title, self.normal_font, CYAN, panel.left + 45, y)
            draw_text(self.screen, description, self.small_font, WHITE, panel.left + 190, y + 4)
            y += 63

    def draw_settings(self) -> None:
        self.back_button.draw(self.screen)
        draw_text(self.screen, "SETTINGS", self.title_font, WHITE, GAME_WIDTH // 2, 90, center=True)
        panel = pygame.Rect(225, 205, 750, 350)
        draw_panel(self.screen, panel)
        lines = (
            "F11 toggles fullscreen.",
            "The browser automatically fits the game to the available screen.",
            "Version numbers appear in the bottom-right of the home screen.",
            "Campaign progress and local bests save automatically.",
            "Online Endless bests use your Matthew's Games account.",
        )
        for index, line in enumerate(lines):
            draw_text(
                self.screen,
                line,
                self.normal_font if index < 2 else self.small_font,
                WHITE if index < 2 else LIGHT_GREY,
                panel.centerx,
                panel.top + 55 + index * 58,
                center=True,
            )

    def draw(self, current_time: int) -> None:
        self.draw_background(current_time)
        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER, STATE_LEVEL_COMPLETE):
            self.draw_gameplay()

        if self.state == STATE_ACCOUNT_LOADING:
            self.draw_account(True)
        elif self.state == STATE_ACCOUNT_REQUIRED:
            self.draw_account(False)
        elif self.state == STATE_MENU:
            self.draw_menu()
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
        elif self.state == STATE_HELP:
            self.draw_help()
        elif self.state == STATE_SETTINGS:
            self.draw_settings()

    # ========================================================
    # LOOP
    # ========================================================

    async def run(self) -> None:
        while self.running:
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw(current_time)
            self.present()
            await asyncio.sleep(0)

        self.save.save()
        pygame.quit()


async def main() -> None:
    game = OrbitRush()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
