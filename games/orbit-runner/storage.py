from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from config import CAMPAIGN_LEVELS, DEFAULT_SAVE, DEFAULT_SETTINGS, SAVE_FILE, SETTINGS_FILE, ensure_directories


class SaveManager:
    def __init__(self) -> None:
        ensure_directories()
        self.data: dict[str, Any] = deepcopy(DEFAULT_SAVE)
        self.settings: dict[str, Any] = deepcopy(DEFAULT_SETTINGS)
        self.load()

    @staticmethod
    def _read(path, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                result = deepcopy(fallback)
                result.update(raw)
                return result
        except (OSError, json.JSONDecodeError):
            pass
        return deepcopy(fallback)

    @staticmethod
    def _write(path, data: dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            pass

    def load(self) -> None:
        self.data = self._read(SAVE_FILE, DEFAULT_SAVE)
        self.settings = self._read(SETTINGS_FILE, DEFAULT_SETTINGS)
        self._sanitize()

    def _sanitize(self) -> None:
        try:
            unlocked = int(self.data.get("highest_unlocked_level", 1))
        except (TypeError, ValueError):
            unlocked = 1
        self.data["highest_unlocked_level"] = max(1, min(CAMPAIGN_LEVELS, unlocked))

        completed = self.data.get("completed_levels", [])
        if not isinstance(completed, list):
            completed = []
        self.data["completed_levels"] = sorted({
            int(level) for level in completed
            if isinstance(level, int) and 1 <= level <= CAMPAIGN_LEVELS
        })

        for key in ("endless_best_distance", "total_distance", "total_runs", "total_crashes"):
            try:
                self.data[key] = max(0, int(self.data.get(key, 0)))
            except (TypeError, ValueError):
                self.data[key] = 0

    def save(self) -> None:
        self._write(SAVE_FILE, self.data)
        self._write(SETTINGS_FILE, self.settings)

    @property
    def highest_unlocked_level(self) -> int:
        return int(self.data["highest_unlocked_level"])

    @property
    def endless_best_distance(self) -> int:
        return int(self.data["endless_best_distance"])

    def is_level_complete(self, level_number: int) -> bool:
        return level_number in self.data["completed_levels"]

    def record_crash(self, distance: float, endless: bool) -> int:
        metres = max(0, round(distance))
        self.data["total_runs"] += 1
        self.data["total_crashes"] += 1
        self.data["total_distance"] += metres
        if endless:
            self.data["endless_best_distance"] = max(
                self.endless_best_distance,
                metres,
            )
        self.save()
        return self.endless_best_distance

    def record_level_complete(self, level_number: int, distance: float, time_ms: int) -> None:
        completed = set(self.data["completed_levels"])
        completed.add(level_number)
        self.data["completed_levels"] = sorted(completed)
        self.data["highest_unlocked_level"] = min(
            CAMPAIGN_LEVELS,
            max(self.highest_unlocked_level, level_number + 1),
        )

        distances = dict(self.data.get("level_best_distances", {}))
        distances[str(level_number)] = max(
            int(distances.get(str(level_number), 0)),
            round(distance),
        )
        self.data["level_best_distances"] = distances

        times = dict(self.data.get("level_best_times_ms", {}))
        previous = int(times.get(str(level_number), 0) or 0)
        if previous == 0 or time_ms < previous:
            times[str(level_number)] = max(1, int(time_ms))
        self.data["level_best_times_ms"] = times

        self.data["total_runs"] += 1
        self.data["total_distance"] += max(0, round(distance))
        self.save()
