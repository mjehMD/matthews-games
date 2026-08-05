from __future__ import annotations

import asyncio
import json
import platform
import sys
import urllib.parse
from typing import Any


SUPABASE_PROJECT_URL = "https://bcarxudxfmsibvnteoaj.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_S7ki2S3tODs4shwWovSY6w_-2jknXXg"
SCORES_ENDPOINT = f"{SUPABASE_PROJECT_URL}/rest/v1/scores"

GAME_NAME = "space-shooter"
MAX_LEADERBOARD_ENTRIES = 10
IS_WEB = sys.platform in ("emscripten", "wasi")


def clean_player_name(value: Any) -> str:
    name = str(value).strip()[:16]
    return name or "Player"


def clean_score(value: Any) -> int:
    try:
        return max(0, min(100_000_000, int(value)))
    except (TypeError, ValueError):
        return 0


def clean_wave(value: Any) -> int:
    try:
        return max(1, min(100_000, int(value)))
    except (TypeError, ValueError):
        return 1


def clean_entries(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        return []

    entries: list[dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        entries.append(
            {
                "name": clean_player_name(
                    item.get("player_name", "Player")
                ),
                "score": clean_score(item.get("score", 0)),
                "wave": clean_wave(item.get("wave", 1)),
            }
        )

    entries.sort(
        key=lambda entry: (entry["score"], entry["wave"]),
        reverse=True,
    )

    return entries[:MAX_LEADERBOARD_ENTRIES]


_BROWSER_FETCH_READY = False


def install_browser_fetch() -> None:
    global _BROWSER_FETCH_READY

    if not IS_WEB or _BROWSER_FETCH_READY:
        return

    platform.window.eval("""
        window.MatthewsLeaderboardFetch = {
            request: function* (
                method,
                url,
                apiKey,
                token,
                bodyText,
                prefer
            ) {
                let finished = false;
                let result = "";

                const headers = {
                    "apikey": apiKey,
                    "Authorization": "Bearer " + token,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                };

                if (prefer) {
                    headers["Prefer"] = prefer;
                }

                const options = {
                    method: method,
                    headers: headers
                };

                if (bodyText) {
                    options.body = bodyText;
                }

                fetch(url, options)
                .then(async response => {
                    result = JSON.stringify({
                        ok: response.ok,
                        status: response.status,
                        text: await response.text()
                    });
                    finished = true;
                })
                .catch(error => {
                    result = JSON.stringify({
                        ok: false,
                        status: 0,
                        text: String(error)
                    });
                    finished = true;
                });

                while (!finished) {
                    yield;
                }

                yield result;
            }
        };
    """)

    _BROWSER_FETCH_READY = True


async def make_request(
    method: str,
    url: str,
    access_token: str = "",
    body: dict[str, Any] | None = None,
    prefer: str = "",
) -> tuple[bool, int, str]:
    if not IS_WEB:
        return (
            False,
            0,
            "Online leaderboards require the website version.",
        )

    install_browser_fetch()

    token = access_token or SUPABASE_PUBLISHABLE_KEY
    body_text = json.dumps(body) if body is not None else ""

    try:
        raw_result = await platform.jsiter(
            platform.window.MatthewsLeaderboardFetch.request(
                method.upper(),
                url,
                SUPABASE_PUBLISHABLE_KEY,
                token,
                body_text,
                prefer,
            )
        )

        result = json.loads(str(raw_result))

        return (
            bool(result.get("ok", False)),
            int(result.get("status", 0)),
            str(result.get("text", "")),
        )
    except Exception as error:
        return False, 0, str(error)


async def load_online_leaderboard(
) -> tuple[list[dict[str, Any]], str]:
    query = urllib.parse.urlencode(
        {
            "select": "player_name,score,wave",
            "game": f"eq.{GAME_NAME}",
            "order": "score.desc,wave.desc",
            "limit": MAX_LEADERBOARD_ENTRIES,
        }
    )

    success, status, response_text = await make_request(
        "GET",
        f"{SCORES_ENDPOINT}?{query}",
    )

    if not success:
        return [], f"Could not load leaderboard ({status})."

    try:
        return (
            clean_entries(json.loads(response_text)),
            "Online leaderboard loaded.",
        )
    except json.JSONDecodeError:
        return [], "Leaderboard returned invalid data."


async def submit_online_score(
    player_name: str,
    score: int,
    wave: int,
    user_id: str,
    access_token: str,
) -> tuple[bool, str]:
    if not user_id or not access_token:
        return False, "A signed-in account is required."

    new_score = clean_score(score)
    new_wave = clean_wave(wave)

    existing_query = urllib.parse.urlencode(
        {
            "select": "player_name,score,wave",
            "game": f"eq.{GAME_NAME}",
            "user_id": f"eq.{user_id}",
            "limit": 1,
        }
    )

    success, status, response_text = await make_request(
        "GET",
        f"{SCORES_ENDPOINT}?{existing_query}",
        access_token,
    )

    if not success:
        return False, f"Could not check current score ({status})."

    try:
        existing_rows = json.loads(response_text)
    except json.JSONDecodeError:
        existing_rows = []

    payload = {
        "game": GAME_NAME,
        "user_id": user_id,
        "player_name": clean_player_name(player_name),
        "score": new_score,
        "wave": new_wave,
    }

    if existing_rows:
        existing = clean_entries(existing_rows)[0]

        existing_key = (existing["score"], existing["wave"])
        entry = payload
        new_key = (entry["score"], entry["wave"])

        if new_key <= existing_key:
            return True, "Your existing best score is higher."

        update_query = urllib.parse.urlencode(
            {
                "game": f"eq.{GAME_NAME}",
                "user_id": f"eq.{user_id}",
            }
        )

        success, status, response_text = await make_request(
            "PATCH",
            f"{SCORES_ENDPOINT}?{update_query}",
            access_token,
            payload,
            "return=minimal",
        )
    else:
        success, status, response_text = await make_request(
            "POST",
            SCORES_ENDPOINT,
            access_token,
            payload,
            "return=minimal",
        )

    if success and status in (200, 201, 204):
        return True, "Personal best saved online."

    return (
        False,
        f"Score was not saved online ({status}): "
        f"{response_text.strip()}",
    )
