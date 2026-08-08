from __future__ import annotations

import json
import sys
import urllib.parse
from typing import Any

from config import (
    ENDLESS_LEADERBOARD_MAX_DISTANCE,
    LEADERBOARD_GAME_NAME,
    MAX_LEADERBOARD_ENTRIES,
    SUPABASE_PROJECT_URL,
    SUPABASE_PUBLISHABLE_KEY,
    SUPABASE_SCORES_TABLE,
)


# ============================================================
# TUNNEL RUNNER
# ONLINE LEADERBOARD
# VERSION 0.1.0
# ============================================================
#
# Handles:
#
# - Endless Mode leaderboard
# - Global Top 10
# - Personal all-time best
# - Signed-in score submission
# - One best score per account
# - Automatic username use
# - Supabase REST API
# - Browser / Pygbag compatibility
# - Desktop-safe fallbacks
#
# Endless Mode score = metres travelled.
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
# ENDPOINT
# ============================================================

SCORES_ENDPOINT = (
    f"{SUPABASE_PROJECT_URL}"
    f"/rest/v1/{SUPABASE_SCORES_TABLE}"
)


# ============================================================
# CLEANING HELPERS
# ============================================================

def clean_user_id(
    value: Any,
) -> str:
    return (
        str(
            value
            if value is not None
            else ""
        )
        .strip()
    )


def clean_username(
    value: Any,
) -> str:
    username = (
        str(
            value
            if value is not None
            else ""
        )
        .strip()
    )

    if not username:
        return "Player"

    return username[:30]


def clean_distance(
    value: Any,
) -> int:
    if isinstance(
        value,
        bool,
    ):
        return 0

    try:
        distance = int(
            round(
                float(
                    value
                )
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
            ENDLESS_LEADERBOARD_MAX_DISTANCE,
            distance,
        ),
    )


def clean_timestamp(
    value: Any,
) -> str:
    return (
        str(
            value
            if value is not None
            else ""
        )
        .strip()
    )


# ============================================================
# LEADERBOARD ENTRY
# ============================================================

def clean_leaderboard_entry(
    value: Any,
) -> dict[str, Any] | None:
    if not isinstance(
        value,
        dict,
    ):
        return None

    return {
        "user_id": clean_user_id(
            value.get(
                "user_id",
                "",
            )
        ),

        "name": clean_username(
            value.get(
                "player_name",
                "Player",
            )
        ),

        "distance": clean_distance(
            value.get(
                "score",
                0,
            )
        ),

        "created_at": clean_timestamp(
            value.get(
                "created_at",
                "",
            )
        ),
    }


def clean_leaderboard(
    value: Any,
) -> list[
    dict[str, Any]
]:
    if not isinstance(
        value,
        list,
    ):
        return []

    entries: list[
        dict[str, Any]
    ] = []

    for raw_entry in value:
        entry = (
            clean_leaderboard_entry(
                raw_entry
            )
        )

        if entry is None:
            continue

        entries.append(
            entry
        )

    entries.sort(
        key=lambda entry: (
            int(
                entry.get(
                    "distance",
                    0,
                )
            ),

            str(
                entry.get(
                    "created_at",
                    "",
                )
            ),
        ),
        reverse=True,
    )

    return entries[
        :MAX_LEADERBOARD_ENTRIES
    ]


# ============================================================
# BROWSER FETCH BRIDGE
# ============================================================

_BROWSER_FETCH_INSTALLED = False


def install_browser_fetch_bridge(
) -> None:
    global _BROWSER_FETCH_INSTALLED

    if not IS_WEB:
        return

    if _BROWSER_FETCH_INSTALLED:
        return

    try:
        import platform

        javascript = r"""
            window.TunnelRunnerLeaderboardAPI = {

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
                        "apikey":
                            apiKey,

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
                        method:
                            method,

                        headers:
                            headers
                    };

                    if (bodyText) {
                        options.body =
                            bodyText;
                    }

                    fetch(
                        url,
                        options
                    )
                    .then(
                        async (
                            response
                        ) => {

                            const text =
                                await response.text();

                            resultText =
                                JSON.stringify({
                                    ok:
                                        response.ok,

                                    status:
                                        response.status,

                                    text:
                                        text
                                });

                            finished = true;
                        }
                    )
                    .catch(
                        (
                            error
                        ) => {

                            resultText =
                                JSON.stringify({
                                    ok:
                                        false,

                                    status:
                                        0,

                                    text:
                                        String(
                                            error
                                        )
                                });

                            finished = true;
                        }
                    );

                    while (
                        !finished
                    ) {
                        yield;
                    }

                    yield resultText;
                }
            };
        """

        platform.window.eval(
            javascript
        )

        _BROWSER_FETCH_INSTALLED = (
            True
        )

    except Exception:
        _BROWSER_FETCH_INSTALLED = (
            False
        )


# ============================================================
# BROWSER REQUEST
# ============================================================

async def browser_request(
    method: str,
    url: str,
    *,
    access_token: str = "",
    body: dict[str, Any] | None = None,
    prefer: str = "",
) -> tuple[
    bool,
    int,
    str,
]:
    if not IS_WEB:
        return (
            False,
            0,
            (
                "Online leaderboard requests "
                "are only available in the "
                "website version."
            ),
        )

    install_browser_fetch_bridge()

    if not _BROWSER_FETCH_INSTALLED:
        return (
            False,
            0,
            (
                "Could not install the "
                "browser leaderboard bridge."
            ),
        )

    body_text = ""

    if body is not None:
        try:
            body_text = json.dumps(
                body
            )

        except (
            TypeError,
            ValueError,
        ):
            body_text = ""

    try:
        import platform

        raw_result = (
            await platform.jsiter(
                platform.window
                .TunnelRunnerLeaderboardAPI
                .request(
                    method.upper(),

                    url,

                    SUPABASE_PUBLISHABLE_KEY,

                    access_token,

                    body_text,

                    prefer,
                )
            )
        )

        result = json.loads(
            str(
                raw_result
            )
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
            str(
                error
            ),
        )


# ============================================================
# LOAD GLOBAL LEADERBOARD
# ============================================================

async def load_global_leaderboard(
) -> tuple[
    list[
        dict[str, Any]
    ],
    str,
]:
    if not IS_WEB:
        return (
            [],
            (
                "The global leaderboard "
                "is available on the website."
            ),
        )

    query = urllib.parse.urlencode(
        {
            "select": (
                "user_id,"
                "player_name,"
                "score,"
                "created_at"
            ),

            "game": (
                f"eq.{LEADERBOARD_GAME_NAME}"
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

    (
        success,
        status,
        response_text,
    ) = await browser_request(
        "GET",

        (
            f"{SCORES_ENDPOINT}"
            f"?{query}"
        ),
    )

    if not success:
        return (
            [],
            (
                "Could not load "
                "the leaderboard "
                f"({status})."
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
                "The leaderboard "
                "returned invalid data."
            ),
        )

    return (
        clean_leaderboard(
            raw_data
        ),

        "Leaderboard loaded.",
    )


# ============================================================
# LOAD PERSONAL BEST
# ============================================================

async def load_personal_best(
    user_id: str,
    access_token: str,
) -> tuple[
    int,
    str,
]:
    cleaned_user_id = (
        clean_user_id(
            user_id
        )
    )

    if not cleaned_user_id:
        return (
            0,
            "Missing user ID.",
        )

    if not IS_WEB:
        return (
            0,
            (
                "Online personal best "
                "is available on the website."
            ),
        )

    if not access_token:
        return (
            0,
            (
                "A signed-in account "
                "is required."
            ),
        )

    query = urllib.parse.urlencode(
        {
            "select": (
                "score,"
                "created_at"
            ),

            "game": (
                f"eq.{LEADERBOARD_GAME_NAME}"
            ),

            "user_id": (
                f"eq.{cleaned_user_id}"
            ),

            "order": (
                "score.desc"
            ),

            "limit": 1,
        }
    )

    (
        success,
        status,
        response_text,
    ) = await browser_request(
        "GET",

        (
            f"{SCORES_ENDPOINT}"
            f"?{query}"
        ),

        access_token=(
            access_token
        ),
    )

    if not success:
        return (
            0,
            (
                "Could not load "
                "your personal best "
                f"({status})."
            ),
        )

    try:
        rows = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        return (
            0,
            (
                "Personal best "
                "returned invalid data."
            ),
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
            (
                "You have not submitted "
                "an Endless run yet."
            ),
        )

    first_row = rows[0]

    if not isinstance(
        first_row,
        dict,
    ):
        return (
            0,
            (
                "Invalid personal "
                "best data."
            ),
        )

    distance = clean_distance(
        first_row.get(
            "score",
            0,
        )
    )

    return (
        distance,

        (
            "Personal best: "
            f"{distance:,} m"
        ),
    )


# ============================================================
# LOAD CURRENT SCORE ROW
# ============================================================

async def load_current_score_row(
    user_id: str,
    access_token: str,
) -> tuple[
    dict[str, Any] | None,
    str,
]:
    cleaned_user_id = (
        clean_user_id(
            user_id
        )
    )

    if not cleaned_user_id:
        return (
            None,
            "Missing user ID.",
        )

    if not IS_WEB:
        return (
            None,
            (
                "Online score checking "
                "is only available on the website."
            ),
        )

    if not access_token:
        return (
            None,
            (
                "A signed-in account "
                "is required."
            ),
        )

    query = urllib.parse.urlencode(
        {
            "select": (
                "user_id,"
                "player_name,"
                "score,"
                "created_at"
            ),

            "game": (
                f"eq.{LEADERBOARD_GAME_NAME}"
            ),

            "user_id": (
                f"eq.{cleaned_user_id}"
            ),

            "limit": 1,
        }
    )

    (
        success,
        status,
        response_text,
    ) = await browser_request(
        "GET",

        (
            f"{SCORES_ENDPOINT}"
            f"?{query}"
        ),

        access_token=(
            access_token
        ),
    )

    if not success:
        return (
            None,
            (
                "Could not check "
                "your current score "
                f"({status})."
            ),
        )

    try:
        rows = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        return (
            None,
            (
                "Current score "
                "returned invalid data."
            ),
        )

    if (
        not isinstance(
            rows,
            list,
        )
        or not rows
    ):
        return (
            None,
            (
                "No current "
                "score row."
            ),
        )

    entry = (
        clean_leaderboard_entry(
            rows[0]
        )
    )

    return (
        entry,
        "Current score loaded.",
    )


# ============================================================
# SUBMIT ENDLESS DISTANCE
# ============================================================

async def submit_endless_distance(
    player_name: str,
    distance_metres: float,
    user_id: str,
    access_token: str,
) -> tuple[
    bool,
    str,
    int,
    bool,
]:
    """
    Returns:

        success
        message
        stored_best
        new_personal_best
    """

    cleaned_name = clean_username(
        player_name
    )

    cleaned_user_id = (
        clean_user_id(
            user_id
        )
    )

    cleaned_distance = (
        clean_distance(
            distance_metres
        )
    )

    if not cleaned_user_id:
        return (
            False,
            "Missing user ID.",
            0,
            False,
        )

    if not access_token:
        return (
            False,
            (
                "A signed-in account "
                "is required to submit scores."
            ),
            0,
            False,
        )

    if not IS_WEB:
        return (
            False,
            (
                "Scores are only uploaded "
                "from the website version."
            ),
            0,
            False,
        )

    # ========================================================
    # CHECK EXISTING BEST
    # ========================================================

    (
        existing_row,
        _message,
    ) = await load_current_score_row(
        cleaned_user_id,
        access_token,
    )

    existing_distance = 0

    if existing_row is not None:
        existing_distance = (
            clean_distance(
                existing_row.get(
                    "distance",
                    0,
                )
            )
        )

    # ========================================================
    # DO NOT REPLACE A BETTER SCORE
    # ========================================================

    if (
        existing_distance
        >= cleaned_distance
    ):
        return (
            True,

            (
                "Your best remains "
                f"{existing_distance:,} m."
            ),

            existing_distance,

            False,
        )

    # ========================================================
    # SCORE PAYLOAD
    # ========================================================

    payload = {
        "game": (
            LEADERBOARD_GAME_NAME
        ),

        "user_id": (
            cleaned_user_id
        ),

        "player_name": (
            cleaned_name
        ),

        "score": (
            cleaned_distance
        ),

        # Shared score-table compatibility fields.
        "wave": 1,

        "difficulty": (
            "Endless"
        ),

        "kills": 0,
    }

    # ========================================================
    # UPDATE EXISTING ROW
    # ========================================================

    if existing_row is not None:
        query = urllib.parse.urlencode(
            {
                "game": (
                    f"eq.{LEADERBOARD_GAME_NAME}"
                ),

                "user_id": (
                    f"eq.{cleaned_user_id}"
                ),
            }
        )

        (
            success,
            status,
            response_text,
        ) = await browser_request(
            "PATCH",

            (
                f"{SCORES_ENDPOINT}"
                f"?{query}"
            ),

            access_token=(
                access_token
            ),

            body=payload,

            prefer=(
                "return=minimal"
            ),
        )

    # ========================================================
    # CREATE NEW ROW
    # ========================================================

    else:
        (
            success,
            status,
            response_text,
        ) = await browser_request(
            "POST",

            SCORES_ENDPOINT,

            access_token=(
                access_token
            ),

            body=payload,

            prefer=(
                "return=minimal"
            ),
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    if (
        success
        and status
        in (
            200,
            201,
            204,
        )
    ):
        return (
            True,

            (
                "New online best: "
                f"{cleaned_distance:,} m"
            ),

            cleaned_distance,

            True,
        )

    # ========================================================
    # FAILURE
    # ========================================================

    error_text = (
        response_text.strip()
        or "Unknown leaderboard error."
    )

    return (
        False,

        (
            "Could not save "
            "your score "
            f"({status}): "
            f"{error_text}"
        ),

        existing_distance,

        False,
    )


# ============================================================
# RANK
# ============================================================

def get_player_rank(
    leaderboard: list[
        dict[str, Any]
    ],
    user_id: str,
) -> int | None:
    cleaned_user_id = (
        clean_user_id(
            user_id
        )
    )

    if not cleaned_user_id:
        return None

    for (
        rank,
        entry,
    ) in enumerate(
        leaderboard,
        start=1,
    ):
        if (
            clean_user_id(
                entry.get(
                    "user_id",
                    "",
                )
            )
            == cleaned_user_id
        ):
            return rank

    return None


# ============================================================
# DISPLAY HELPERS
# ============================================================

def format_leaderboard_distance(
    value: Any,
) -> str:
    distance = clean_distance(
        value
    )

    return (
        f"{distance:,} m"
    )


def leaderboard_entry_name(
    entry: dict[str, Any],
) -> str:
    return clean_username(
        entry.get(
            "name",
            "Player",
        )
    )


def leaderboard_entry_distance(
    entry: dict[str, Any],
) -> int:
    return clean_distance(
        entry.get(
            "distance",
            0,
        )
    )


# ============================================================
# DUPLICATE USER SCORE CLEANER
# ============================================================

def keep_best_score_per_user(
    entries: list[
        dict[str, Any]
    ],
) -> list[
    dict[str, Any]
]:
    """
    Defensive helper.

    If the database ever contains multiple Tunnel Runner rows
    for the same account, only keep that account's best result.
    """

    best_by_user: dict[
        str,
        dict[str, Any],
    ] = {}

    anonymous_entries: list[
        dict[str, Any]
    ] = []

    for entry in entries:
        user_id = clean_user_id(
            entry.get(
                "user_id",
                "",
            )
        )

        if not user_id:
            anonymous_entries.append(
                entry
            )

            continue

        current = (
            best_by_user.get(
                user_id
            )
        )

        if current is None:
            best_by_user[
                user_id
            ] = entry

            continue

        current_distance = (
            leaderboard_entry_distance(
                current
            )
        )

        new_distance = (
            leaderboard_entry_distance(
                entry
            )
        )

        if (
            new_distance
            > current_distance
        ):
            best_by_user[
                user_id
            ] = entry

    result = (
        list(
            best_by_user.values()
        )
        + anonymous_entries
    )

    result.sort(
        key=lambda entry: (
            leaderboard_entry_distance(
                entry
            )
        ),
        reverse=True,
    )

    return result[
        :MAX_LEADERBOARD_ENTRIES
    ]


# ============================================================
# VALIDATION
# ============================================================

def validate_leaderboard_config(
) -> None:
    if not SUPABASE_PROJECT_URL:
        raise ValueError(
            "SUPABASE_PROJECT_URL is empty."
        )

    if not SUPABASE_PUBLISHABLE_KEY:
        raise ValueError(
            "SUPABASE_PUBLISHABLE_KEY is empty."
        )

    if not SUPABASE_SCORES_TABLE:
        raise ValueError(
            "SUPABASE_SCORES_TABLE is empty."
        )

    if not LEADERBOARD_GAME_NAME:
        raise ValueError(
            "LEADERBOARD_GAME_NAME is empty."
        )

    if MAX_LEADERBOARD_ENTRIES <= 0:
        raise ValueError(
            (
                "MAX_LEADERBOARD_ENTRIES "
                "must be greater than zero."
            )
        )

    if ENDLESS_LEADERBOARD_MAX_DISTANCE <= 0:
        raise ValueError(
            (
                "ENDLESS_LEADERBOARD_MAX_DISTANCE "
                "must be greater than zero."
            )
        )


validate_leaderboard_config()