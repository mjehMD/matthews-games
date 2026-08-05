from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ============================================================
# STORAGE SETTINGS
# ============================================================

LEADERBOARD_FILE = Path(__file__).with_name("leaderboard.json")

MAX_LEADERBOARD_ENTRIES = 10

VALID_DIFFICULTIES = {
    "Easy",
    "Medium",
    "Hard",
}


# ============================================================
# VALIDATION HELPERS
# ============================================================

def clean_player_name(name: Any) -> str:
    """
    Clean and limit a leaderboard player name.
    """

    cleaned_name = str(name).strip()

    if not cleaned_name:
        cleaned_name = "Player"

    return cleaned_name[:16]


def clean_difficulty(difficulty: Any) -> str:
    """
    Return a valid difficulty display name.
    """

    cleaned_difficulty = str(difficulty).strip().title()

    if cleaned_difficulty not in VALID_DIFFICULTIES:
        return "Easy"

    return cleaned_difficulty


def clean_score(value: Any) -> int:
    """
    Return a valid non-negative score.
    """

    if isinstance(value, bool):
        return 0

    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0

    return max(0, score)


def clean_wave(value: Any) -> int:
    """
    Return a valid wave number.
    """

    if isinstance(value, bool):
        return 1

    try:
        wave = int(value)
    except (TypeError, ValueError):
        return 1

    return max(1, wave)


def clean_kills(value: Any) -> int:
    """
    Return a valid enemy kill count.
    """

    if isinstance(value, bool):
        return 0

    try:
        kills = int(value)
    except (TypeError, ValueError):
        return 0

    return max(0, kills)


def difficulty_multiplier(difficulty: str) -> int:
    """
    Return the score multiplier for a difficulty.
    """

    multipliers = {
        "Easy": 1,
        "Medium": 2,
        "Hard": 3,
    }

    return multipliers.get(
        clean_difficulty(difficulty),
        1,
    )


# ============================================================
# LEADERBOARD ENTRY
# ============================================================

def create_leaderboard_entry(
    player_name: Any,
    score: Any,
    wave: Any,
    difficulty: Any,
    kills: Any | None = None,
) -> dict[str, Any]:
    """
    Create one validated leaderboard entry.
    """

    cleaned_difficulty = clean_difficulty(difficulty)
    cleaned_score = clean_score(score)

    if kills is None:
        multiplier = difficulty_multiplier(
            cleaned_difficulty
        )

        cleaned_kills = (
            cleaned_score // multiplier
            if multiplier > 0
            else cleaned_score
        )
    else:
        cleaned_kills = clean_kills(kills)

    return {
        "name": clean_player_name(player_name),
        "score": cleaned_score,
        "wave": clean_wave(wave),
        "difficulty": cleaned_difficulty,
        "kills": cleaned_kills,
    }


def leaderboard_sort_key(
    entry: dict[str, Any],
) -> tuple[int, int, int]:
    """
    Sort higher scores first.

    Ties are broken by:
    1. Higher wave
    2. More enemies defeated
    """

    return (
        clean_score(entry.get("score", 0)),
        clean_wave(entry.get("wave", 1)),
        clean_kills(entry.get("kills", 0)),
    )


def sort_leaderboard(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return a cleaned and sorted leaderboard.
    """

    cleaned_entries: list[dict[str, Any]] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        cleaned_entries.append(
            create_leaderboard_entry(
                player_name=entry.get(
                    "name",
                    "Player",
                ),
                score=entry.get(
                    "score",
                    0,
                ),
                wave=entry.get(
                    "wave",
                    1,
                ),
                difficulty=entry.get(
                    "difficulty",
                    "Easy",
                ),
                kills=entry.get(
                    "kills",
                ),
            )
        )

    cleaned_entries.sort(
        key=leaderboard_sort_key,
        reverse=True,
    )

    return cleaned_entries[
        :MAX_LEADERBOARD_ENTRIES
    ]


# ============================================================
# FILE CREATION
# ============================================================

def create_empty_leaderboard_file() -> None:
    """
    Create leaderboard.json if it does not exist.
    """

    if LEADERBOARD_FILE.exists():
        return

    try:
        with LEADERBOARD_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                [],
                file,
                indent=4,
            )

    except OSError:
        pass


# ============================================================
# LOADING
# ============================================================

def load_leaderboard() -> list[dict[str, Any]]:
    """
    Load and validate the leaderboard.

    Invalid or damaged entries are ignored. If the file is
    missing or unreadable, an empty leaderboard is returned.
    """

    create_empty_leaderboard_file()

    try:
        with LEADERBOARD_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []

    if not isinstance(raw_data, list):
        return []

    return sort_leaderboard(raw_data)


# ============================================================
# SAVING
# ============================================================

def save_leaderboard(
    entries: list[dict[str, Any]],
) -> bool:
    """
    Save the leaderboard.

    Returns True if saving succeeds.
    """

    cleaned_entries = sort_leaderboard(
        entries
    )

    temporary_file = LEADERBOARD_FILE.with_suffix(
        ".tmp"
    )

    try:
        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                cleaned_entries,
                file,
                indent=4,
            )

        temporary_file.replace(
            LEADERBOARD_FILE
        )

        return True

    except OSError:
        try:
            if temporary_file.exists():
                temporary_file.unlink()
        except OSError:
            pass

        return False


# ============================================================
# ADDING SCORES
# ============================================================

def add_score(
    entries: list[dict[str, Any]],
    player_name: str,
    score: int,
    wave: int,
    difficulty: str,
    kills: int | None = None,
) -> dict[str, Any]:
    """
    Add a completed game to the leaderboard.

    This function matches the current call used by main.py.
    """

    entry = create_leaderboard_entry(
        player_name=player_name,
        score=score,
        wave=wave,
        difficulty=difficulty,
        kills=kills,
    )

    entries.append(entry)

    sorted_entries = sort_leaderboard(
        entries
    )

    entries.clear()
    entries.extend(sorted_entries)

    save_leaderboard(entries)

    return entry


# ============================================================
# PLAYER SCORE HELPERS
# ============================================================

def get_player_best_score(
    entries: list[dict[str, Any]],
    player_name: str,
) -> dict[str, Any] | None:
    """
    Return a player's best leaderboard result.
    """

    cleaned_name = clean_player_name(
        player_name
    ).lower()

    matching_entries = [
        entry
        for entry in sort_leaderboard(entries)
        if clean_player_name(
            entry.get("name", "")
        ).lower()
        == cleaned_name
    ]

    if not matching_entries:
        return None

    return matching_entries[0]


def score_qualifies(
    entries: list[dict[str, Any]],
    score: int,
    wave: int = 1,
    kills: int = 0,
) -> bool:
    """
    Check whether a score qualifies for the top ten.
    """

    cleaned_entries = sort_leaderboard(
        entries
    )

    if len(cleaned_entries) < MAX_LEADERBOARD_ENTRIES:
        return True

    candidate_key = (
        clean_score(score),
        clean_wave(wave),
        clean_kills(kills),
    )

    lowest_entry_key = leaderboard_sort_key(
        cleaned_entries[-1]
    )

    return candidate_key > lowest_entry_key


def clear_leaderboard() -> bool:
    """
    Remove all saved leaderboard entries.
    """

    return save_leaderboard([])