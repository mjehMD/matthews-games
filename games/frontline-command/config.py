from __future__ import annotations


# ============================================================
# WINDOW
# ============================================================

GAME_WIDTH = 1450
GAME_HEIGHT = 800
FPS = 60

WINDOW_TITLE = "Frontline Command"


# ============================================================
# INTERFACE LAYOUT
# ============================================================

LEFT_PANEL_LEFT = 15
LEFT_PANEL_TOP = 80
LEFT_PANEL_WIDTH = 225
LEFT_PANEL_HEIGHT = 670

TILE_SIZE = 50

MAP_COLUMNS = 18
MAP_ROWS = 14

MAP_LEFT = 260
MAP_TOP = 80

MAP_WIDTH = MAP_COLUMNS * TILE_SIZE
MAP_HEIGHT = MAP_ROWS * TILE_SIZE

SIDEBAR_LEFT = MAP_LEFT + MAP_WIDTH + 20
SIDEBAR_WIDTH = GAME_WIDTH - SIDEBAR_LEFT - 20


# ============================================================
# ENEMY PATH
# ============================================================

PATH_TILES = [
    (0, 2),
    (1, 2),
    (2, 2),
    (3, 2),
    (4, 2),
    (4, 3),
    (4, 4),
    (4, 5),
    (5, 5),
    (6, 5),
    (7, 5),
    (8, 5),
    (9, 5),
    (9, 6),
    (9, 7),
    (9, 8),
    (8, 8),
    (7, 8),
    (6, 8),
    (5, 8),
    (5, 9),
    (5, 10),
    (6, 10),
    (7, 10),
    (8, 10),
    (9, 10),
    (10, 10),
    (11, 10),
    (12, 10),
    (13, 10),
    (13, 9),
    (13, 8),
    (14, 8),
    (15, 8),
    (16, 8),
    (17, 8),
]


# ============================================================
# COLOURS
# ============================================================

BLACK = (8, 10, 12)
WHITE = (240, 243, 235)

BACKGROUND = (24, 29, 24)

PANEL = (38, 45, 38)
PANEL_LIGHT = (52, 61, 50)

GREEN = (72, 108, 62)
LIGHT_GREEN = (112, 155, 91)
DARK_GREEN = (39, 66, 38)

SAND = (166, 147, 104)

ROAD = (112, 101, 76)
ROAD_EDGE = (78, 69, 50)

GREY = (135, 140, 136)
DARK_GREY = (67, 73, 70)
LIGHT_GREY = (190, 195, 187)

RED = (205, 66, 57)
DARK_RED = (112, 42, 38)

BLUE = (65, 112, 177)
LIGHT_BLUE = (92, 157, 220)

YELLOW = (228, 198, 71)
ORANGE = (224, 126, 51)
PURPLE = (138, 88, 161)

CYAN = (70, 205, 215)
BROWN = (116, 79, 48)

HEALTH_GREEN = (65, 186, 86)
ARMOR_BLUE = (72, 141, 205)


# ============================================================
# DIFFICULTY
# ============================================================

DIFFICULTIES = {
    "easy": {
        "display_name": "Easy",
        "multiplier": 1,
        "starting_money": 1400,
        "base_health": 30,
        "enemy_health_multiplier": 0.85,
        "enemy_speed_multiplier": 0.90,
        "enemy_reward_multiplier": 1.15,
    },
    "medium": {
        "display_name": "Medium",
        "multiplier": 2,
        "starting_money": 1050,
        "base_health": 20,
        "enemy_health_multiplier": 1.0,
        "enemy_speed_multiplier": 1.0,
        "enemy_reward_multiplier": 1.0,
    },
    "hard": {
        "display_name": "Hard",
        "multiplier": 3,
        "starting_money": 800,
        "base_health": 14,
        "enemy_health_multiplier": 1.25,
        "enemy_speed_multiplier": 1.12,
        "enemy_reward_multiplier": 0.90,
    },
}


# ============================================================
# DEFENCE UNITS
# ============================================================

TOWER_TYPES = {
    "rifle": {
        "name": "Rifle Squad",
        "short_name": "Rifle",
        "description": "Balanced infantry defence.",
        "category": "combat",
        "unit_kind": "tower",
        "placement": "ground",
        "cost": 200,
        "damage": 8,
        "range": 125,
        "cooldown": 520,
        "projectile_speed": 8,
        "projectile_type": "bullet",
        "armor_piercing": 0,
        "splash_radius": 0,
        "slow_multiplier": 1.0,
        "slow_duration_ms": 0,
        "max_level": 4,
        "default_targeting": "first",
        "colour": LIGHT_GREEN,
    },

    "machine_gun": {
        "name": "Machine Gun Nest",
        "short_name": "MG Nest",
        "description": "Extremely rapid gunfire.",
        "category": "combat",
        "unit_kind": "tower",
        "placement": "ground",
        "cost": 350,
        "damage": 4,
        "range": 120,
        "cooldown": 145,
        "projectile_speed": 11,
        "projectile_type": "bullet",
        "armor_piercing": 0.5,
        "splash_radius": 0,
        "slow_multiplier": 1.0,
        "slow_duration_ms": 0,
        "max_level": 4,
        "default_targeting": "first",
        "colour": YELLOW,
    },

    "sniper": {
        "name": "Sniper Team",
        "short_name": "Sniper",
        "description": "Long-range armor-piercing shots.",
        "category": "combat",
        "unit_kind": "tower",
        "placement": "ground",
        "cost": 450,
        "damage": 40,
        "range": 240,
        "cooldown": 1250,
        "projectile_speed": 17,
        "projectile_type": "sniper",
        "armor_piercing": 5,
        "splash_radius": 0,
        "slow_multiplier": 1.0,
        "slow_duration_ms": 0,
        "max_level": 4,
        "default_targeting": "strongest",
        "colour": LIGHT_BLUE,
    },

    "mortar": {
        "name": "Mortar Position",
        "short_name": "Mortar",
        "description": "Explosive area damage.",
        "category": "combat",
        "unit_kind": "tower",
        "placement": "ground",
        "cost": 550,
        "damage": 26,
        "range": 190,
        "cooldown": 1550,
        "projectile_speed": 7,
        "projectile_type": "shell",
        "armor_piercing": 1,
        "splash_radius": 70,
        "slow_multiplier": 0.82,
        "slow_duration_ms": 900,
        "max_level": 4,
        "default_targeting": "first",
        "colour": ORANGE,
    },

    "land_mine": {
        "name": "Land Mine",
        "short_name": "Mine",
        "description": "Road trap that rearms each wave.",
        "category": "combat",
        "unit_kind": "mine",
        "placement": "road",
        "cost": 125,
        "damage": 90,
        "range": 0,
        "cooldown": 0,
        "projectile_speed": 0,
        "projectile_type": "none",
        "armor_piercing": 3,
        "splash_radius": 70,
        "slow_multiplier": 0.70,
        "slow_duration_ms": 1100,
        "max_level": 4,
        "default_targeting": "first",
        "colour": RED,
    },

    "supply_depot": {
        "name": "Supply Depot",
        "short_name": "Depot",
        "description": "Generates funds after each wave.",
        "category": "support",
        "unit_kind": "income",
        "placement": "ground",
        "cost": 650,
        "wave_income": 90,
        "max_level": 4,
        "colour": BROWN,
    },

    "intelligence": {
        "name": "Intelligence Centre",
        "short_name": "Intel",
        "description": "Generates bonus leaderboard score.",
        "category": "support",
        "unit_kind": "score",
        "placement": "ground",
        "cost": 800,
        "wave_score": 2,
        "max_level": 4,
        "colour": PURPLE,
    },

    "tank_factory": {
        "name": "Tank Factory",
        "short_name": "Factory",
        "description": "Deploys friendly tanks each wave.",
        "category": "support",
        "unit_kind": "factory",
        "placement": "ground",
        "cost": 1100,
        "factory_interval": 8500,
        "friendly_tank_damage": 38,
        "friendly_tank_health": 4,
        "friendly_tank_speed": 1.15,
        "max_level": 4,
        "colour": DARK_GREEN,
    },

    "helipad": {
        "name": "Helicopter Pad",
        "short_name": "Helipad",
        "description": "Launches orbiting attack helicopters.",
        "category": "support",
        "unit_kind": "helipad",
        "placement": "ground",
        "cost": 1250,
        "helicopter_count": 1,
        "helicopter_damage": 10,
        "helicopter_range": 220,
        "helicopter_cooldown": 430,
        "max_level": 4,
        "colour": CYAN,
    },
}


# ============================================================
# ENEMY TYPES
# ============================================================

ENEMY_TYPES = {
    "infantry": {
        "name": "Infantry",
        "health": 45,
        "armor": 0,
        "speed": 1.15,
        "reward": 22,
        "base_damage": 1,
        "colour": RED,
        "size": 18,
    },

    "scout": {
        "name": "Scout",
        "health": 30,
        "armor": 0,
        "speed": 1.80,
        "reward": 25,
        "base_damage": 1,
        "colour": ORANGE,
        "size": 15,
    },

    "armored": {
        "name": "Armored Infantry",
        "health": 95,
        "armor": 3,
        "speed": 0.92,
        "reward": 38,
        "base_damage": 2,
        "colour": PURPLE,
        "size": 20,
    },

    "jeep": {
        "name": "Military Jeep",
        "health": 125,
        "armor": 2,
        "speed": 1.55,
        "reward": 45,
        "base_damage": 2,
        "colour": YELLOW,
        "size": 22,
    },

    "tank": {
        "name": "Battle Tank",
        "health": 280,
        "armor": 6,
        "speed": 0.65,
        "reward": 85,
        "base_damage": 4,
        "colour": DARK_GREEN,
        "size": 25,
    },

    "boss": {
        "name": "Command Tank",
        "health": 850,
        "armor": 8,
        "speed": 0.48,
        "reward": 250,
        "base_damage": 8,
        "colour": DARK_RED,
        "size": 34,
    },
}