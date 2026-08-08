from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from config import (
    ACHIEVEMENT_DEFINITIONS,
    DEFAULT_SAVE_DATA,
    DEFAULT_SETTINGS_DATA,
    DEFAULT_STATISTICS_DATA,
    SAVE_FILE,
    SETTINGS_FILE,
    STATISTICS_FILE,
    TOTAL_LEVELS,
)


# ============================================================
# TUNNEL RUNNER
# STORAGE SYSTEM
# VERSION 0.1.0
# ============================================================
#
# Handles:
#
# - campaign progression
# - highest unlocked level
# - completed levels
# - best level times
# - level attempts
# - Endless personal best
# - total runs
# - total crashes
# - total distance
# - play time
# - maximum speed
# - achievements
# - settings
#
# Desktop:
#     JSON files in saves/
#
# Browser / Pygbag:
#     browser localStorage
#
# Online leaderboard data is NOT saved here.
#
# ============================================================


# ============================================================
# PLATFORM
# ============================================================

IS_WEB = sys.platform in (
    "emscripten",
    "wasi",
)


# ============================================================
# BROWSER STORAGE KEYS
# ============================================================

BROWSER_PROGRESS_KEY = (
    "matthews-games-tunnel-runner-progress"
)

BROWSER_SETTINGS_KEY = (
    "matthews-games-tunnel-runner-settings"
)

BROWSER_STATISTICS_KEY = (
    "matthews-games-tunnel-runner-statistics"
)


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_int(
    value: Any,
    default: int = 0,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    try:
        if isinstance(
            value,
            bool,
        ):
            result = default

        else:
            result = int(
                value
            )

    except (
        TypeError,
        ValueError,
    ):
        result = default

    if minimum is not None:
        result = max(
            minimum,
            result,
        )

    if maximum is not None:
        result = min(
            maximum,
            result,
        )

    return result


def safe_float(
    value: Any,
    default: float = 0.0,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    try:
        if isinstance(
            value,
            bool,
        ):
            result = default

        else:
            result = float(
                value
            )

    except (
        TypeError,
        ValueError,
    ):
        result = default

    if minimum is not None:
        result = max(
            minimum,
            result,
        )

    if maximum is not None:
        result = min(
            maximum,
            result,
        )

    return result


def safe_bool(
    value: Any,
    default: bool = False,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        cleaned = (
            value
            .strip()
            .lower()
        )

        if cleaned in (
            "true",
            "yes",
            "1",
            "on",
        ):
            return True

        if cleaned in (
            "false",
            "no",
            "0",
            "off",
        ):
            return False

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return bool(
            value
        )

    return default


def safe_string(
    value: Any,
    default: str = "",
) -> str:
    if value is None:
        return default

    try:
        return str(
            value
        )

    except Exception:
        return default


def safe_dictionary(
    value: Any,
) -> dict[str, Any]:
    if isinstance(
        value,
        dict,
    ):
        return dict(
            value
        )

    return {}


def safe_string_list(
    value: Any,
) -> list[str]:
    if not isinstance(
        value,
        list,
    ):
        return []

    result: list[str] = []

    for item in value:
        cleaned = (
            safe_string(
                item
            )
            .strip()
        )

        if (
            cleaned
            and cleaned
            not in result
        ):
            result.append(
                cleaned
            )

    return result


def safe_level_list(
    value: Any,
) -> list[int]:
    if not isinstance(
        value,
        list,
    ):
        return []

    result: list[int] = []

    for item in value:
        level_number = safe_int(
            item,
            -1,
        )

        if (
            1
            <= level_number
            <= TOTAL_LEVELS
            and level_number
            not in result
        ):
            result.append(
                level_number
            )

    result.sort()

    return result


# ============================================================
# DEEP DEFAULT MERGE
# ============================================================

def merge_defaults(
    defaults: dict[str, Any],
    loaded: dict[str, Any],
) -> dict[str, Any]:
    result = copy.deepcopy(
        defaults
    )

    for (
        key,
        value,
    ) in loaded.items():

        if (
            key in result
            and isinstance(
                result[key],
                dict,
            )
            and isinstance(
                value,
                dict,
            )
        ):
            result[key] = (
                merge_defaults(
                    result[key],
                    value,
                )
            )

        else:
            result[key] = (
                copy.deepcopy(
                    value
                )
            )

    return result


# ============================================================
# DESKTOP JSON HELPERS
# ============================================================

def read_json_file(
    path: Path,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    try:
        if not path.exists():
            return copy.deepcopy(
                defaults
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            loaded = json.load(
                file
            )

        if not isinstance(
            loaded,
            dict,
        ):
            return copy.deepcopy(
                defaults
            )

        return merge_defaults(
            defaults,
            loaded,
        )

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return copy.deepcopy(
            defaults
        )


def write_json_file(
    path: Path,
    data: dict[str, Any],
) -> bool:
    temporary_path = (
        path.with_suffix(
            path.suffix
            + ".tmp"
        )
    )

    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )

        temporary_path.replace(
            path
        )

        return True

    except (
        OSError,
        TypeError,
        ValueError,
    ):
        try:
            if temporary_path.exists():
                temporary_path.unlink()

        except OSError:
            pass

        return False


# ============================================================
# BROWSER JSON HELPERS
# ============================================================

def browser_read_json(
    key: str,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    if not IS_WEB:
        return copy.deepcopy(
            defaults
        )

    try:
        import platform

        raw_value = (
            platform.window
            .localStorage
            .getItem(
                key
            )
        )

        if not raw_value:
            return copy.deepcopy(
                defaults
            )

        loaded = json.loads(
            str(
                raw_value
            )
        )

        if not isinstance(
            loaded,
            dict,
        ):
            return copy.deepcopy(
                defaults
            )

        return merge_defaults(
            defaults,
            loaded,
        )

    except Exception:
        return copy.deepcopy(
            defaults
        )


def browser_write_json(
    key: str,
    data: dict[str, Any],
) -> bool:
    if not IS_WEB:
        return False

    try:
        import platform

        encoded = json.dumps(
            data
        )

        platform.window.localStorage.setItem(
            key,
            encoded,
        )

        return True

    except Exception:
        return False


# ============================================================
# STORAGE MANAGER
# ============================================================

class StorageManager:
    def __init__(
        self,
    ):
        self.progress: dict[
            str,
            Any,
        ] = {}

        self.settings: dict[
            str,
            Any,
        ] = {}

        self.statistics: dict[
            str,
            Any,
        ] = {}

        self.new_achievements: list[
            str
        ] = []

        self.load_all()

    # ========================================================
    # LOAD
    # ========================================================

    def load_all(
        self,
    ) -> None:
        if IS_WEB:
            self.progress = (
                browser_read_json(
                    BROWSER_PROGRESS_KEY,
                    DEFAULT_SAVE_DATA,
                )
            )

            self.settings = (
                browser_read_json(
                    BROWSER_SETTINGS_KEY,
                    DEFAULT_SETTINGS_DATA,
                )
            )

            self.statistics = (
                browser_read_json(
                    BROWSER_STATISTICS_KEY,
                    DEFAULT_STATISTICS_DATA,
                )
            )

        else:
            self.progress = (
                read_json_file(
                    SAVE_FILE,
                    DEFAULT_SAVE_DATA,
                )
            )

            self.settings = (
                read_json_file(
                    SETTINGS_FILE,
                    DEFAULT_SETTINGS_DATA,
                )
            )

            self.statistics = (
                read_json_file(
                    STATISTICS_FILE,
                    DEFAULT_STATISTICS_DATA,
                )
            )

        self._sanitize_progress()
        self._sanitize_settings()
        self._sanitize_statistics()

        self.check_achievements()

    # ========================================================
    # SAVE
    # ========================================================

    def save_all(
        self,
    ) -> bool:
        self._sanitize_progress()
        self._sanitize_settings()
        self._sanitize_statistics()

        if IS_WEB:
            progress_saved = (
                browser_write_json(
                    BROWSER_PROGRESS_KEY,
                    self.progress,
                )
            )

            settings_saved = (
                browser_write_json(
                    BROWSER_SETTINGS_KEY,
                    self.settings,
                )
            )

            statistics_saved = (
                browser_write_json(
                    BROWSER_STATISTICS_KEY,
                    self.statistics,
                )
            )

        else:
            progress_saved = (
                write_json_file(
                    SAVE_FILE,
                    self.progress,
                )
            )

            settings_saved = (
                write_json_file(
                    SETTINGS_FILE,
                    self.settings,
                )
            )

            statistics_saved = (
                write_json_file(
                    STATISTICS_FILE,
                    self.statistics,
                )
            )

        return (
            progress_saved
            and settings_saved
            and statistics_saved
        )

    def save_progress(
        self,
    ) -> bool:
        self._sanitize_progress()

        if IS_WEB:
            return browser_write_json(
                BROWSER_PROGRESS_KEY,
                self.progress,
            )

        return write_json_file(
            SAVE_FILE,
            self.progress,
        )

    def save_settings(
        self,
    ) -> bool:
        self._sanitize_settings()

        if IS_WEB:
            return browser_write_json(
                BROWSER_SETTINGS_KEY,
                self.settings,
            )

        return write_json_file(
            SETTINGS_FILE,
            self.settings,
        )

    def save_statistics(
        self,
    ) -> bool:
        self._sanitize_statistics()

        if IS_WEB:
            return browser_write_json(
                BROWSER_STATISTICS_KEY,
                self.statistics,
            )

        return write_json_file(
            STATISTICS_FILE,
            self.statistics,
        )

    # ========================================================
    # SANITIZE PROGRESS
    # ========================================================

    def _sanitize_progress(
        self,
    ) -> None:
        self.progress = merge_defaults(
            DEFAULT_SAVE_DATA,
            self.progress,
        )

        self.progress[
            "save_version"
        ] = safe_int(
            self.progress.get(
                "save_version",
                1,
            ),
            1,
            minimum=1,
        )

        self.progress[
            "highest_unlocked_level"
        ] = safe_int(
            self.progress.get(
                "highest_unlocked_level",
                1,
            ),
            1,
            minimum=1,
            maximum=TOTAL_LEVELS,
        )

        self.progress[
            "completed_levels"
        ] = safe_level_list(
            self.progress.get(
                "completed_levels",
                [],
            )
        )

        self.progress[
            "level_best_times"
        ] = self._sanitize_level_float_dict(
            self.progress.get(
                "level_best_times",
                {},
            )
        )

        self.progress[
            "level_attempts"
        ] = self._sanitize_level_int_dict(
            self.progress.get(
                "level_attempts",
                {},
            )
        )

        self.progress[
            "endless_best_distance"
        ] = safe_int(
            self.progress.get(
                "endless_best_distance",
                0,
            ),
            0,
            minimum=0,
        )

        self.progress[
            "total_runs"
        ] = safe_int(
            self.progress.get(
                "total_runs",
                0,
            ),
            0,
            minimum=0,
        )

        self.progress[
            "total_crashes"
        ] = safe_int(
            self.progress.get(
                "total_crashes",
                0,
            ),
            0,
            minimum=0,
        )

        self.progress[
            "total_distance"
        ] = safe_int(
            self.progress.get(
                "total_distance",
                0,
            ),
            0,
            minimum=0,
        )

        achievements = (
            safe_string_list(
                self.progress.get(
                    "achievements",
                    [],
                )
            )
        )

        self.progress[
            "achievements"
        ] = [
            achievement_id
            for achievement_id
            in achievements
            if achievement_id
            in ACHIEVEMENT_DEFINITIONS
        ]

    # ========================================================
    # SANITIZE SETTINGS
    # ========================================================

    def _sanitize_settings(
        self,
    ) -> None:
        self.settings = merge_defaults(
            DEFAULT_SETTINGS_DATA,
            self.settings,
        )

        boolean_keys = (
            "fullscreen",
            "screen_shake",
            "particles",
            "speed_lines",
            "glow",
            "show_fps",
            "music_enabled",
            "sfx_enabled",
        )

        for key in boolean_keys:
            self.settings[
                key
            ] = safe_bool(
                self.settings.get(
                    key,
                    DEFAULT_SETTINGS_DATA.get(
                        key,
                        False,
                    ),
                ),
                bool(
                    DEFAULT_SETTINGS_DATA.get(
                        key,
                        False,
                    )
                ),
            )

        volume_keys = (
            "master_volume",
            "music_volume",
            "sfx_volume",
        )

        for key in volume_keys:
            self.settings[
                key
            ] = safe_float(
                self.settings.get(
                    key,
                    DEFAULT_SETTINGS_DATA.get(
                        key,
                        1.0,
                    ),
                ),
                float(
                    DEFAULT_SETTINGS_DATA.get(
                        key,
                        1.0,
                    )
                ),
                minimum=0.0,
                maximum=1.0,
            )

    # ========================================================
    # SANITIZE STATISTICS
    # ========================================================

    def _sanitize_statistics(
        self,
    ) -> None:
        self.statistics = merge_defaults(
            DEFAULT_STATISTICS_DATA,
            self.statistics,
        )

        integer_keys = (
            "total_runs",
            "campaign_runs",
            "endless_runs",
            "total_crashes",
            "levels_completed",
            "total_distance",
            "total_play_time_seconds",
            "longest_endless_run",
        )

        for key in integer_keys:
            self.statistics[
                key
            ] = safe_int(
                self.statistics.get(
                    key,
                    0,
                ),
                0,
                minimum=0,
            )

        self.statistics[
            "maximum_speed"
        ] = safe_float(
            self.statistics.get(
                "maximum_speed",
                0.0,
            ),
            0.0,
            minimum=0.0,
        )

    # ========================================================
    # LEVEL DICTIONARY CLEANERS
    # ========================================================

    def _sanitize_level_float_dict(
        self,
        value: Any,
    ) -> dict[str, float]:
        raw = safe_dictionary(
            value
        )

        result: dict[
            str,
            float,
        ] = {}

        for (
            key,
            item,
        ) in raw.items():
            level_number = safe_int(
                key,
                -1,
            )

            if not (
                1
                <= level_number
                <= TOTAL_LEVELS
            ):
                continue

            result[
                str(
                    level_number
                )
            ] = safe_float(
                item,
                0.0,
                minimum=0.0,
            )

        return result

    def _sanitize_level_int_dict(
        self,
        value: Any,
    ) -> dict[str, int]:
        raw = safe_dictionary(
            value
        )

        result: dict[
            str,
            int,
        ] = {}

        for (
            key,
            item,
        ) in raw.items():
            level_number = safe_int(
                key,
                -1,
            )

            if not (
                1
                <= level_number
                <= TOTAL_LEVELS
            ):
                continue

            result[
                str(
                    level_number
                )
            ] = safe_int(
                item,
                0,
                minimum=0,
            )

        return result

    # ========================================================
    # PROGRESSION
    # ========================================================

    @property
    def highest_unlocked_level(
        self,
    ) -> int:
        return safe_int(
            self.progress.get(
                "highest_unlocked_level",
                1,
            ),
            1,
            minimum=1,
            maximum=TOTAL_LEVELS,
        )

    @property
    def completed_levels(
        self,
    ) -> list[int]:
        return safe_level_list(
            self.progress.get(
                "completed_levels",
                [],
            )
        )

    def is_level_unlocked(
        self,
        level_number: int,
    ) -> bool:
        level_number = safe_int(
            level_number,
            0,
        )

        return (
            1
            <= level_number
            <= self.highest_unlocked_level
        )

    def is_level_completed(
        self,
        level_number: int,
    ) -> bool:
        return (
            safe_int(
                level_number,
                0,
            )
            in self.completed_levels
        )

    def unlock_level(
        self,
        level_number: int,
    ) -> bool:
        level_number = safe_int(
            level_number,
            1,
            minimum=1,
            maximum=TOTAL_LEVELS,
        )

        if (
            level_number
            <= self.highest_unlocked_level
        ):
            return False

        self.progress[
            "highest_unlocked_level"
        ] = level_number

        self.save_progress()

        return True

    # ========================================================
    # LEVEL ATTEMPTS
    # ========================================================

    def get_level_attempts(
        self,
        level_number: int,
    ) -> int:
        attempts = safe_dictionary(
            self.progress.get(
                "level_attempts",
                {},
            )
        )

        return safe_int(
            attempts.get(
                str(
                    level_number
                ),
                0,
            ),
            0,
            minimum=0,
        )

    def _increment_level_attempt(
        self,
        level_number: int,
    ) -> None:
        attempts = safe_dictionary(
            self.progress.get(
                "level_attempts",
                {},
            )
        )

        key = str(
            level_number
        )

        attempts[
            key
        ] = (
            safe_int(
                attempts.get(
                    key,
                    0,
                ),
                0,
                minimum=0,
            )
            + 1
        )

        self.progress[
            "level_attempts"
        ] = attempts

    # ========================================================
    # LEVEL BEST TIME
    # ========================================================

    def get_level_best_time(
        self,
        level_number: int,
    ) -> float:
        values = safe_dictionary(
            self.progress.get(
                "level_best_times",
                {},
            )
        )

        return safe_float(
            values.get(
                str(
                    level_number
                ),
                0.0,
            ),
            0.0,
            minimum=0.0,
        )

    def _update_level_best_time(
        self,
        level_number: int,
        play_time_seconds: float,
    ) -> bool:
        play_time_seconds = safe_float(
            play_time_seconds,
            0.0,
            minimum=0.0,
        )

        if play_time_seconds <= 0.0:
            return False

        values = safe_dictionary(
            self.progress.get(
                "level_best_times",
                {},
            )
        )

        key = str(
            level_number
        )

        current = safe_float(
            values.get(
                key,
                0.0,
            ),
            0.0,
            minimum=0.0,
        )

        if (
            current > 0.0
            and play_time_seconds
            >= current
        ):
            return False

        values[
            key
        ] = play_time_seconds

        self.progress[
            "level_best_times"
        ] = values

        return True

    # ========================================================
    # CAMPAIGN START
    # ========================================================

    def record_level_start(
        self,
        level_number: int,
    ) -> None:
        level_number = safe_int(
            level_number,
            1,
            minimum=1,
            maximum=TOTAL_LEVELS,
        )

        self._increment_level_attempt(
            level_number
        )

        self.progress[
            "total_runs"
        ] = (
            safe_int(
                self.progress.get(
                    "total_runs",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.statistics[
            "total_runs"
        ] = (
            safe_int(
                self.statistics.get(
                    "total_runs",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.statistics[
            "campaign_runs"
        ] = (
            safe_int(
                self.statistics.get(
                    "campaign_runs",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.unlock_achievement(
            "first_run"
        )

        self.save_all()

    # ========================================================
    # CAMPAIGN CRASH
    # ========================================================

    def record_level_crash(
        self,
        level_number: int,
        *,
        distance: float,
        play_time_seconds: float,
        maximum_speed: float,
    ) -> None:
        self._record_crash()

        self._add_distance(
            distance
        )

        self._add_play_time(
            play_time_seconds
        )

        self._update_maximum_speed(
            maximum_speed
        )

        self.check_achievements()

        self.save_all()

    # ========================================================
    # CAMPAIGN COMPLETE
    # ========================================================

    def record_level_completion(
        self,
        level_number: int,
        *,
        distance: float,
        play_time_seconds: float,
        maximum_speed: float,
    ) -> tuple[
        bool,
        bool,
    ]:
        """
        Returns:
            first_completion
            new_best_time
        """

        level_number = safe_int(
            level_number,
            1,
            minimum=1,
            maximum=TOTAL_LEVELS,
        )

        completed = (
            self.completed_levels
        )

        first_completion = (
            level_number
            not in completed
        )

        if first_completion:
            completed.append(
                level_number
            )

            completed.sort()

            self.progress[
                "completed_levels"
            ] = completed

            self.statistics[
                "levels_completed"
            ] = (
                safe_int(
                    self.statistics.get(
                        "levels_completed",
                        0,
                    ),
                    minimum=0,
                )
                + 1
            )

        if (
            level_number
            < TOTAL_LEVELS
        ):
            next_level = (
                level_number
                + 1
            )

            if (
                next_level
                > self.highest_unlocked_level
            ):
                self.progress[
                    "highest_unlocked_level"
                ] = next_level

        new_best_time = (
            self._update_level_best_time(
                level_number,
                play_time_seconds,
            )
        )

        self._add_distance(
            distance
        )

        self._add_play_time(
            play_time_seconds
        )

        self._update_maximum_speed(
            maximum_speed
        )

        self.check_achievements()

        self.save_all()

        return (
            first_completion,
            new_best_time,
        )

    # ========================================================
    # ENDLESS START
    # ========================================================

    def record_endless_start(
        self,
    ) -> None:
        self.progress[
            "total_runs"
        ] = (
            safe_int(
                self.progress.get(
                    "total_runs",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.statistics[
            "total_runs"
        ] = (
            safe_int(
                self.statistics.get(
                    "total_runs",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.statistics[
            "endless_runs"
        ] = (
            safe_int(
                self.statistics.get(
                    "endless_runs",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.unlock_achievement(
            "first_run"
        )

        self.save_all()

    # ========================================================
    # ENDLESS BEST
    # ========================================================

    @property
    def endless_best_distance(
        self,
    ) -> int:
        return safe_int(
            self.progress.get(
                "endless_best_distance",
                0,
            ),
            0,
            minimum=0,
        )

    # ========================================================
    # ENDLESS CRASH
    # ========================================================

    def record_endless_run(
        self,
        *,
        distance: float,
        play_time_seconds: float,
        maximum_speed: float,
    ) -> tuple[
        int,
        bool,
    ]:
        cleaned_distance = max(
            0,
            round(
                safe_float(
                    distance,
                    0.0,
                )
            ),
        )

        previous_best = (
            self.endless_best_distance
        )

        new_personal_best = (
            cleaned_distance
            > previous_best
        )

        if new_personal_best:
            self.progress[
                "endless_best_distance"
            ] = cleaned_distance

        self.statistics[
            "longest_endless_run"
        ] = max(
            safe_int(
                self.statistics.get(
                    "longest_endless_run",
                    0,
                ),
                minimum=0,
            ),
            cleaned_distance,
        )

        self._record_crash()

        self._add_distance(
            distance
        )

        self._add_play_time(
            play_time_seconds
        )

        self._update_maximum_speed(
            maximum_speed
        )

        self.check_achievements()

        self.save_all()

        return (
            self.endless_best_distance,
            new_personal_best,
        )

    # ========================================================
    # SHARED CRASH
    # ========================================================

    def _record_crash(
        self,
    ) -> None:
        self.progress[
            "total_crashes"
        ] = (
            safe_int(
                self.progress.get(
                    "total_crashes",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

        self.statistics[
            "total_crashes"
        ] = (
            safe_int(
                self.statistics.get(
                    "total_crashes",
                    0,
                ),
                minimum=0,
            )
            + 1
        )

    # ========================================================
    # DISTANCE
    # ========================================================

    def _add_distance(
        self,
        distance: float,
    ) -> None:
        cleaned_distance = max(
            0,
            round(
                safe_float(
                    distance,
                    0.0,
                )
            ),
        )

        self.progress[
            "total_distance"
        ] = (
            safe_int(
                self.progress.get(
                    "total_distance",
                    0,
                ),
                minimum=0,
            )
            + cleaned_distance
        )

        self.statistics[
            "total_distance"
        ] = (
            safe_int(
                self.statistics.get(
                    "total_distance",
                    0,
                ),
                minimum=0,
            )
            + cleaned_distance
        )

    # ========================================================
    # PLAY TIME
    # ========================================================

    def _add_play_time(
        self,
        seconds: float,
    ) -> None:
        cleaned_seconds = max(
            0,
            round(
                safe_float(
                    seconds,
                    0.0,
                )
            ),
        )

        self.statistics[
            "total_play_time_seconds"
        ] = (
            safe_int(
                self.statistics.get(
                    "total_play_time_seconds",
                    0,
                ),
                minimum=0,
            )
            + cleaned_seconds
        )

    # ========================================================
    # MAXIMUM SPEED
    # ========================================================

    def _update_maximum_speed(
        self,
        speed: float,
    ) -> None:
        cleaned_speed = max(
            0.0,
            safe_float(
                speed,
                0.0,
            ),
        )

        self.statistics[
            "maximum_speed"
        ] = max(
            safe_float(
                self.statistics.get(
                    "maximum_speed",
                    0.0,
                ),
                minimum=0.0,
            ),
            cleaned_speed,
        )

    # ========================================================
    # STATS ACCESS
    # ========================================================

    def total_runs(
        self,
    ) -> int:
        return safe_int(
            self.statistics.get(
                "total_runs",
                0,
            ),
            minimum=0,
        )

    def total_crashes(
        self,
    ) -> int:
        return safe_int(
            self.statistics.get(
                "total_crashes",
                0,
            ),
            minimum=0,
        )

    def total_distance(
        self,
    ) -> int:
        return safe_int(
            self.statistics.get(
                "total_distance",
                0,
            ),
            minimum=0,
        )

    def total_play_time_seconds(
        self,
    ) -> int:
        return safe_int(
            self.statistics.get(
                "total_play_time_seconds",
                0,
            ),
            minimum=0,
        )

    def maximum_speed_reached(
        self,
    ) -> float:
        return safe_float(
            self.statistics.get(
                "maximum_speed",
                0.0,
            ),
            minimum=0.0,
        )

    def campaign_runs(
        self,
    ) -> int:
        return safe_int(
            self.statistics.get(
                "campaign_runs",
                0,
            ),
            minimum=0,
        )

    def endless_runs(
        self,
    ) -> int:
        return safe_int(
            self.statistics.get(
                "endless_runs",
                0,
            ),
            minimum=0,
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def get_setting(
        self,
        setting_name: str,
        default: Any = None,
    ) -> Any:
        return self.settings.get(
            setting_name,
            default,
        )

    def set_setting(
        self,
        setting_name: str,
        value: Any,
    ) -> bool:
        if (
            setting_name
            not in DEFAULT_SETTINGS_DATA
        ):
            return False

        default_value = (
            DEFAULT_SETTINGS_DATA[
                setting_name
            ]
        )

        if isinstance(
            default_value,
            bool,
        ):
            cleaned_value = safe_bool(
                value,
                default_value,
            )

        elif isinstance(
            default_value,
            float,
        ):
            cleaned_value = safe_float(
                value,
                default_value,
                minimum=0.0,
                maximum=1.0,
            )

        else:
            cleaned_value = value

        self.settings[
            setting_name
        ] = cleaned_value

        return self.save_settings()

    def toggle_setting(
        self,
        setting_name: str,
    ) -> bool:
        current = (
            self.settings.get(
                setting_name
            )
        )

        if not isinstance(
            current,
            bool,
        ):
            return False

        self.settings[
            setting_name
        ] = not current

        self.save_settings()

        return True

    # ========================================================
    # SETTING PROPERTIES
    # ========================================================

    @property
    def fullscreen_enabled(
        self,
    ) -> bool:
        return safe_bool(
            self.settings.get(
                "fullscreen",
                False,
            )
        )

    @property
    def screen_shake_enabled(
        self,
    ) -> bool:
        return safe_bool(
            self.settings.get(
                "screen_shake",
                True,
            ),
            True,
        )

    @property
    def particles_enabled(
        self,
    ) -> bool:
        return safe_bool(
            self.settings.get(
                "particles",
                True,
            ),
            True,
        )

    @property
    def speed_lines_enabled(
        self,
    ) -> bool:
        return safe_bool(
            self.settings.get(
                "speed_lines",
                True,
            ),
            True,
        )

    @property
    def glow_enabled(
        self,
    ) -> bool:
        return safe_bool(
            self.settings.get(
                "glow",
                True,
            ),
            True,
        )

    @property
    def show_fps(
        self,
    ) -> bool:
        return safe_bool(
            self.settings.get(
                "show_fps",
                False,
            ),
            False,
        )

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    @property
    def unlocked_achievements(
        self,
    ) -> list[str]:
        return safe_string_list(
            self.progress.get(
                "achievements",
                [],
            )
        )

    def has_achievement(
        self,
        achievement_id: str,
    ) -> bool:
        return (
            achievement_id
            in self.unlocked_achievements
        )

    def unlock_achievement(
        self,
        achievement_id: str,
    ) -> bool:
        if (
            achievement_id
            not in ACHIEVEMENT_DEFINITIONS
        ):
            return False

        if self.has_achievement(
            achievement_id
        ):
            return False

        achievements = (
            self.unlocked_achievements
        )

        achievements.append(
            achievement_id
        )

        self.progress[
            "achievements"
        ] = achievements

        if (
            achievement_id
            not in self.new_achievements
        ):
            self.new_achievements.append(
                achievement_id
            )

        return True

    def check_achievements(
        self,
    ) -> list[str]:
        before = set(
            self.unlocked_achievements
        )

        if self.total_runs() >= 1:
            self.unlock_achievement(
                "first_run"
            )

        completed = set(
            self.completed_levels
        )

        if 1 in completed:
            self.unlock_achievement(
                "first_level"
            )

        if 10 in completed:
            self.unlock_achievement(
                "level_10"
            )

        if 25 in completed:
            self.unlock_achievement(
                "level_25"
            )

        if 50 in completed:
            self.unlock_achievement(
                "level_50"
            )

        best = (
            self.endless_best_distance
        )

        if best >= 500:
            self.unlock_achievement(
                "endless_500"
            )

        if best >= 1000:
            self.unlock_achievement(
                "endless_1000"
            )

        if best >= 2500:
            self.unlock_achievement(
                "endless_2500"
            )

        if best >= 5000:
            self.unlock_achievement(
                "endless_5000"
            )

        if best >= 10000:
            self.unlock_achievement(
                "endless_10000"
            )

        after = set(
            self.unlocked_achievements
        )

        return [
            achievement_id
            for achievement_id
            in after
            if achievement_id
            not in before
        ]

    def consume_new_achievements(
        self,
    ) -> list[str]:
        result = list(
            self.new_achievements
        )

        self.new_achievements.clear()

        return result

    # ========================================================
    # RESET PROGRESS
    # ========================================================

    def reset_progress(
        self,
    ) -> None:
        self.progress = (
            copy.deepcopy(
                DEFAULT_SAVE_DATA
            )
        )

        self.statistics = (
            copy.deepcopy(
                DEFAULT_STATISTICS_DATA
            )
        )

        self.new_achievements.clear()

        self.save_progress()
        self.save_statistics()

    # ========================================================
    # RESET SETTINGS
    # ========================================================

    def reset_settings(
        self,
    ) -> None:
        self.settings = (
            copy.deepcopy(
                DEFAULT_SETTINGS_DATA
            )
        )

        self.save_settings()

    # ========================================================
    # RESET EVERYTHING
    # ========================================================

    def reset_everything(
        self,
    ) -> None:
        self.progress = (
            copy.deepcopy(
                DEFAULT_SAVE_DATA
            )
        )

        self.settings = (
            copy.deepcopy(
                DEFAULT_SETTINGS_DATA
            )
        )

        self.statistics = (
            copy.deepcopy(
                DEFAULT_STATISTICS_DATA
            )
        )

        self.new_achievements.clear()

        self.save_all()


# ============================================================
# FORMATTING HELPERS
# ============================================================

def format_play_time(
    total_seconds: int | float,
) -> str:
    seconds = max(
        0,
        round(
            total_seconds
        ),
    )

    hours = (
        seconds
        // 3600
    )

    minutes = (
        (
            seconds
            % 3600
        )
        // 60
    )

    remaining_seconds = (
        seconds
        % 60
    )

    if hours > 0:
        return (
            f"{hours}h "
            f"{minutes}m "
            f"{remaining_seconds}s"
        )

    if minutes > 0:
        return (
            f"{minutes}m "
            f"{remaining_seconds}s"
        )

    return (
        f"{remaining_seconds}s"
    )


def format_level_time(
    seconds: float,
) -> str:
    seconds = max(
        0.0,
        float(
            seconds
        ),
    )

    minutes = int(
        seconds
        // 60
    )

    remaining = (
        seconds
        % 60.0
    )

    if minutes > 0:
        return (
            f"{minutes}:"
            f"{remaining:05.2f}"
        )

    return (
        f"{remaining:.2f}s"
    )


# ============================================================
# ACHIEVEMENT DISPLAY HELPERS
# ============================================================

def get_achievement_name(
    achievement_id: str,
) -> str:
    definition = (
        ACHIEVEMENT_DEFINITIONS.get(
            achievement_id,
            {},
        )
    )

    return safe_string(
        definition.get(
            "name",
            "Achievement",
        )
    )


def get_achievement_description(
    achievement_id: str,
) -> str:
    definition = (
        ACHIEVEMENT_DEFINITIONS.get(
            achievement_id,
            {},
        )
    )

    return safe_string(
        definition.get(
            "description",
            "",
        )
    )


def achievement_is_hidden(
    achievement_id: str,
) -> bool:
    definition = (
        ACHIEVEMENT_DEFINITIONS.get(
            achievement_id,
            {},
        )
    )

    return safe_bool(
        definition.get(
            "hidden",
            False,
        )
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_storage_defaults(
) -> None:
    required_progress_keys = (
        "highest_unlocked_level",
        "completed_levels",
        "level_best_times",
        "level_attempts",
        "endless_best_distance",
        "total_runs",
        "total_crashes",
        "total_distance",
        "achievements",
    )

    for key in required_progress_keys:
        if (
            key
            not in DEFAULT_SAVE_DATA
        ):
            raise ValueError(
                "DEFAULT_SAVE_DATA is missing: "
                f"{key}"
            )

    required_settings = (
        "fullscreen",
        "screen_shake",
        "particles",
        "speed_lines",
        "glow",
        "show_fps",
    )

    for key in required_settings:
        if (
            key
            not in DEFAULT_SETTINGS_DATA
        ):
            raise ValueError(
                "DEFAULT_SETTINGS_DATA is missing: "
                f"{key}"
            )

    required_statistics = (
        "total_runs",
        "campaign_runs",
        "endless_runs",
        "total_crashes",
        "levels_completed",
        "total_distance",
        "total_play_time_seconds",
        "maximum_speed",
        "longest_endless_run",
    )

    for key in required_statistics:
        if (
            key
            not in DEFAULT_STATISTICS_DATA
        ):
            raise ValueError(
                "DEFAULT_STATISTICS_DATA is missing: "
                f"{key}"
            )


validate_storage_defaults()