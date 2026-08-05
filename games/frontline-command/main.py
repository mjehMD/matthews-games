Library
/
frontline_command_main_mouse_fixed.py


from __future__ import annotations

import asyncio
import random

import pygame

from config import (
    BACKGROUND,
    DARK_GREEN,
    DARK_GREY,
    DIFFICULTIES,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    GREEN,
    LEFT_PANEL_HEIGHT,
    LEFT_PANEL_LEFT,
    LEFT_PANEL_TOP,
    LEFT_PANEL_WIDTH,
    LIGHT_BLUE,
    LIGHT_GREEN,
    LIGHT_GREY,
    MAP_COLUMNS,
    MAP_HEIGHT,
    MAP_LEFT,
    MAP_ROWS,
    MAP_TOP,
    MAP_WIDTH,
    PANEL,
    PANEL_LIGHT,
    PATH_TILES,
    RED,
    ROAD,
    ROAD_EDGE,
    SAND,
    SIDEBAR_LEFT,
    SIDEBAR_WIDTH,
    TILE_SIZE,
    TOWER_TYPES,
    WHITE,
    WINDOW_TITLE,
    YELLOW,
)
from entities import Enemy, FriendlyTank, Projectile, Tower
from online_leaderboard import (
    load_online_leaderboard,
    submit_online_score,
)
from storage import add_score, load_leaderboard, save_leaderboard


# ============================================================
# BUTTON
# ============================================================

class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hovered = False

    def update(self, mouse_position: tuple[int, int]) -> None:
        self.hovered = self.rect.collidepoint(mouse_position)

    def clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(
        self,
        surface: pygame.Surface,
        enabled: bool = True,
        selected: bool = False,
    ) -> None:
        if not enabled:
            fill_colour = DARK_GREY
            border_colour = LIGHT_GREY
        elif selected:
            fill_colour = LIGHT_GREEN
            border_colour = YELLOW
        elif self.hovered:
            fill_colour = LIGHT_GREEN
            border_colour = WHITE
        else:
            fill_colour = GREEN
            border_colour = LIGHT_GREEN

        pygame.draw.rect(
            surface,
            (12, 15, 12),
            self.rect.move(0, 4),
            border_radius=8,
        )

        pygame.draw.rect(
            surface,
            fill_colour,
            self.rect,
            border_radius=8,
        )

        pygame.draw.rect(
            surface,
            border_colour,
            self.rect,
            width=3 if selected else 2,
            border_radius=8,
        )

        image = self.font.render(
            self.text,
            True,
            WHITE if enabled else LIGHT_GREY,
        )

        surface.blit(
            image,
            image.get_rect(center=self.rect.center),
        )


# ============================================================
# VISUAL EFFECTS
# ============================================================

class Particle:
    def __init__(
        self,
        position: pygame.Vector2,
        colour: tuple[int, int, int],
    ):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(
            random.uniform(-4, 4),
            random.uniform(-4, 4),
        )

        self.colour = colour
        self.life = random.randint(20, 42)
        self.max_life = self.life
        self.radius = random.randint(2, 5)

    def update(self, time_scale: float) -> None:
        self.position += self.velocity * time_scale
        self.velocity *= 0.95
        self.life -= time_scale

    def draw(self, surface: pygame.Surface) -> None:
        if self.life <= 0:
            return

        fade = max(0, self.life / self.max_life)

        colour = (
            int(self.colour[0] * fade),
            int(self.colour[1] * fade),
            int(self.colour[2] * fade),
        )

        pygame.draw.circle(
            surface,
            colour,
            (
                round(self.position.x),
                round(self.position.y),
            ),
            max(1, int(self.radius * fade)),
        )


class FloatingText:
    def __init__(
        self,
        text: str,
        position: pygame.Vector2,
        colour: tuple[int, int, int],
    ):
        self.text = text
        self.position = pygame.Vector2(position)
        self.colour = colour
        self.life = 65

    def update(self, time_scale: float) -> None:
        self.position.y -= 0.7 * time_scale
        self.life -= time_scale

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        image = font.render(self.text, True, self.colour)

        surface.blit(
            image,
            image.get_rect(
                center=(
                    round(self.position.x),
                    round(self.position.y),
                )
            ),
        )


# ============================================================
# MAIN GAME
# ============================================================

class FrontlineCommand:
    def __init__(self):
        pygame.init()

        self.fullscreen = False

        self.screen = pygame.display.set_mode(
            (GAME_WIDTH, GAME_HEIGHT)
        )

        pygame.display.set_caption(WINDOW_TITLE)

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.Font(None, 70)
        self.heading_font = pygame.font.Font(None, 38)
        self.normal_font = pygame.font.Font(None, 27)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 17)

        self.running = True
        self.state = "name_entry"

        self.player_name = ""

        self.difficulty_key = "easy"
        self.difficulty = DIFFICULTIES["easy"]

        self.money = 0
        self.base_health = 0

        self.wave = 0
        self.kills = 0

        self.kill_score = 0
        self.bonus_score = 0
        self.score = 0

        self.wave_active = False
        self.wave_enemies_to_spawn = 0
        self.wave_spawned = 0

        self.last_spawn_time = 0
        self.spawn_delay = 850

        self.towers: list[Tower] = []
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.friendly_tanks: list[FriendlyTank] = []

        self.particles: list[Particle] = []
        self.floating_texts: list[FloatingText] = []

        self.selected_tower_type: str | None = None
        self.selected_tower: Tower | None = None

        self.sidebar_tab = "combat"

        self.paused = False
        self.game_speed = 1

        self.score_saved = False
        self.leaderboard = load_leaderboard()

        self.leaderboard_task: asyncio.Task | None = None
        self.score_submit_task: asyncio.Task | None = None

        self.leaderboard_loading = False
        self.score_uploading = False

        self.leaderboard_status = (
            "Local leaderboard loaded."
            if self.leaderboard
            else "No scores saved yet."
        )

        self.status_message = ""
        self.status_message_until = 0

        self.create_buttons()

    # ========================================================
    # BUTTONS
    # ========================================================

    def create_buttons(self) -> None:
        center_x = GAME_WIDTH // 2

        self.easy_button = Button(
            pygame.Rect(center_x - 270, 315, 170, 65),
            "EASY x1",
            self.normal_font,
        )

        self.medium_button = Button(
            pygame.Rect(center_x - 85, 315, 170, 65),
            "MEDIUM x2",
            self.normal_font,
        )

        self.hard_button = Button(
            pygame.Rect(center_x + 100, 315, 170, 65),
            "HARD x3",
            self.normal_font,
        )

        self.start_button = Button(
            pygame.Rect(center_x - 160, 455, 320, 70),
            "START MISSION",
            self.heading_font,
        )

        tab_width = (SIDEBAR_WIDTH - 30) // 2

        self.combat_tab_button = Button(
            pygame.Rect(
                SIDEBAR_LEFT + 10,
                145,
                tab_width,
                34,
            ),
            "COMBAT",
            self.small_font,
        )

        self.support_tab_button = Button(
            pygame.Rect(
                SIDEBAR_LEFT + 20 + tab_width,
                145,
                tab_width,
                34,
            ),
            "SUPPORT",
            self.small_font,
        )

        self.upgrade_button = Button(
            pygame.Rect(
                LEFT_PANEL_LEFT + 12,
                545,
                LEFT_PANEL_WIDTH - 24,
                44,
            ),
            "UPGRADE",
            self.small_font,
        )

        self.target_button = Button(
            pygame.Rect(
                LEFT_PANEL_LEFT + 12,
                599,
                LEFT_PANEL_WIDTH - 24,
                40,
            ),
            "TARGET",
            self.small_font,
        )

        self.sell_button = Button(
            pygame.Rect(
                LEFT_PANEL_LEFT + 12,
                649,
                LEFT_PANEL_WIDTH - 24,
                40,
            ),
            "SELL",
            self.small_font,
        )

        self.wave_button = Button(
            pygame.Rect(
                SIDEBAR_LEFT + 12,
                690,
                SIDEBAR_WIDTH - 24,
                50,
            ),
            "START WAVE",
            self.normal_font,
        )

        self.fullscreen_button = Button(
            pygame.Rect(
                GAME_WIDTH - 145,
                GAME_HEIGHT - 34,
                130,
                27,
            ),
            "FULLSCREEN",
            self.tiny_font,
        )

    # ========================================================
    # GENERAL
    # ========================================================

    def set_status(
        self,
        message: str,
        duration_ms: int = 1800,
    ) -> None:
        self.status_message = message
        self.status_message_until = (
            pygame.time.get_ticks() + duration_ms
        )

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen

        flags = (
            pygame.FULLSCREEN
            if self.fullscreen
            else 0
        )

        self.screen = pygame.display.set_mode(
            (GAME_WIDTH, GAME_HEIGHT),
            flags,
        )

        pygame.display.set_caption(WINDOW_TITLE)

        self.fullscreen_button.text = (
            "WINDOWED"
            if self.fullscreen
            else "FULLSCREEN"
        )

    def reset_game(self) -> None:
        self.difficulty = DIFFICULTIES[self.difficulty_key]

        self.money = int(self.difficulty["starting_money"])
        self.base_health = int(self.difficulty["base_health"])

        self.wave = 0
        self.kills = 0

        self.kill_score = 0
        self.bonus_score = 0
        self.score = 0

        self.wave_active = False
        self.wave_enemies_to_spawn = 0
        self.wave_spawned = 0

        self.towers.clear()
        self.enemies.clear()
        self.projectiles.clear()
        self.friendly_tanks.clear()

        self.particles.clear()
        self.floating_texts.clear()

        self.selected_tower_type = None
        self.selected_tower = None

        self.sidebar_tab = "combat"

        self.paused = False
        self.game_speed = 1

        self.score_saved = False
        self.state = "playing"

    def update_score(self) -> None:
        multiplier = int(self.difficulty["multiplier"])

        self.kill_score = self.kills * multiplier
        self.score = self.kill_score + self.bonus_score

    # ========================================================
    # PLACEMENT
    # ========================================================

    def screen_to_tile(
        self,
        position: tuple[int, int],
    ) -> tuple[int, int] | None:
        x, y = position

        if not (
            MAP_LEFT <= x < MAP_LEFT + MAP_WIDTH
            and MAP_TOP <= y < MAP_TOP + MAP_HEIGHT
        ):
            return None

        return (
            int((x - MAP_LEFT) // TILE_SIZE),
            int((y - MAP_TOP) // TILE_SIZE),
        )

    def tower_at_tile(
        self,
        tile: tuple[int, int],
    ) -> Tower | None:
        for tower in self.towers:
            if tower.tile == tile:
                return tower

        return None

    def can_place_tower(
        self,
        tower_type: str,
        tile: tuple[int, int],
    ) -> bool:
        column, row = tile

        if not (
            0 <= column < MAP_COLUMNS
            and 0 <= row < MAP_ROWS
        ):
            return False

        if self.tower_at_tile(tile) is not None:
            return False

        placement = str(TOWER_TYPES[tower_type]["placement"])

        if placement == "road":
            return tile in PATH_TILES

        return tile not in PATH_TILES

    def place_tower(self, tile: tuple[int, int]) -> None:
        tower_type = self.selected_tower_type

        if tower_type is None:
            return

        if not self.can_place_tower(tower_type, tile):
            if TOWER_TYPES[tower_type]["placement"] == "road":
                self.set_status(
                    "Land mines must be placed on the road."
                )
            else:
                self.set_status(
                    "This unit must be placed beside the road."
                )

            return

        cost = int(TOWER_TYPES[tower_type]["cost"])

        if self.money < cost:
            self.set_status("Not enough funds.")
            return

        self.money -= cost

        tower = Tower(tower_type, tile)
        self.towers.append(tower)

        self.selected_tower = tower
        self.selected_tower_type = None

        self.set_status(f"{tower.name} deployed.")

    def visible_tower_types(self) -> list[str]:
        return [
            tower_type
            for tower_type, data in TOWER_TYPES.items()
            if data["category"] == self.sidebar_tab
        ]

    def tower_card_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(
            SIDEBAR_LEFT + 10,
            190 + index * 86,
            SIDEBAR_WIDTH - 20,
            76,
        )

    def select_tower_card(
        self,
        position: tuple[int, int],
    ) -> bool:
        for index, tower_type in enumerate(
            self.visible_tower_types()
        ):
            card_rect = self.tower_card_rect(index)

            if not card_rect.collidepoint(position):
                continue

            cost = int(TOWER_TYPES[tower_type]["cost"])

            if self.money < cost:
                self.set_status("Not enough funds.")
                return True

            self.selected_tower_type = tower_type
            self.selected_tower = None

            self.set_status(
                f"Place {TOWER_TYPES[tower_type]['name']}."
            )

            return True

        return False

    # ========================================================
    # SELECTED UNIT ACTIONS
    # ========================================================

    def upgrade_selected_tower(self) -> None:
        tower = self.selected_tower

        if tower is None:
            self.set_status("Select a deployed unit first.")
            return

        if not tower.can_upgrade():
            self.set_status("Maximum level reached.")
            return

        if self.money < tower.upgrade_cost:
            self.set_status(
                "Not enough funds for this upgrade."
            )
            return

        cost = tower.upgrade()
        self.money -= cost

        self.set_status(
            f"{tower.name} upgraded to level {tower.level}."
        )

    def sell_selected_tower(self) -> None:
        tower = self.selected_tower

        if tower is None:
            self.set_status("Select a deployed unit first.")
            return

        value = tower.sell_value

        self.money += value
        self.towers.remove(tower)
        self.selected_tower = None

        self.set_status(f"Unit sold for ${value}.")

    def cycle_selected_targeting(self) -> None:
        tower = self.selected_tower

        if tower is None:
            self.set_status("Select a deployed unit first.")
            return

        if tower.unit_kind != "tower":
            self.set_status(
                "This unit does not use targeting modes."
            )
            return

        mode = tower.cycle_targeting_mode()
        self.set_status(f"Targeting: {mode.title()}.")

    # ========================================================
    # WAVES
    # ========================================================

    def start_wave(self) -> None:
        if self.wave_active or self.enemies:
            self.set_status(
                "The current wave is still active."
            )
            return

        self.wave += 1
        self.wave_active = True

        if self.wave % 5 == 0:
            self.wave_enemies_to_spawn = 1
        else:
            self.wave_enemies_to_spawn = 6 + self.wave * 2

        self.wave_spawned = 0
        self.last_spawn_time = 0

        self.spawn_delay = max(
            330,
            900 - self.wave * 18,
        )

        for tower in self.towers:
            tower.rearm_for_wave()

        if self.wave % 5 == 0:
            self.set_status(
                f"BOSS WAVE {self.wave}",
                2500,
            )
        else:
            self.set_status(f"Wave {self.wave} started.")

    def choose_enemy_type(self) -> str:
        if self.wave % 5 == 0:
            return "boss"

        available = ["infantry", "scout"]

        if self.wave >= 6:
            available.extend(["armored", "jeep"])

        if self.wave >= 11:
            available.append("tank")

        weights = {
            "infantry": 42,
            "scout": 28,
            "armored": 16,
            "jeep": 10,
            "tank": 4,
        }

        return random.choices(
            available,
            weights=[
                weights[enemy_type]
                for enemy_type in available
            ],
            k=1,
        )[0]

    def spawn_enemy(self) -> None:
        enemy_type = self.choose_enemy_type()

        self.enemies.append(
            Enemy(
                enemy_type,
                self.wave,
                float(
                    self.difficulty[
                        "enemy_health_multiplier"
                    ]
                ),
                float(
                    self.difficulty[
                        "enemy_speed_multiplier"
                    ]
                ),
                float(
                    self.difficulty[
                        "enemy_reward_multiplier"
                    ]
                ),
            )
        )

        self.wave_spawned += 1

    def update_wave_spawning(self, current_time: int) -> None:
        if not self.wave_active:
            return

        if self.wave_spawned >= self.wave_enemies_to_spawn:
            return

        if (
            current_time - self.last_spawn_time
            < self.spawn_delay
        ):
            return

        self.spawn_enemy()
        self.last_spawn_time = current_time

    # ========================================================
    # COMBAT
    # ========================================================

    def update_enemies(self, current_time: int) -> None:
        time_scale = float(self.game_speed)

        for enemy in self.enemies[:]:
            enemy.update(time_scale, current_time)

            if not enemy.reached_base:
                continue

            self.base_health -= enemy.base_damage

            self.create_explosion(
                enemy.position,
                RED,
                16,
            )

            self.enemies.remove(enemy)

            self.set_status(
                f"Base hit! -{enemy.base_damage} health"
            )

            if self.base_health <= 0:
                self.base_health = 0
                self.end_game()
                return

    def update_defence_units(self, current_time: int) -> None:
        adjusted_time = current_time * self.game_speed
        time_scale = float(self.game_speed)

        for tower in self.towers:
            projectile = tower.update_attack(
                self.enemies,
                adjusted_time,
            )

            if projectile is not None:
                self.projectiles.append(projectile)

            self.projectiles.extend(
                tower.update_helicopters(
                    self.enemies,
                    adjusted_time,
                    time_scale,
                )
            )

            if tower.try_trigger_mine(
                self.enemies,
                current_time,
            ):
                self.create_explosion(
                    tower.position,
                    RED,
                    34,
                )

                self.set_status("Land mine detonated!")

            if (
                self.wave_active
                and tower.should_factory_spawn(adjusted_time)
            ):
                self.friendly_tanks.append(
                    FriendlyTank(tower)
                )

                self.set_status("Friendly tank deployed.")

    def update_friendly_tanks(
        self,
        current_time: int,
    ) -> None:
        time_scale = float(self.game_speed)

        for tank in self.friendly_tanks[:]:
            tank.update(
                self.enemies,
                time_scale,
                current_time,
            )

            if tank.dead:
                self.create_explosion(
                    tank.position,
                    DARK_GREEN,
                    15,
                )

                self.friendly_tanks.remove(tank)

    def update_projectiles(self, current_time: int) -> None:
        time_scale = float(self.game_speed)

        for projectile in self.projectiles[:]:
            projectile.update(
                self.enemies,
                time_scale,
                current_time,
            )

            if projectile.dead:
                self.create_explosion(
                    projectile.target_position,
                    projectile.colour,
                    7,
                )

                self.projectiles.remove(projectile)

        self.collect_destroyed_enemies()

    def collect_destroyed_enemies(self) -> None:
        for enemy in self.enemies[:]:
            if not enemy.dead:
                continue

            self.money += enemy.reward
            self.kills += 1
            self.update_score()

            self.create_explosion(
                enemy.position,
                enemy.colour,
                70 if enemy.enemy_type == "boss" else 24,
            )

            self.floating_texts.append(
                FloatingText(
                    f"+${enemy.reward}",
                    enemy.position,
                    YELLOW,
                )
            )

            self.enemies.remove(enemy)

    def check_wave_complete(self) -> None:
        if not self.wave_active:
            return

        if self.wave_spawned < self.wave_enemies_to_spawn:
            return

        if self.enemies:
            return

        self.wave_active = False

        wave_bonus = 75 + self.wave * 18

        if self.wave % 5 == 0:
            wave_bonus += 150

        support_income = sum(
            tower.wave_income
            for tower in self.towers
            if tower.unit_kind == "income"
        )

        raw_score_bonus = sum(
            tower.wave_score
            for tower in self.towers
            if tower.unit_kind == "score"
        )

        score_bonus = (
            raw_score_bonus
            * int(self.difficulty["multiplier"])
        )

        self.money += wave_bonus + support_income

        self.bonus_score += score_bonus
        self.update_score()

        message = f"Wave complete! ${wave_bonus}"

        if support_income:
            message += f" + ${support_income} depot income"

        if score_bonus:
            message += f" + {score_bonus} score"

        self.set_status(message, 3000)

    # ========================================================
    # EFFECTS AND GAME OVER
    # ========================================================

    def create_explosion(
        self,
        position: pygame.Vector2,
        colour: tuple[int, int, int],
        amount: int,
    ) -> None:
        for _ in range(amount):
            self.particles.append(
                Particle(
                    position,
                    random.choice(
                        [colour, YELLOW, WHITE]
                    ),
                )
            )

    def update_effects(self) -> None:
        time_scale = float(
            self.game_speed
            if self.state == "playing" and not self.paused
            else 1
        )

        for particle in self.particles[:]:
            particle.update(time_scale)

            if particle.life <= 0:
                self.particles.remove(particle)

        for text in self.floating_texts[:]:
            text.update(time_scale)

            if text.life <= 0:
                self.floating_texts.remove(text)

    def open_leaderboard(self) -> None:
        self.state = "leaderboard"
        self.start_online_leaderboard_load()

    def start_online_leaderboard_load(self) -> None:
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

    def start_online_score_submit(self) -> None:
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
                str(self.difficulty["display_name"]),
                self.kills,
            )
        )

    def update_online_leaderboard_tasks(self) -> None:
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

    def end_game(self) -> None:
        if not self.score_saved:
            add_score(
                self.leaderboard,
                self.player_name,
                self.score,
                self.wave,
                str(self.difficulty["display_name"]),
                self.kills,
            )

            self.score_saved = True
            self.start_online_score_submit()

        self.wave_active = False
        self.paused = False
        self.state = "game_over"

    # ========================================================
    # EVENTS
    # ========================================================

    def handle_name_entry(
        self,
        event: pygame.event.Event,
    ) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            cleaned = self.player_name.strip()

            if cleaned:
                self.player_name = cleaned[:16]
                self.state = "difficulty"

        elif event.key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]

        elif event.unicode.isprintable():
            if len(self.player_name) < 16:
                self.player_name += event.unicode

    def handle_difficulty(
        self,
        event: pygame.event.Event,
    ) -> None:
        if self.easy_button.clicked(event):
            self.difficulty_key = "easy"

        elif self.medium_button.clicked(event):
            self.difficulty_key = "medium"

        elif self.hard_button.clicked(event):
            self.difficulty_key = "hard"

        elif self.start_button.clicked(event):
            self.reset_game()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.difficulty_key = "easy"
            elif event.key == pygame.K_2:
                self.difficulty_key = "medium"
            elif event.key == pygame.K_3:
                self.difficulty_key = "hard"
            elif event.key == pygame.K_RETURN:
                self.reset_game()
            elif event.key == pygame.K_l:
                self.open_leaderboard()

    def handle_playing(
        self,
        event: pygame.event.Event,
    ) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_p,
                pygame.K_ESCAPE,
            ):
                self.paused = not self.paused
                return

            if self.paused:
                return

            if event.key == pygame.K_SPACE:
                self.start_wave()
            elif event.key == pygame.K_1:
                self.game_speed = 1
            elif event.key == pygame.K_2:
                self.game_speed = 2
            elif event.key == pygame.K_u:
                self.upgrade_selected_tower()
            elif event.key == pygame.K_t:
                self.cycle_selected_targeting()
            elif event.key == pygame.K_s:
                self.sell_selected_tower()

            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.fullscreen_button.clicked(event):
            self.toggle_fullscreen()
            return

        if self.paused:
            return

        if event.button == 3:
            self.selected_tower_type = None
            self.selected_tower = None
            self.set_status("Selection cancelled.")
            return

        if event.button != 1:
            return

        if self.combat_tab_button.clicked(event):
            self.sidebar_tab = "combat"
            self.selected_tower_type = None
            return

        if self.support_tab_button.clicked(event):
            self.sidebar_tab = "support"
            self.selected_tower_type = None
            return

        if self.wave_button.clicked(event):
            self.start_wave()
            return

        if self.upgrade_button.clicked(event):
            self.upgrade_selected_tower()
            return

        if self.target_button.clicked(event):
            self.cycle_selected_targeting()
            return

        if self.sell_button.clicked(event):
            self.sell_selected_tower()
            return

        if self.select_tower_card(event.pos):
            return

        tile = self.screen_to_tile(event.pos)

        if tile is None:
            return

        existing = self.tower_at_tile(tile)

        if existing is not None:
            self.selected_tower = existing
            self.selected_tower_type = None
            self.set_status(f"{existing.name} selected.")

        elif self.selected_tower_type is not None:
            self.place_tower(tile)

        else:
            self.selected_tower = None

    def handle_event(self, event: pygame.event.Event) -> None:
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

        elif self.state == "difficulty":
            self.handle_difficulty(event)

        elif self.state == "playing":
            self.handle_playing(event)

        elif self.state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_r, pygame.K_m):
                    self.state = "difficulty"
                elif event.key == pygame.K_l:
                    self.open_leaderboard()

        elif self.state == "leaderboard":
            if (
                event.type == pygame.KEYDOWN
                and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_RETURN,
                    pygame.K_m,
                )
            ):
                self.state = "difficulty"

    # ========================================================
    # UPDATE
    # ========================================================

    def update_buttons(self) -> None:
        mouse = pygame.mouse.get_pos()

        for button in (
            self.easy_button,
            self.medium_button,
            self.hard_button,
            self.start_button,
            self.combat_tab_button,
            self.support_tab_button,
            self.upgrade_button,
            self.target_button,
            self.sell_button,
            self.wave_button,
            self.fullscreen_button,
        ):
            button.update(mouse)

    def update(self, current_time: int) -> None:
        self.update_buttons()
        self.update_effects()

        if self.state != "playing" or self.paused:
            return

        self.update_wave_spawning(current_time)
        self.update_enemies(current_time)

        if self.state != "playing":
            return

        self.update_defence_units(current_time)
        self.update_friendly_tanks(current_time)
        self.update_projectiles(current_time)
        self.check_wave_complete()

    # ========================================================
    # DRAWING HELPERS
    # ========================================================

    def draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        colour: tuple[int, int, int],
        x: int,
        y: int,
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

        self.screen.blit(image, rect)
        return rect

    def draw_background(self) -> None:
        self.screen.fill(BACKGROUND)

    def draw_map(self) -> None:
        pygame.draw.rect(
            self.screen,
            SAND,
            (MAP_LEFT, MAP_TOP, MAP_WIDTH, MAP_HEIGHT),
        )

        for row in range(MAP_ROWS):
            for column in range(MAP_COLUMNS):
                tile = (column, row)

                tile_rect = pygame.Rect(
                    MAP_LEFT + column * TILE_SIZE,
                    MAP_TOP + row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                if tile in PATH_TILES:
                    pygame.draw.rect(
                        self.screen,
                        ROAD,
                        tile_rect,
                    )

                    pygame.draw.rect(
                        self.screen,
                        ROAD_EDGE,
                        tile_rect,
                        width=1,
                    )
                else:
                    colour = (
                        GREEN
                        if (column + row) % 2 == 0
                        else DARK_GREEN
                    )

                    pygame.draw.rect(
                        self.screen,
                        colour,
                        tile_rect,
                    )

                    pygame.draw.rect(
                        self.screen,
                        (42, 67, 40),
                        tile_rect,
                        width=1,
                    )

        entrance = PATH_TILES[0]
        base_tile = PATH_TILES[-1]

        entrance_rect = pygame.Rect(
            MAP_LEFT + entrance[0] * TILE_SIZE,
            MAP_TOP + entrance[1] * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )

        base_rect = pygame.Rect(
            MAP_LEFT + base_tile[0] * TILE_SIZE,
            MAP_TOP + base_tile[1] * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )

        pygame.draw.rect(
            self.screen,
            RED,
            entrance_rect,
            width=4,
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_BLUE,
            base_rect,
            width=4,
        )

        self.draw_text(
            "ENEMY",
            self.tiny_font,
            WHITE,
            entrance_rect.centerx,
            entrance_rect.centery,
            center=True,
        )

        self.draw_text(
            "BASE",
            self.tiny_font,
            WHITE,
            base_rect.centerx,
            base_rect.centery,
            center=True,
        )

    def draw_placement_preview(self) -> None:
        tower_type = self.selected_tower_type

        if tower_type is None:
            return

        tile = self.screen_to_tile(pygame.mouse.get_pos())

        if tile is None:
            return

        tile_rect = pygame.Rect(
            MAP_LEFT + tile[0] * TILE_SIZE,
            MAP_TOP + tile[1] * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )

        valid = self.can_place_tower(tower_type, tile)

        preview = pygame.Surface(
            (TILE_SIZE, TILE_SIZE),
            pygame.SRCALPHA,
        )

        preview.fill(
            (80, 220, 100, 115)
            if valid
            else (230, 60, 60, 125)
        )

        self.screen.blit(preview, tile_rect.topleft)

        data = TOWER_TYPES[tower_type]
        unit_kind = str(data["unit_kind"])

        radius = 0

        if unit_kind == "tower":
            radius = int(data.get("range", 0))
        elif unit_kind == "mine":
            radius = int(data.get("splash_radius", 0))
        elif unit_kind == "helipad":
            radius = int(data.get("helicopter_range", 0))

        if radius <= 0:
            return

        range_surface = pygame.Surface(
            (GAME_WIDTH, GAME_HEIGHT),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            range_surface,
            (
                90,
                220,
                120,
                35,
            )
            if valid
            else (
                230,
                70,
                70,
                35,
            ),
            tile_rect.center,
            radius,
        )

        pygame.draw.circle(
            range_surface,
            (
                235,
                255,
                235,
                190,
            )
            if valid
            else (
                255,
                90,
                90,
                210,
            ),
            tile_rect.center,
            radius,
            width=2,
        )

        self.screen.blit(range_surface, (0, 0))

    # ========================================================
    # LEFT SELECTED-UNIT PANEL
    # ========================================================

    def selected_unit_details(self) -> list[tuple[str, str]]:
        tower = self.selected_tower

        if tower is None:
            return []

        details: list[tuple[str, str]] = [
            ("Level", f"{tower.level}/{tower.max_level}"),
            ("Sell value", f"${tower.sell_value}"),
        ]

        if tower.unit_kind == "tower":
            details.extend(
                [
                    ("Damage", f"{tower.damage:.1f}"),
                    ("Range", f"{tower.attack_range:.0f}"),
                    ("Cooldown", f"{tower.cooldown} ms"),
                    (
                        "Armor pierce",
                        f"{tower.armor_piercing:.1f}",
                    ),
                    (
                        "Targeting",
                        tower.targeting_mode.title(),
                    ),
                ]
            )

            if tower.splash_radius > 0:
                details.append(
                    (
                        "Blast radius",
                        f"{tower.splash_radius:.0f}",
                    )
                )

        elif tower.unit_kind == "mine":
            details.extend(
                [
                    ("Damage", f"{tower.damage:.1f}"),
                    (
                        "Blast radius",
                        f"{tower.splash_radius:.0f}",
                    ),
                    (
                        "Status",
                        "Armed"
                        if tower.mine_armed
                        else "Used this wave",
                    ),
                ]
            )

        elif tower.unit_kind == "income":
            details.append(
                (
                    "Wave income",
                    f"${tower.wave_income}",
                )
            )

        elif tower.unit_kind == "score":
            details.append(
                (
                    "Wave score",
                    f"+{tower.wave_score}",
                )
            )

        elif tower.unit_kind == "factory":
            details.extend(
                [
                    (
                        "Tank damage",
                        f"{tower.friendly_tank_damage:.1f}",
                    ),
                    (
                        "Tank durability",
                        str(tower.friendly_tank_health),
                    ),
                    (
                        "Tank speed",
                        f"{tower.friendly_tank_speed:.2f}",
                    ),
                    (
                        "Deploy time",
                        f"{tower.factory_interval / 1000:.1f}s",
                    ),
                ]
            )

        elif tower.unit_kind == "helipad":
            details.extend(
                [
                    (
                        "Helicopters",
                        str(tower.helicopter_count),
                    ),
                    (
                        "Damage",
                        f"{tower.helicopter_damage:.1f}",
                    ),
                    (
                        "Range",
                        f"{tower.helicopter_range:.0f}",
                    ),
                    (
                        "Fire delay",
                        f"{tower.helicopter_cooldown} ms",
                    ),
                ]
            )

        return details

    def draw_selected_unit_panel(self) -> None:
        panel_rect = pygame.Rect(
            LEFT_PANEL_LEFT,
            LEFT_PANEL_TOP,
            LEFT_PANEL_WIDTH,
            LEFT_PANEL_HEIGHT,
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            panel_rect,
            border_radius=10,
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_GREY,
            panel_rect,
            width=2,
            border_radius=10,
        )

        self.draw_text(
            "UNIT COMMAND",
            self.heading_font,
            WHITE,
            panel_rect.centerx,
            112,
            center=True,
        )

        pygame.draw.line(
            self.screen,
            LIGHT_GREEN,
            (
                panel_rect.left + 12,
                142,
            ),
            (
                panel_rect.right - 12,
                142,
            ),
            width=2,
        )

        tower = self.selected_tower

        if tower is None:
            self.draw_text(
                "No unit selected",
                self.normal_font,
                LIGHT_GREY,
                panel_rect.centerx,
                205,
                center=True,
            )

            self.draw_text(
                "Click a deployed",
                self.small_font,
                LIGHT_GREY,
                panel_rect.centerx,
                255,
                center=True,
            )

            self.draw_text(
                "defence unit to",
                self.small_font,
                LIGHT_GREY,
                panel_rect.centerx,
                280,
                center=True,
            )

            self.draw_text(
                "view its statistics.",
                self.small_font,
                LIGHT_GREY,
                panel_rect.centerx,
                305,
                center=True,
            )

            self.draw_text(
                "Right-click cancels",
                self.tiny_font,
                LIGHT_GREY,
                panel_rect.centerx,
                390,
                center=True,
            )

            self.draw_text(
                "your current selection.",
                self.tiny_font,
                LIGHT_GREY,
                panel_rect.centerx,
                410,
                center=True,
            )

            return

        icon_center = (
            panel_rect.centerx,
            185,
        )

        pygame.draw.circle(
            self.screen,
            (22, 27, 22),
            icon_center,
            34,
        )

        pygame.draw.circle(
            self.screen,
            tower.colour,
            icon_center,
            29,
        )

        self.draw_text(
            str(tower.level),
            self.heading_font,
            WHITE,
            icon_center[0],
            icon_center[1],
            center=True,
        )

        self.draw_text(
            tower.name,
            self.normal_font,
            WHITE,
            panel_rect.centerx,
            240,
            center=True,
        )

        self.draw_text(
            f"Level {tower.level}",
            self.small_font,
            YELLOW,
            panel_rect.centerx,
            270,
            center=True,
        )

        pygame.draw.line(
            self.screen,
            DARK_GREY,
            (
                panel_rect.left + 12,
                295,
            ),
            (
                panel_rect.right - 12,
                295,
            ),
            width=2,
        )

        detail_y = 315

        for label, value in self.selected_unit_details():
            self.draw_text(
                label,
                self.tiny_font,
                LIGHT_GREY,
                panel_rect.left + 15,
                detail_y,
            )

            self.draw_text(
                value,
                self.tiny_font,
                WHITE,
                panel_rect.right - 15,
                detail_y,
                right=True,
            )

            detail_y += 25

            if detail_y > 510:
                break

        self.upgrade_button.text = (
            f"UPGRADE ${tower.upgrade_cost}"
            if tower.can_upgrade()
            else "MAXIMUM LEVEL"
        )

        self.target_button.text = (
            f"TARGET: {tower.targeting_mode.upper()}"
            if tower.unit_kind == "tower"
            else "NO TARGETING"
        )

        self.sell_button.text = (
            f"SELL ${tower.sell_value}"
        )

        self.upgrade_button.draw(
            self.screen,
            enabled=(
                tower.can_upgrade()
                and self.money >= tower.upgrade_cost
            ),
        )

        self.target_button.draw(
            self.screen,
            enabled=tower.unit_kind == "tower",
        )

        self.sell_button.draw(self.screen)

    # ========================================================
    # RIGHT DEFENCE CATALOGUE
    # ========================================================

    def draw_tower_cards(self) -> None:
        for index, tower_type in enumerate(
            self.visible_tower_types()
        ):
            data = TOWER_TYPES[tower_type]
            rect = self.tower_card_rect(index)

            selected = self.selected_tower_type == tower_type
            affordable = self.money >= int(data["cost"])

            fill = (
                LIGHT_GREEN
                if selected
                else PANEL_LIGHT
                if affordable
                else DARK_GREY
            )

            pygame.draw.rect(
                self.screen,
                fill,
                rect,
                border_radius=7,
            )

            pygame.draw.rect(
                self.screen,
                YELLOW if selected else LIGHT_GREY,
                rect,
                width=3 if selected else 2,
                border_radius=7,
            )

            self.draw_text(
                data["name"],
                self.small_font,
                WHITE if affordable else LIGHT_GREY,
                rect.x + 8,
                rect.y + 8,
            )

            self.draw_text(
                f"${data['cost']}",
                self.small_font,
                YELLOW if affordable else RED,
                rect.right - 8,
                rect.y + 8,
                right=True,
            )

            self.draw_text(
                data["description"],
                self.tiny_font,
                LIGHT_GREY,
                rect.x + 8,
                rect.y + 39,
            )

    def draw_sidebar(self) -> None:
        sidebar_rect = pygame.Rect(
            SIDEBAR_LEFT,
            MAP_TOP,
            SIDEBAR_WIDTH,
            MAP_HEIGHT,
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            sidebar_rect,
            border_radius=10,
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_GREY,
            sidebar_rect,
            width=2,
            border_radius=10,
        )

        self.draw_text(
            "DEFENCE UNITS",
            self.heading_font,
            WHITE,
            sidebar_rect.centerx,
            110,
            center=True,
        )

        self.combat_tab_button.draw(
            self.screen,
            selected=self.sidebar_tab == "combat",
        )

        self.support_tab_button.draw(
            self.screen,
            selected=self.sidebar_tab == "support",
        )

        self.draw_tower_cards()

        self.wave_button.text = (
            "WAVE ACTIVE"
            if self.wave_active or self.enemies
            else "START WAVE"
        )

        self.wave_button.draw(
            self.screen,
            enabled=(
                not self.wave_active
                and not self.enemies
                and not self.paused
            ),
        )

    # ========================================================
    # HUD AND GAME DRAWING
    # ========================================================

    def draw_hud(self) -> None:
        pygame.draw.rect(
            self.screen,
            PANEL,
            (0, 0, GAME_WIDTH, 65),
        )

        self.draw_text(
            "FRONTLINE COMMAND",
            self.heading_font,
            WHITE,
            18,
            15,
        )

        self.draw_text(
            f"Funds: ${self.money}",
            self.normal_font,
            YELLOW,
            355,
            20,
        )

        self.draw_text(
            f"Base: {self.base_health}",
            self.normal_font,
            LIGHT_BLUE if self.base_health > 5 else RED,
            515,
            20,
        )

        self.draw_text(
            f"Wave: {self.wave}",
            self.normal_font,
            WHITE,
            635,
            20,
        )

        self.draw_text(
            f"Kills: {self.kills}",
            self.normal_font,
            WHITE,
            745,
            20,
        )

        self.draw_text(
            f"Score: {self.score}",
            self.normal_font,
            YELLOW,
            855,
            20,
        )

        self.draw_text(
            f"{self.difficulty['display_name']} "
            f"x{self.difficulty['multiplier']}",
            self.normal_font,
            LIGHT_GREEN,
            1035,
            20,
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            (0, GAME_HEIGHT - 40, GAME_WIDTH, 40),
        )

        self.draw_text(
            f"Speed: {self.game_speed}x",
            self.small_font,
            WHITE,
            15,
            GAME_HEIGHT - 28,
        )

        self.draw_text(
            "Space: Wave  P: Pause  1/2: Speed  "
            "U: Upgrade  T: Target  S: Sell",
            self.small_font,
            LIGHT_GREY,
            125,
            GAME_HEIGHT - 28,
        )

        self.fullscreen_button.draw(self.screen)

    def draw_status_message(self, current_time: int) -> None:
        if current_time >= self.status_message_until:
            return

        message_rect = pygame.Rect(
            MAP_LEFT + 150,
            MAP_TOP + 10,
            600,
            42,
        )

        pygame.draw.rect(
            self.screen,
            (20, 25, 20),
            message_rect,
            border_radius=9,
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_GREEN,
            message_rect,
            width=2,
            border_radius=9,
        )

        self.draw_text(
            self.status_message,
            self.small_font,
            WHITE,
            message_rect.centerx,
            message_rect.centery,
            center=True,
        )

    def draw_playing(self, current_time: int) -> None:
        self.draw_map()
        self.draw_placement_preview()

        for tower in self.towers:
            tower.draw(
                self.screen,
                selected=tower is self.selected_tower,
            )

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for tank in self.friendly_tanks:
            tank.draw(self.screen)

        for projectile in self.projectiles:
            projectile.draw(self.screen)

        for particle in self.particles:
            particle.draw(self.screen)

        for text in self.floating_texts:
            text.draw(self.screen, self.small_font)

        self.draw_selected_unit_panel()
        self.draw_sidebar()
        self.draw_hud()
        self.draw_status_message(current_time)

        if self.paused:
            overlay = pygame.Surface(
                (GAME_WIDTH, GAME_HEIGHT),
                pygame.SRCALPHA,
            )

            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            self.draw_text(
                "PAUSED",
                self.title_font,
                WHITE,
                GAME_WIDTH // 2,
                GAME_HEIGHT // 2 - 25,
                center=True,
            )

            self.draw_text(
                "Press P or Escape to continue",
                self.normal_font,
                LIGHT_GREY,
                GAME_WIDTH // 2,
                GAME_HEIGHT // 2 + 35,
                center=True,
            )

    # ========================================================
    # MENU DRAWING
    # ========================================================

    def draw_name_entry(self, current_time: int) -> None:
        self.draw_text(
            "FRONTLINE COMMAND",
            self.title_font,
            LIGHT_GREEN,
            GAME_WIDTH // 2,
            150,
            center=True,
        )

        self.draw_text(
            "Military Tower Defence",
            self.heading_font,
            WHITE,
            GAME_WIDTH // 2,
            225,
            center=True,
        )

        self.draw_text(
            "Enter your commander name",
            self.heading_font,
            WHITE,
            GAME_WIDTH // 2,
            315,
            center=True,
        )

        name_rect = pygame.Rect(
            GAME_WIDTH // 2 - 230,
            380,
            460,
            70,
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            name_rect,
            border_radius=10,
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_GREEN,
            name_rect,
            width=3,
            border_radius=10,
        )

        shown_name = self.player_name

        if current_time % 1000 < 500:
            shown_name += "|"

        self.draw_text(
            shown_name,
            self.heading_font,
            WHITE,
            name_rect.centerx,
            name_rect.centery,
            center=True,
        )

        self.draw_text(
            "Press Enter to continue",
            self.normal_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            505,
            center=True,
        )

    def draw_difficulty(self) -> None:
        self.draw_text(
            "SELECT DIFFICULTY",
            self.title_font,
            LIGHT_GREEN,
            GAME_WIDTH // 2,
            135,
            center=True,
        )

        self.draw_text(
            "Higher difficulty gives a larger score multiplier.",
            self.normal_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            220,
            center=True,
        )

        self.easy_button.draw(
            self.screen,
            selected=self.difficulty_key == "easy",
        )

        self.medium_button.draw(
            self.screen,
            selected=self.difficulty_key == "medium",
        )

        self.hard_button.draw(
            self.screen,
            selected=self.difficulty_key == "hard",
        )

        data = DIFFICULTIES[self.difficulty_key]

        self.draw_text(
            f"Starting funds: ${data['starting_money']}",
            self.normal_font,
            YELLOW,
            GAME_WIDTH // 2,
            405,
            center=True,
        )

        self.draw_text(
            f"Base health: {data['base_health']}",
            self.normal_font,
            LIGHT_BLUE,
            GAME_WIDTH // 2,
            438,
            center=True,
        )

        self.start_button.draw(self.screen)

        self.draw_text(
            "Press L to view the leaderboard",
            self.small_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            590,
            center=True,
        )

    def draw_game_over(self) -> None:
        self.draw_text(
            "COMMAND BASE DESTROYED",
            self.title_font,
            RED,
            GAME_WIDTH // 2,
            140,
            center=True,
        )

        self.draw_text(
            f"Final score: {self.score}",
            self.heading_font,
            YELLOW,
            GAME_WIDTH // 2,
            270,
            center=True,
        )

        self.draw_text(
            f"Kill score: {self.kill_score}",
            self.normal_font,
            WHITE,
            GAME_WIDTH // 2,
            335,
            center=True,
        )

        self.draw_text(
            f"Support bonus: {self.bonus_score}",
            self.normal_font,
            LIGHT_GREEN,
            GAME_WIDTH // 2,
            375,
            center=True,
        )

        self.draw_text(
            f"Wave reached: {self.wave}",
            self.normal_font,
            WHITE,
            GAME_WIDTH // 2,
            415,
            center=True,
        )

        self.draw_text(
            "Press R to play again",
            self.normal_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            530,
            center=True,
        )

        self.draw_text(
            "Press L to view the leaderboard",
            self.normal_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            575,
            center=True,
        )

    def draw_leaderboard(self) -> None:
        self.draw_text(
            "FRONTLINE LEADERBOARD",
            self.title_font,
            YELLOW,
            GAME_WIDTH // 2,
            85,
            center=True,
        )

        board = pygame.Rect(
            GAME_WIDTH // 2 - 410,
            140,
            820,
            530,
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            board,
            border_radius=14,
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_GREEN,
            board,
            width=2,
            border_radius=14,
        )

        headers = [
            ("Rank", board.left + 45),
            ("Commander", board.left + 155),
            ("Score", board.left + 430),
            ("Difficulty", board.left + 575),
            ("Wave", board.left + 720),
        ]

        for text, x in headers:
            self.draw_text(
                text,
                self.normal_font,
                LIGHT_BLUE,
                x,
                165,
            )

        if not self.leaderboard:
            self.draw_text(
                "No scores yet",
                self.heading_font,
                LIGHT_GREY,
                GAME_WIDTH // 2,
                390,
                center=True,
            )
        else:
            y = 215

            for position, entry in enumerate(
                self.leaderboard,
                start=1,
            ):
                colour = (
                    YELLOW
                    if position == 1
                    else LIGHT_BLUE
                    if position == 2
                    else LIGHT_GREEN
                    if position == 3
                    else WHITE
                )

                self.draw_text(
                    str(position),
                    self.normal_font,
                    colour,
                    board.left + 65,
                    y,
                    center=True,
                )

                self.draw_text(
                    entry["name"],
                    self.normal_font,
                    colour,
                    board.left + 155,
                    y - 13,
                )

                self.draw_text(
                    str(entry["score"]),
                    self.normal_font,
                    colour,
                    board.left + 460,
                    y,
                    center=True,
                )

                self.draw_text(
                    entry["difficulty"],
                    self.normal_font,
                    colour,
                    board.left + 625,
                    y,
                    center=True,
                )

                self.draw_text(
                    str(entry["wave"]),
                    self.normal_font,
                    colour,
                    board.left + 755,
                    y,
                    center=True,
                )

                y += 42

        status_colour = (
            LIGHT_BLUE
            if self.leaderboard_loading
            or self.score_uploading
            else LIGHT_GREEN
            if "loaded" in self.leaderboard_status.lower()
            or "saved" in self.leaderboard_status.lower()
            else LIGHT_GREY
        )

        self.draw_text(
            self.leaderboard_status,
            self.small_font,
            status_colour,
            GAME_WIDTH // 2,
            688,
            center=True,
        )

        self.draw_text(
            "Press Enter, M, or Escape to return",
            self.normal_font,
            LIGHT_GREY,
            GAME_WIDTH // 2,
            720,
            center=True,
        )

    # ========================================================
    # MAIN DRAW AND LOOP
    # ========================================================

    def draw(self, current_time: int) -> None:
        self.draw_background()

        if self.state == "name_entry":
            self.draw_name_entry(current_time)

        elif self.state == "difficulty":
            self.draw_difficulty()

        elif self.state == "playing":
            self.draw_playing(current_time)

        elif self.state == "game_over":
            self.draw_game_over()

        elif self.state == "leaderboard":
            self.draw_leaderboard()

        pygame.display.flip()

    async def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)

            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                self.handle_event(event)

            self.update_online_leaderboard_tasks()
            self.update(current_time)
            self.draw(current_time)

            await asyncio.sleep(0)

        pygame.quit()


async def main() -> None:
    game = FrontlineCommand()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())