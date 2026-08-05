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

GAME_NAME = "space-shooter"
MAX_LEADERBOARD_ENTRIES = 10

IS_WEB = sys.platform in (
    "emscripten",
    "wasi",
)


# ============================================================
# SHARED HELPERS
# ============================================================

def clean_player_name(name: str) -> str:
    cleaned = str(name).strip()[:16]

    if not cleaned:
        return "Player"

    return cleaned


def clean_score(score: int) -> int:
    try:
        return max(
            0,
            min(
                100_000_000,
                int(score),
            ),
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0


def clean_wave(wave: int) -> int:
    try:
        return max(
            1,
            min(
                100_000,
                int(wave),
            ),
        )

    except (
        TypeError,
        ValueError,
    ):
        return 1


def clean_leaderboard_data(
    data: Any,
) -> list[dict[str, int | str]]:
    if not isinstance(data, list):
        return []

    cleaned_entries: list[
        dict[str, int | str]
    ] = []

    for entry in data:
        if not isinstance(entry, dict):
            continue

        player_name = clean_player_name(
            entry.get(
                "player_name",
                entry.get(
                    "name",
                    "Player",
                ),
            )
        )

        score = clean_score(
            entry.get(
                "score",
                0,
            )
        )

        wave = clean_wave(
            entry.get(
                "wave",
                1,
            )
        )

        cleaned_entries.append(
            {
                "name": player_name,
                "score": score,
                "wave": wave,
            }
        )

    cleaned_entries.sort(
        key=lambda entry: (
            int(entry["score"]),
            int(entry["wave"]),
        ),
        reverse=True,
    )

    return cleaned_entries[
        :MAX_LEADERBOARD_ENTRIES
    ]


def request_headers(
    *,
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
# DESKTOP HTTP REQUESTS
# ============================================================

def desktop_request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
) -> tuple[bool, int, str]:
    encoded_body = None

    if body is not None:
        encoded_body = json.dumps(
            body
        ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=encoded_body,
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
            response_text = (
                response.read()
                .decode("utf-8")
            )

            return (
                True,
                int(response.status),
                response_text,
            )

    except urllib.error.HTTPError as error:
        try:
            error_text = (
                error.read()
                .decode("utf-8")
            )

        except Exception:
            error_text = str(error)

        return (
            False,
            int(error.code),
            error_text,
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
# PYGBAG BROWSER REQUESTS
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
        window.MatthewsLeaderboardAPI = {
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
        await asyncio.sleep(0)

        raw_result = await platform.jsiter(
            platform.window
            .MatthewsLeaderboardAPI
            .request(
                method.upper(),
                url,
                SUPABASE_PUBLISHABLE_KEY,
                body_text,
            )
        )

        decoded_result = json.loads(
            str(raw_result)
        )

        return (
            bool(
                decoded_result.get(
                    "ok",
                    False,
                )
            ),
            int(
                decoded_result.get(
                    "status",
                    0,
                )
            ),
            str(
                decoded_result.get(
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
# CROSS-PLATFORM REQUEST
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
# PUBLIC LEADERBOARD FUNCTIONS
# ============================================================

async def load_online_leaderboard(
) -> tuple[
    list[dict[str, int | str]],
    str,
]:
    query_parameters = urllib.parse.urlencode(
        {
            "select": (
                "player_name,score,wave"
            ),
            "game": (
                f"eq.{GAME_NAME}"
            ),
            "order": (
                "score.desc,wave.desc"
            ),
            "limit": (
                MAX_LEADERBOARD_ENTRIES
            ),
        }
    )

    url = (
        f"{SCORES_ENDPOINT}"
        f"?{query_parameters}"
    )

    success, status, response_text = (
        await make_request(
            "GET",
            url,
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

    leaderboard = clean_leaderboard_data(
        data
    )

    return (
        leaderboard,
        "Online leaderboard loaded.",
    )


async def submit_online_score(
    player_name: str,
    score: int,
    wave: int,
) -> tuple[bool, str]:
    score_entry = {
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
    }

    success, status, response_text = (
        await make_request(
            "POST",
            SCORES_ENDPOINT,
            score_entry,
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

    error_message = (
        response_text.strip()
        or "Unknown connection error."
    )

    return (
        False,
        (
            "Score was not saved online "
            f"({status}): {error_message}"
        ),
    )