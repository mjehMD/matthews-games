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
# VERSION 0.2.0
# ============================================================
#
# FEATURES:
#
# - Tunnel Runner leaderboard
# - Reads old Orbit Runner scores
# - Reads new Tunnel Runner scores
# - Combines both leaderboards
# - Keeps best score per account
# - Personal all-time best
# - Signed-in score saving
# - Never replaces a better score
# - New scores save as tunnel-runner
# - Browser / Pygbag compatible
# - Async network requests
# - No blocking requests during gameplay
# - Desktop-safe fallback
#
# Endless score = metres travelled.
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
# GAME IDS
# ============================================================

CURRENT_GAME_NAME = (
    LEADERBOARD_GAME_NAME
)

LEGACY_GAME_NAMES = (
    "orbit-runner",
)


def leaderboard_game_names(
) -> tuple[str, ...]:

    names: list[str] = []

    for name in (
        CURRENT_GAME_NAME,
        *LEGACY_GAME_NAMES,
    ):

        cleaned = str(
            name
        ).strip()

        if (
            cleaned
            and cleaned
            not in names
        ):

            names.append(
                cleaned
            )

    return tuple(
        names
    )


ALL_GAME_NAMES = (
    leaderboard_game_names()
)


# ============================================================
# ENDPOINT
# ============================================================

SCORES_ENDPOINT = (
    f"{SUPABASE_PROJECT_URL}"
    f"/rest/v1/{SUPABASE_SCORES_TABLE}"
)


# ============================================================
# BROWSER FETCH BRIDGE
# ============================================================

_BROWSER_FETCH_INSTALLED = False


def install_browser_fetch_bridge(
) -> None:

    global _BROWSER_FETCH_INSTALLED

    if _BROWSER_FETCH_INSTALLED:
        return

    if not IS_WEB:
        return

    try:

        import platform

        javascript = r"""
            (() => {
                if (
                    window.TunnelRunnerLeaderboardAPI
                    && window.TunnelRunnerLeaderboardAPI.request
                ) {
                    return;
                }

                window.TunnelRunnerLeaderboardAPI = {
                    request: async function(
                        method,
                        url,
                        apiKey,
                        accessToken,
                        bodyText,
                        prefer
                    ) {
                        let finished = false;
                        let resultText = "";

                        const run = async () => {
                            try {
                                const headers = {
                                    "apikey": apiKey,
                                    "Accept": "application/json"
                                };

                                if (
                                    accessToken
                                    && accessToken.length > 0
                                ) {
                                    headers["Authorization"] =
                                        "Bearer " + accessToken;
                                } else {
                                    headers["Authorization"] =
                                        "Bearer " + apiKey;
                                }

                                if (
                                    bodyText
                                    && bodyText.length > 0
                                ) {
                                    headers["Content-Type"] =
                                        "application/json";
                                }

                                if (
                                    prefer
                                    && prefer.length > 0
                                ) {
                                    headers["Prefer"] = prefer;
                                }

                                const options = {
                                    method: method,
                                    headers: headers
                                };

                                if (
                                    bodyText
                                    && bodyText.length > 0
                                    && method !== "GET"
                                    && method !== "HEAD"
                                ) {
                                    options.body = bodyText;
                                }

                                const response = await fetch(
                                    url,
                                    options
                                );

                                const text = await response.text();

                                resultText = JSON.stringify({
                                    ok: response.ok,
                                    status: response.status,
                                    text: text
                                });
                            } catch (error) {
                                resultText = JSON.stringify({
                                    ok: false,
                                    status: 0,
                                    text: String(error)
                                });
                            }

                            finished = true;
                        };

                        run();

                        while (!finished) {
                            yield;
                        }

                        yield resultText;
                    }
                };
            })();
        """

        platform.window.eval(
            javascript
        )

        _BROWSER_FETCH_INSTALLED = True

    except Exception:

        _BROWSER_FETCH_INSTALLED = False


# ============================================================
# NETWORK REQUEST
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

        raw_result = await platform.jsiter(
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
# CLEANING
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

    return username[
        :30
    ]


def clean_game_name(
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
# ENTRY CLEANING
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
        "game": clean_game_name(
            value.get(
                "game",
                "",
            )
        ),

        "user_id": clean_user_id(
            value.get(
                "user_id",
                "",
            )
        ),

        "name": clean_username(
            value.get(
                "player_name",
                value.get(
                    "name",
                    "Player",
                ),
            )
        ),

        "distance": clean_distance(
            value.get(
                "score",
                value.get(
                    "distance",
                    0,
                ),
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
            leaderboard_entry_distance(
                entry
            )
        ),
        reverse=True,
    )

    return entries


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
            entry.get(
                "player_name",
                "Player",
            ),
        )
    )


def leaderboard_entry_distance(
    entry: dict[str, Any],
) -> int:

    return clean_distance(
        entry.get(
            "distance",
            entry.get(
                "score",
                0,
            ),
        )
    )


# ============================================================
# BEST SCORE PER PLAYER
# ============================================================

def keep_best_score_per_user(
    entries: list[
        dict[str, Any]
    ],
) -> list[
    dict[str, Any]
]:

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

        elif (
            new_distance
            == current_distance
        ):

            # Prefer the new Tunnel Runner row if both
            # game names contain the same score.

            current_game = clean_game_name(
                current.get(
                    "game",
                    "",
                )
            )

            new_game = clean_game_name(
                entry.get(
                    "game",
                    "",
                )
            )

            if (
                current_game
                != CURRENT_GAME_NAME

                and new_game
                == CURRENT_GAME_NAME
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
# PLAYER RANK
# ============================================================

def get_player_rank(
    entries: list[
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

    cleaned_entries = (
        keep_best_score_per_user(
            entries
        )
    )

    for index, entry in enumerate(
        cleaned_entries
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

            return (
                index + 1
            )

    return None


# ============================================================
# POSTGREST GAME FILTER
# ============================================================

def game_filter_value(
) -> str:

    if (
        len(
            ALL_GAME_NAMES
        )
        == 1
    ):

        return (
            f"eq.{ALL_GAME_NAMES[0]}"
        )

    joined = ",".join(
        ALL_GAME_NAMES
    )

    return (
        f"in.({joined})"
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

    # Ask Supabase for both:
    #
    # tunnel-runner
    # orbit-runner
    #
    # in one request.

    request_limit = max(
        MAX_LEADERBOARD_ENTRIES
        * max(
            2,
            len(
                ALL_GAME_NAMES
            ),
        )
        * 3,

        30,
    )

    query = urllib.parse.urlencode(
        {
            "select": (
                "game,"
                "user_id,"
                "player_name,"
                "score,"
                "created_at"
            ),

            "game": (
                game_filter_value()
            ),

            "order": (
                "score.desc,"
                "created_at.asc"
            ),

            "limit": (
                request_limit
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

    entries = (
        clean_leaderboard(
            raw_data
        )
    )

    entries = (
        keep_best_score_per_user(
            entries
        )
    )

    if not entries:

        return (
            [],
            "No leaderboard scores yet.",
        )

    return (
        entries,
        "Leaderboard loaded.",
    )


# ============================================================
# LOAD ALL USER ROWS
# ============================================================

async def load_user_score_rows(
    user_id: str,
    access_token: str,
) -> tuple[
    list[
        dict[str, Any]
    ],
    str,
]:

    cleaned_user_id = (
        clean_user_id(
            user_id
        )
    )

    if not cleaned_user_id:

        return (
            [],
            "Missing user ID.",
        )

    if not IS_WEB:

        return (
            [],
            (
                "Online scores are only "
                "available on the website."
            ),
        )

    if not access_token:

        return (
            [],
            (
                "A signed-in account "
                "is required."
            ),
        )

    query = urllib.parse.urlencode(
        {
            "select": (
                "game,"
                "user_id,"
                "player_name,"
                "score,"
                "created_at"
            ),

            "game": (
                game_filter_value()
            ),

            "user_id": (
                f"eq.{cleaned_user_id}"
            ),

            "order": (
                "score.desc,"
                "created_at.asc"
            ),

            "limit": 20,
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
            [],
            (
                "Could not load "
                "your saved scores "
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
                "Saved scores returned "
                "invalid data."
            ),
        )

    return (
        clean_leaderboard(
            raw_data
        ),
        "Saved scores loaded.",
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

    rows, message = (
        await load_user_score_rows(
            user_id,
            access_token,
        )
    )

    if not rows:

        return (
            0,
            message,
        )

    best_distance = max(
        (
            leaderboard_entry_distance(
                entry
            )

            for entry
            in rows
        ),
        default=0,
    )

    return (
        best_distance,
        (
            "Personal best loaded: "
            f"{best_distance:,} m."
        ),
    )


# ============================================================
# CURRENT GAME ROW
# ============================================================

def current_game_row(
    entries: list[
        dict[str, Any]
    ],
) -> dict[str, Any] | None:

    current_rows = [
        entry

        for entry
        in entries

        if (
            clean_game_name(
                entry.get(
                    "game",
                    "",
                )
            )
            == CURRENT_GAME_NAME
        )
    ]

    if not current_rows:

        return None

    current_rows.sort(
        key=lambda entry: (
            leaderboard_entry_distance(
                entry
            )
        ),
        reverse=True,
    )

    return current_rows[0]


# ============================================================
# BEST ROW
# ============================================================

def best_score_row(
    entries: list[
        dict[str, Any]
    ],
) -> dict[str, Any] | None:

    if not entries:

        return None

    return max(
        entries,
        key=lambda entry: (
            leaderboard_entry_distance(
                entry
            )
        ),
    )


# ============================================================
# LOAD CURRENT SCORE ROW
# ============================================================
#
# Kept for compatibility with older main.py versions.
#

async def load_current_score_row(
    user_id: str,
    access_token: str,
) -> tuple[
    dict[str, Any] | None,
    str,
]:

    rows, message = (
        await load_user_score_rows(
            user_id,
            access_token,
        )
    )

    if not rows:

        return (
            None,
            message,
        )

    row = (
        best_score_row(
            rows
        )
    )

    if row is None:

        return (
            None,
            "No current score row.",
        )

    return (
        row,
        "Current score loaded.",
    )


# ============================================================
# UPDATE CURRENT TUNNEL RUNNER ROW
# ============================================================

async def update_current_game_score(
    *,
    user_id: str,
    access_token: str,
    payload: dict[str, Any],
) -> tuple[
    bool,
    int,
    str,
]:

    query = urllib.parse.urlencode(
        {
            "game": (
                f"eq.{CURRENT_GAME_NAME}"
            ),

            "user_id": (
                f"eq.{user_id}"
            ),
        }
    )

    return await browser_request(
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


# ============================================================
# INSERT NEW TUNNEL RUNNER ROW
# ============================================================

async def insert_current_game_score(
    *,
    access_token: str,
    payload: dict[str, Any],
) -> tuple[
    bool,
    int,
    str,
]:

    return await browser_request(
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


# ============================================================
# SUBMIT ENDLESS SCORE
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

    cleaned_name = (
        clean_username(
            player_name
        )
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
    # LOAD ALL EXISTING SCORES
    # ========================================================

    existing_rows, _message = (
        await load_user_score_rows(
            cleaned_user_id,
            access_token,
        )
    )

    best_existing_row = (
        best_score_row(
            existing_rows
        )
    )

    existing_best = 0

    if best_existing_row is not None:

        existing_best = (
            leaderboard_entry_distance(
                best_existing_row
            )
        )

    # ========================================================
    # DON'T REPLACE A BETTER OLD OR NEW SCORE
    # ========================================================

    if (
        existing_best
        >= cleaned_distance
    ):

        return (
            True,

            (
                "Your best remains "
                f"{existing_best:,} m."
            ),

            existing_best,

            False,
        )

    # ========================================================
    # NEW TUNNEL RUNNER PAYLOAD
    # ========================================================

    payload = {
        "game": (
            CURRENT_GAME_NAME
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

        # Compatibility with the shared Matthews Games
        # Supabase score table.

        "wave": 1,

        "difficulty": (
            "Endless"
        ),

        "kills": 0,
    }

    # ========================================================
    # CHECK IF A NEW-NAME ROW ALREADY EXISTS
    # ========================================================

    existing_current_row = (
        current_game_row(
            existing_rows
        )
    )

    # ========================================================
    # UPDATE TUNNEL-RUNNER ROW
    # ========================================================

    if existing_current_row is not None:

        (
            success,
            status,
            response_text,
        ) = await update_current_game_score(
            user_id=(
                cleaned_user_id
            ),

            access_token=(
                access_token
            ),

            payload=payload,
        )

        if not success:

            return (
                False,

                (
                    "Could not update "
                    "your score "
                    f"({status}). "
                    f"{response_text[:100]}"
                ),

                existing_best,

                False,
            )

    # ========================================================
    # CREATE TUNNEL-RUNNER ROW
    # ========================================================
    #
    # If the only old score was orbit-runner, we create a
    # new tunnel-runner entry instead of modifying history.
    #

    else:

        (
            success,
            status,
            response_text,
        ) = await insert_current_game_score(
            access_token=(
                access_token
            ),

            payload=payload,
        )

        if not success:

            # ------------------------------------------------
            # DUPLICATE FALLBACK
            # ------------------------------------------------
            #
            # If Supabase already has a tunnel-runner row but
            # it wasn't returned for some reason, attempt PATCH.
            #

            if status in (
                400,
                409,
            ):

                (
                    retry_success,
                    retry_status,
                    retry_text,
                ) = await update_current_game_score(
                    user_id=(
                        cleaned_user_id
                    ),

                    access_token=(
                        access_token
                    ),

                    payload=payload,
                )

                if not retry_success:

                    return (
                        False,

                        (
                            "Could not save "
                            "your score "
                            f"({retry_status}). "
                            f"{retry_text[:100]}"
                        ),

                        existing_best,

                        False,
                    )

            else:

                return (
                    False,

                    (
                        "Could not save "
                        "your score "
                        f"({status}). "
                        f"{response_text[:100]}"
                    ),

                    existing_best,

                    False,
                )

    # ========================================================
    # SUCCESS
    # ========================================================

    return (
        True,

        (
            "New personal best: "
            f"{cleaned_distance:,} m!"
        ),

        cleaned_distance,

        True,
    )


# ============================================================
# CONFIG VALIDATION
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