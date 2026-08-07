from __future__ import annotations

import asyncio
import json
import platform
import sys
from dataclasses import dataclass
from typing import Any

from config import SUPABASE_KEY, SUPABASE_URL

IS_WEB = sys.platform in ("emscripten", "wasi")
PROJECT_REFERENCE = "bcarxudxfmsibvnteoaj"
AUTH_STORAGE_KEY = f"sb-{PROJECT_REFERENCE}-auth-token"


@dataclass
class PlayerSession:
    signed_in: bool = False
    user_id: str = ""
    username: str = "Player"
    access_token: str = ""
    role: str = "player"
    message: str = "Sign in on Matthew's Games before playing."


def _find_token(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("access_token"):
            return str(value["access_token"])
        for nested in value.values():
            token = _find_token(nested)
            if token:
                return token
    elif isinstance(value, list):
        for nested in value:
            token = _find_token(nested)
            if token:
                return token
    return ""


def _read_token() -> str:
    if not IS_WEB:
        return ""
    try:
        raw = platform.window.localStorage.getItem(AUTH_STORAGE_KEY)
        return _find_token(json.loads(str(raw))) if raw else ""
    except Exception:
        return ""


_FETCH_INSTALLED = False


def _install_fetch() -> None:
    global _FETCH_INSTALLED
    if not IS_WEB or _FETCH_INSTALLED:
        return
    platform.window.eval(r'''
        window.OrbitRushSessionV3 = {
            get: function* (url, key, token) {
                let done = false;
                let result = "";
                fetch(url, {
                    method: "GET",
                    headers: {
                        "apikey": key,
                        "Authorization": "Bearer " + token,
                        "Accept": "application/json"
                    }
                }).then(async response => {
                    result = JSON.stringify({
                        ok: response.ok,
                        status: response.status,
                        text: await response.text()
                    });
                    done = true;
                }).catch(error => {
                    result = JSON.stringify({ok:false,status:0,text:String(error)});
                    done = true;
                });
                while (!done) yield;
                yield result;
            }
        };
    ''')
    _FETCH_INSTALLED = True


async def _get(url: str, token: str) -> tuple[bool, int, str]:
    _install_fetch()
    try:
        raw = await platform.jsiter(
            platform.window.OrbitRushSessionV3.get(url, SUPABASE_KEY, token)
        )
        result = json.loads(str(raw))
        return bool(result.get("ok")), int(result.get("status", 0)), str(result.get("text", ""))
    except Exception as error:
        return False, 0, str(error)


async def load_player_session() -> PlayerSession:
    # Desktop mode is intentionally available for testing.
    if not IS_WEB:
        return PlayerSession(
            signed_in=True,
            user_id="desktop-test",
            username="Desktop Player",
            access_token="",
            role="player",
            message="Desktop test mode.",
        )

    token = _read_token()
    if not token:
        return PlayerSession()

    ok, status, text = await _get(f"{SUPABASE_URL}/auth/v1/user", token)
    if not ok:
        return PlayerSession(message=f"Could not verify account ({status}).")

    try:
        user = json.loads(text)
        user_id = str(user.get("id", ""))
    except (json.JSONDecodeError, AttributeError):
        return PlayerSession(message="Invalid account response.")

    if not user_id:
        return PlayerSession(message="The account has no user ID.")

    profile_url = (
        f"{SUPABASE_URL}/rest/v1/profiles"
        f"?select=username,role&id=eq.{user_id}&limit=1"
    )
    ok, status, text = await _get(profile_url, token)
    username = "Player"
    role = "player"

    if ok:
        try:
            rows = json.loads(text)
            if isinstance(rows, list) and rows:
                username = str(rows[0].get("username", "Player")).strip()[:16] or "Player"
                role = "admin" if str(rows[0].get("role", "player")).lower() == "admin" else "player"
        except (json.JSONDecodeError, AttributeError):
            pass

    return PlayerSession(
        signed_in=True,
        user_id=user_id,
        username=username,
        access_token=token,
        role=role,
        message=f"Signed in as {username}.",
    )
