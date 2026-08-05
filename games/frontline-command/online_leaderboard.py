from __future__ import annotations

import asyncio
import json
import platform
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


# ============================================================
# SUPABASE SETTINGS
# ============================================================

SUPABASE_PROJECT_URL = (
    "https://bcarxudxfmsibvnteoaj.supabase.co"
)

SUPABASE_PUBLISHABLE_KEY = (
    "sb_publishable_S7ki2S3tODs4shwWovSY6w_-2jknXXg"
)

SCORES_ENDPOINT = (
    f"{SUPABASE_PROJECT_URL}/rest/v1/scores"
)

GAME_NAME = "frontline-command"
MAX_LEADERBOARD_ENTRIES = 10

VALID_DIFFICULTIES = {
    "Easy",
    "Medium",
    "Hard",
}

IS_WEB = sys.platform in (
    "emscripten",
    "wasi",
)


# ============================================================
# VALIDATION
# ============================================================

def clean_player_name(value: Any) -> str:
    cleaned = str(value).strip()[:16]
    return cleaned or "Player"


def clean_score(value: Any) -> int:
    try:
        return max(
            0,
            min(
                100_000_000,
                int(value),
            ),
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def clean_wave(value: Any) -> int:
    try:
        return max(
            1,
            min(
                100_000,
                int(value),
            ),
        )
    except (
        TypeError,
        ValueError,
    ):
        return 1


def clean_kills(value: Any) -> int:
    try:
        return max(
            0,
            min(
                100_000_000,
                int(value),
            ),
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def clean_difficulty(value: Any) -> str:
    cleaned = str(value).strip().title()

    if cleaned not in VALID_DIFFICULTIES:
        return "Easy"

    return cleaned


def clean_online_entries(
    data: Any,
) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        return []

    entries: list[dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        entries.append(
            {
                "name": clean_player_name(
                    item.get(
                        "player_name",
                        item.get(
                            "name",
                            "Player",
                        ),
                    )
                ),
                "score": clean_score(
                    item.get(
                        "score",
                        0,
                    )
                ),
                "wave": clean_wave(
                    item.get(
                        "wave",
                        1,
                    )
                ),
                "difficulty": clean_difficulty(
                    item.get(
                        "difficulty",
                        "Easy",
                    )
                ),
                "kills": clean_kills(
                    item.get(
                        "kills",
                        0,
                    )
                ),
            }
        )

    entries.sort(
        key=lambda entry: (
            entry["score"],
            entry["wave"],
            entry["kills"],
        ),
        reverse=True,
    )

    return entries[
        :MAX_LEADERBOARD_ENTRIES
    ]


def request_headers(
    include_prefer: bool = False,
) -> dict[str, str]:
    headers = {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": (
            "Bearer "
            + SUPABASE_PUBLISHABLE_KEY
        ),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if include_prefer:
        headers["Prefer"] = "return=minimal"

    return headers


# ============================================================
# DESKTOP REQUESTS
# ============================================================

def desktop_request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
) -> tuple[bool, int, str]:
    request_body = None

    if body is not None:
        request_body = json.dumps(
            body
        ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=request_body,
        headers=request_headers(
            include_prefer=(
                method.upper() == "POST"
            )
        ),
        method=method.upper(),
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=8,
        ) as response:
            return (
                True,
                int(response.status),
                response.read().decode(
                    "utf-8"
                ),
            )

    except urllib.error.HTTPError as error:
        try:
            message = error.read().decode(
                "utf-8"
            )
        except Exception:
            message = str(error)

        return (
            False,
            int(error.code),
            message,
        )

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as error:
        return (
            False,
            0,
            str(error),
        )


# ============================================================
# BROWSER REQUESTS
# ============================================================

_BROWSER_FETCH_INSTALLED = False


def install_browser_fetch() -> None:
    global _BROWSER_FETCH_INSTALLED

    if (
        not IS_WEB
        or _BROWSER_FETCH_INSTALLED
    ):
        return

    javascript = """
        window.FrontlineLeaderboardAPI = {
            request: function* (
                method,
                url,
                apiKey,
                bodyText
            ) {
                let finished = false;
                let resultText = "";

                const options = {
                    method: method,
                    headers: {
                        "apikey": apiKey,
                        "Authorization":
                            "Bearer " + apiKey,
                        "Accept":
                            "application/json",
                        "Content-Type":
                            "application/json"
                    }
                };

                if (method === "POST") {
                    options.headers["Prefer"] =
                        "return=minimal";

                    options.body = bodyText;
                }

                fetch(url, options)
                    .then(async (response) => {
                        const text =
                            await response.text();

                        resultText = JSON.stringify({
                            ok: response.ok,
                            status: response.status,
                            text: text
                        });

                        finished = true;
                    })
                    .catch((error) => {
                        resultText = JSON.stringify({
                            ok: false,
                            status: 0,
                            text: String(error)
                        });

                        finished = true;
                    });

                while (!finished) {
                    yield;
                }

                yield resultText;
            }
        };
    """

    platform.window.eval(
        javascript
    )

    _BROWSER_FETCH_INSTALLED = True


async def browser_request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
) -> tuple[bool, int, str]:
    install_browser_fetch()

    body_text = ""

    if body is not None:
        body_text = json.dumps(
            body
        )

    try:
        raw_result = await platform.jsiter(
            platform.window
            .FrontlineLeaderboardAPI
            .request(
                method.upper(),
                url,
                SUPABASE_PUBLISHABLE_KEY,
                body_text,
            )
        )

        result = json.loads(
            str(raw_result)
        )

        return (
            bool(
                result.get(
                    "ok",
                    False,
                )
            ),
            int(
                result.get(
                    "status",
                    0,
                )
            ),
            str(
                result.get(
                    "text",
                    "",
                )
            ),
        )

    except Exception as error:
        return (
            False,
            0,
            str(error),
        )


# ============================================================
# SHARED REQUEST FUNCTION
# ============================================================

async def make_request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
) -> tuple[bool, int, str]:
    if IS_WEB:
        return await browser_request(
            method,
            url,
            body,
        )

    return await asyncio.to_thread(
        desktop_request,
        method,
        url,
        body,
    )


# ============================================================
# PUBLIC FUNCTIONS
# ============================================================

async def load_online_leaderboard(
) -> tuple[list[dict[str, Any]], str]:
    query = urllib.parse.urlencode(
        {
            "select": (
                "player_name,score,wave,"
                "difficulty,kills"
            ),
            "game": (
                f"eq.{GAME_NAME}"
            ),
            "order": (
                "score.desc,"
                "wave.desc,"
                "kills.desc"
            ),
            "limit": (
                MAX_LEADERBOARD_ENTRIES
            ),
        }
    )

    success, status, response_text = (
        await make_request(
            "GET",
            f"{SCORES_ENDPOINT}?{query}",
        )
    )

    if not success:
        return (
            [],
            (
                "Could not load online "
                f"leaderboard ({status})."
            ),
        )

    try:
        data = json.loads(
            response_text
        )
    except json.JSONDecodeError:
        return (
            [],
            "Leaderboard returned invalid data.",
        )

    return (
        clean_online_entries(data),
        "Online leaderboard loaded.",
    )


async def submit_online_score(
    player_name: str,
    score: int,
    wave: int,
    difficulty: str,
    kills: int,
) -> tuple[bool, str]:
    entry = {
        "game": GAME_NAME,
        "player_name": clean_player_name(
            player_name
        ),
        "score": clean_score(
            score
        ),
        "wave": clean_wave(
            wave
        ),
        "difficulty": clean_difficulty(
            difficulty
        ),
        "kills": clean_kills(
            kills
        ),
    }

    success, status, response_text = (
        await make_request(
            "POST",
            SCORES_ENDPOINT,
            entry,
        )
    )

    if success and status in (
        200,
        201,
        204,
    ):
        return (
            True,
            "Score saved online.",
        )

    return (
        False,
        (
            "Score was not saved online "
            f"({status}): "
            f"{response_text.strip()}"
        ),
    )