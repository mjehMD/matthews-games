from __future__ import annotations

import json
import platform
import sys
import urllib.parse
from typing import Any

from config import (
    GAME_SLUG,
    LEADERBOARD_DISTANCE_LIMIT,
    MAX_LEADERBOARD_ENTRIES,
    SUPABASE_PROJECT_URL,
    SUPABASE_PUBLISHABLE_KEY,
    SUPABASE_SCORES_TABLE,
)


# ============================================================
# ONLINE LEADERBOARD SETTINGS
# ============================================================

GAME_NAME = GAME_SLUG

SCORES_ENDPOINT = (
    f"{SUPABASE_PROJECT_URL}"
    f"/rest/v1/{SUPABASE_SCORES_TABLE}"
)

IS_WEB = sys.platform in (
    "emscripten",
    "wasi",
)


# ============================================================
# DATA CLEANING
# ============================================================

def clean_player_name(
    value: Any,
) -> str:
    """
    Clean a public leaderboard username.
    """

    cleaned_name = str(
        value
    ).strip()

    if not cleaned_name:
        cleaned_name = "Player"

    return cleaned_name[:16]


def clean_distance(
    value: Any,
) -> int:
    """
    Convert a distance to a safe whole number of metres.
    """

    if isinstance(
        value,
        bool,
    ):
        return 0

    try:
        distance = int(
            round(
                float(value)
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0

    return max(
        0,
        min(
            LEADERBOARD_DISTANCE_LIMIT,
            distance,
        ),
    )


def clean_leaderboard_entries(
    data: Any,
) -> list[dict[str, Any]]:
    """
    Validate and sort leaderboard rows returned by Supabase.
    """

    if not isinstance(
        data,
        list,
    ):
        return []

    cleaned_entries: list[
        dict[str, Any]
    ] = []

    for item in data:
        if not isinstance(
            item,
            dict,
        ):
            continue

        cleaned_entries.append(
            {
                "user_id": str(
                    item.get(
                        "user_id",
                        "",
                    )
                ),

                "name": clean_player_name(
                    item.get(
                        "player_name",
                        "Player",
                    )
                ),

                "distance": clean_distance(
                    item.get(
                        "score",
                        0,
                    )
                ),

                "created_at": str(
                    item.get(
                        "created_at",
                        "",
                    )
                ),
            }
        )

    cleaned_entries.sort(
        key=lambda entry: (
            int(
                entry["distance"]
            ),
            str(
                entry["created_at"]
            ),
        ),
        reverse=True,
    )

    return cleaned_entries[
        :MAX_LEADERBOARD_ENTRIES
    ]


# ============================================================
# BROWSER FETCH BRIDGE
# ============================================================

_BROWSER_FETCH_READY = False


def install_browser_fetch() -> None:
    """
    Install the JavaScript fetch helper used by Pygbag.
    """

    global _BROWSER_FETCH_READY

    if (
        not IS_WEB
        or _BROWSER_FETCH_READY
    ):
        return

    javascript = """
        window.OrbitRushLeaderboardAPI = {
            request: function* (
                method,
                url,
                apiKey,
                accessToken,
                bodyText,
                preferValue
            ) {
                let finished = false;
                let resultText = "";

                const token =
                    accessToken || apiKey;

                const headers = {
                    "apikey": apiKey,
                    "Authorization":
                        "Bearer " + token,
                    "Accept":
                        "application/json",
                    "Content-Type":
                        "application/json"
                };

                if (preferValue) {
                    headers["Prefer"] =
                        preferValue;
                }

                const options = {
                    method: method,
                    headers: headers
                };

                if (bodyText) {
                    options.body =
                        bodyText;
                }

                fetch(
                    url,
                    options
                )
                    .then(async (response) => {
                        const responseText =
                            await response.text();

                        resultText =
                            JSON.stringify({
                                ok:
                                    response.ok,

                                status:
                                    response.status,

                                text:
                                    responseText
                            });

                        finished = true;
                    })
                    .catch((error) => {
                        resultText =
                            JSON.stringify({
                                ok: false,
                                status: 0,
                                text:
                                    String(error)
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

    _BROWSER_FETCH_READY = True


async def make_request(
    method: str,
    url: str,
    access_token: str = "",
    body: dict[str, Any] | None = None,
    prefer: str = "",
) -> tuple[bool, int, str]:
    """
    Make one browser request to Supabase.
    """

    if not IS_WEB:
        return (
            False,
            0,
            (
                "Orbit Rush online leaderboards "
                "require the website version."
            ),
        )

    install_browser_fetch()

    body_text = ""

    if body is not None:
        body_text = json.dumps(
            body
        )

    try:
        raw_result = await platform.jsiter(
            platform.window
            .OrbitRushLeaderboardAPI
            .request(
                method.upper(),
                url,
                SUPABASE_PUBLISHABLE_KEY,
                access_token,
                body_text,
                prefer,
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
# LEADERBOARD LOADING
# ============================================================

async def load_online_leaderboard(
) -> tuple[
    list[dict[str, Any]],
    str,
]:
    """
    Load the all-time Orbit Rush Endless leaderboard.
    """

    query = urllib.parse.urlencode(
        {
            "select": (
                "user_id,"
                "player_name,"
                "score,"
                "created_at"
            ),

            "game": (
                f"eq.{GAME_NAME}"
            ),

            "order": (
                "score.desc,"
                "created_at.asc"
            ),

            "limit": (
                MAX_LEADERBOARD_ENTRIES
            ),
        }
    )

    success, status, response_text = (
        await make_request(
            method="GET",
            url=(
                f"{SCORES_ENDPOINT}"
                f"?{query}"
            ),
        )
    )

    if not success:
        return (
            [],
            (
                "Could not load the online "
                f"leaderboard ({status})."
            ),
        )

    try:
        raw_data = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        return (
            [],
            (
                "The online leaderboard "
                "returned invalid data."
            ),
        )

    return (
        clean_leaderboard_entries(
            raw_data
        ),
        "Online leaderboard loaded.",
    )


# ============================================================
# PLAYER BEST DISTANCE
# ============================================================

async def load_player_best_distance(
    user_id: str,
    access_token: str,
) -> tuple[int, str]:
    """
    Load one signed-in player's best Endless distance.
    """

    cleaned_user_id = str(
        user_id
    ).strip()

    if (
        not cleaned_user_id
        or not access_token
    ):
        return (
            0,
            "A signed-in account is required.",
        )

    query = urllib.parse.urlencode(
        {
            "select": "score",

            "game": (
                f"eq.{GAME_NAME}"
            ),

            "user_id": (
                f"eq.{cleaned_user_id}"
            ),

            "limit": 1,
        }
    )

    success, status, response_text = (
        await make_request(
            method="GET",
            url=(
                f"{SCORES_ENDPOINT}"
                f"?{query}"
            ),
            access_token=access_token,
        )
    )

    if not success:
        return (
            0,
            (
                "Could not load your best "
                f"distance ({status})."
            ),
        )

    try:
        rows = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        return (
            0,
            "Your best distance returned invalid data.",
        )

    if (
        not isinstance(
            rows,
            list,
        )
        or not rows
    ):
        return (
            0,
            "No Endless distance has been saved yet.",
        )

    return (
        clean_distance(
            rows[0].get(
                "score",
                0,
            )
        ),
        "Personal best loaded.",
    )


# ============================================================
# SCORE SUBMISSION
# ============================================================

async def submit_endless_distance(
    player_name: str,
    distance_metres: float,
    user_id: str,
    access_token: str,
) -> tuple[bool, str, int]:
    """
    Save a player's best Endless Mode distance.

    Returns:
        success
        status message
        saved personal-best distance
    """

    cleaned_name = clean_player_name(
        player_name
    )

    cleaned_distance = clean_distance(
        distance_metres
    )

    cleaned_user_id = str(
        user_id
    ).strip()

    if (
        not cleaned_user_id
        or not access_token
    ):
        return (
            False,
            "A signed-in account is required.",
            0,
        )

    existing_query = urllib.parse.urlencode(
        {
            "select": (
                "score,"
                "created_at"
            ),

            "game": (
                f"eq.{GAME_NAME}"
            ),

            "user_id": (
                f"eq.{cleaned_user_id}"
            ),

            "limit": 1,
        }
    )

    success, status, response_text = (
        await make_request(
            method="GET",
            url=(
                f"{SCORES_ENDPOINT}"
                f"?{existing_query}"
            ),
            access_token=access_token,
        )
    )

    if not success:
        return (
            False,
            (
                "Could not check your current "
                f"best distance ({status})."
            ),
            0,
        )

    try:
        existing_rows = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        existing_rows = []

    existing_distance = 0

    if (
        isinstance(
            existing_rows,
            list,
        )
        and existing_rows
    ):
        existing_distance = clean_distance(
            existing_rows[0].get(
                "score",
                0,
            )
        )

    if (
        existing_distance
        >= cleaned_distance
    ):
        return (
            True,
            (
                "Your existing personal best "
                "is higher."
            ),
            existing_distance,
        )

    payload = {
        "game": GAME_NAME,

        "user_id": cleaned_user_id,

        "player_name": cleaned_name,

        # Orbit Rush stores metres in the existing score column.
        "score": cleaned_distance,

        # These values satisfy the shared scores-table schema.
        "wave": 1,
        "difficulty": "Easy",
        "kills": 0,
    }

    if existing_rows:
        update_query = urllib.parse.urlencode(
            {
                "game": (
                    f"eq.{GAME_NAME}"
                ),

                "user_id": (
                    f"eq.{cleaned_user_id}"
                ),
            }
        )

        success, status, response_text = (
            await make_request(
                method="PATCH",
                url=(
                    f"{SCORES_ENDPOINT}"
                    f"?{update_query}"
                ),
                access_token=access_token,
                body=payload,
                prefer="return=minimal",
            )
        )

    else:
        success, status, response_text = (
            await make_request(
                method="POST",
                url=SCORES_ENDPOINT,
                access_token=access_token,
                body=payload,
                prefer="return=minimal",
            )
        )

    if (
        success
        and status in (
            200,
            201,
            204,
        )
    ):
        return (
            True,
            (
                f"New personal best: "
                f"{cleaned_distance:,} m"
            ),
            cleaned_distance,
        )

    error_message = (
        response_text.strip()
        or "Unknown connection error."
    )

    return (
        False,
        (
            "Distance was not saved "
            f"({status}): {error_message}"
        ),
        existing_distance,
    )


# ============================================================
# DISPLAY HELPERS
# ============================================================

def leaderboard_rank_text(
    rank: int,
) -> str:
    """
    Format a leaderboard rank.
    """

    cleaned_rank = max(
        1,
        int(rank),
    )

    return f"{cleaned_rank}."


def leaderboard_distance_text(
    distance_metres: Any,
) -> str:
    """
    Format a leaderboard distance.
    """

    distance = clean_distance(
        distance_metres
    )

    return f"{distance:,} m"