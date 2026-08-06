from __future__ import annotations

import asyncio
import json
import platform
import sys
from dataclasses import dataclass
from typing import Any


SUPABASE_PROJECT_URL = "https://bcarxudxfmsibvnteoaj.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_S7ki2S3tODs4shwWovSY6w_-2jknXXg"
AUTH_STORAGE_KEY = "sb-bcarxudxfmsibvnteoaj-auth-token"

AUTH_USER_ENDPOINT = f"{SUPABASE_PROJECT_URL}/auth/v1/user"
PROFILES_ENDPOINT = f"{SUPABASE_PROJECT_URL}/rest/v1/profiles"

IS_WEB = sys.platform in ("emscripten", "wasi")


@dataclass
class PlayerSession:
    signed_in: bool = False
    user_id: str = ""
    username: str = ""
    access_token: str = ""
    message: str = "Sign in on the website to play."


def _find_access_token(value: Any) -> str:
    if isinstance(value, dict):
        token = value.get("access_token")
        if token:
            return str(token)

        for nested in value.values():
            token = _find_access_token(nested)
            if token:
                return token

    elif isinstance(value, list):
        for nested in value:
            token = _find_access_token(nested)
            if token:
                return token

    return ""


def _read_browser_access_token() -> str:
    if not IS_WEB:
        return ""

    try:
        raw_value = platform.window.localStorage.getItem(
            AUTH_STORAGE_KEY
        )

        if not raw_value:
            return ""

        return _find_access_token(
            json.loads(str(raw_value))
        )
    except Exception:
        return ""


_BROWSER_FETCH_READY = False


def _install_browser_fetch() -> None:
    global _BROWSER_FETCH_READY

    if not IS_WEB or _BROWSER_FETCH_READY:
        return

    platform.window.eval("""
        window.MatthewsSessionFetch = {
            request: function* (url, apiKey, token) {
                let finished = false;
                let result = "";

                fetch(url, {
                    method: "GET",
                    headers: {
                        "apikey": apiKey,
                        "Authorization": "Bearer " + token,
                        "Accept": "application/json"
                    }
                })
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


async def _browser_get(
    url: str,
    token: str,
) -> tuple[bool, int, str]:
    _install_browser_fetch()

    try:
        raw_result = await platform.jsiter(
            platform.window.MatthewsSessionFetch.request(
                url,
                SUPABASE_PUBLISHABLE_KEY,
                token,
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


async def load_player_session() -> PlayerSession:
    if not IS_WEB:
        return PlayerSession(
            message=(
                "This version requires the website. "
                "Open the game from Matthew's Games."
            )
        )

    access_token = _read_browser_access_token()

    if not access_token:
        return PlayerSession()

    success, status, user_text = await _browser_get(
        AUTH_USER_ENDPOINT,
        access_token,
    )

    if not success:
        return PlayerSession(
            message=f"Sign-in session could not be verified ({status})."
        )

    try:
        user_data = json.loads(user_text)
        user_id = str(user_data.get("id", ""))
    except (json.JSONDecodeError, AttributeError):
        user_id = ""

    if not user_id:
        return PlayerSession(
            message="The signed-in account could not be identified."
        )

    profile_url = (
        f"{PROFILES_ENDPOINT}"
        f"?select=username"
        f"&id=eq.{user_id}"
        f"&limit=1"
    )

    success, status, profile_text = await _browser_get(
        profile_url,
        access_token,
    )

    if not success:
        return PlayerSession(
            message=f"Player profile could not be loaded ({status})."
        )

    try:
        rows = json.loads(profile_text)
        username = str(rows[0]["username"]).strip()[:16]
    except (json.JSONDecodeError, IndexError, KeyError, TypeError):
        username = ""

    if not username:
        return PlayerSession(
            message="No gaming username was found for this account."
        )

    return PlayerSession(
        signed_in=True,
        user_id=user_id,
        username=username,
        access_token=access_token,
        message="Signed-in player loaded.",
    )