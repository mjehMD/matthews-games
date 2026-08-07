from __future__ import annotations

import json
import platform
import sys
import urllib.parse
from typing import Any

from config import GAME_SLUG, MAX_LEADERBOARD_ENTRIES, SUPABASE_KEY, SUPABASE_SCORES_TABLE, SUPABASE_URL

IS_WEB = sys.platform in ("emscripten", "wasi")
ENDPOINT = f"{SUPABASE_URL}/rest/v1/{SUPABASE_SCORES_TABLE}"
_FETCH_INSTALLED = False


def clean_distance(value: Any) -> int:
    try:
        return max(0, min(100_000_000, round(float(value))))
    except (TypeError, ValueError):
        return 0


def clean_name(value: Any) -> str:
    return str(value).strip()[:16] or "Player"


def _install_fetch() -> None:
    global _FETCH_INSTALLED
    if not IS_WEB or _FETCH_INSTALLED:
        return
    platform.window.eval(r'''
        window.OrbitRushLeaderboardV3 = {
            request: function* (method, url, key, token, body, prefer) {
                let done = false;
                let result = "";
                const headers = {
                    "apikey": key,
                    "Authorization": "Bearer " + (token || key),
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                };
                if (prefer) headers["Prefer"] = prefer;
                const options = {method: method, headers: headers};
                if (body) options.body = body;
                fetch(url, options).then(async response => {
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


async def _request(method: str, url: str, token: str = "", body: dict[str, Any] | None = None, prefer: str = "") -> tuple[bool, int, str]:
    if not IS_WEB:
        return False, 0, "Online leaderboard is available in the website build."
    _install_fetch()
    try:
        raw = await platform.jsiter(
            platform.window.OrbitRushLeaderboardV3.request(
                method,
                url,
                SUPABASE_KEY,
                token,
                json.dumps(body) if body is not None else "",
                prefer,
            )
        )
        result = json.loads(str(raw))
        return bool(result.get("ok")), int(result.get("status", 0)), str(result.get("text", ""))
    except Exception as error:
        return False, 0, str(error)


async def load_online_leaderboard() -> tuple[list[dict[str, Any]], str]:
    query = urllib.parse.urlencode({
        "select": "user_id,player_name,score,created_at",
        "game": f"eq.{GAME_SLUG}",
        "order": "score.desc,created_at.asc",
        "limit": MAX_LEADERBOARD_ENTRIES,
    })
    ok, status, text = await _request("GET", f"{ENDPOINT}?{query}")
    if not ok:
        return [], f"Could not load leaderboard ({status})."
    try:
        rows = json.loads(text)
    except json.JSONDecodeError:
        return [], "Leaderboard returned invalid data."

    result = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                result.append({
                    "user_id": str(row.get("user_id", "")),
                    "name": clean_name(row.get("player_name", "Player")),
                    "distance": clean_distance(row.get("score", 0)),
                })
    return result[:MAX_LEADERBOARD_ENTRIES], "All-time leaderboard loaded."


async def load_player_best_distance(user_id: str, token: str) -> tuple[int, str]:
    if not user_id or not token:
        return 0, "No online account available."
    query = urllib.parse.urlencode({
        "select": "score",
        "game": f"eq.{GAME_SLUG}",
        "user_id": f"eq.{user_id}",
        "limit": 1,
    })
    ok, status, text = await _request("GET", f"{ENDPOINT}?{query}", token)
    if not ok:
        return 0, f"Could not load personal best ({status})."
    try:
        rows = json.loads(text)
        if isinstance(rows, list) and rows:
            return clean_distance(rows[0].get("score", 0)), "Personal best loaded."
    except (json.JSONDecodeError, AttributeError):
        pass
    return 0, "No online best yet."


async def submit_endless_distance(name: str, distance: float, user_id: str, token: str) -> tuple[bool, str, int]:
    if not user_id or not token:
        return False, "A website account is required to submit.", 0

    current, _ = await load_player_best_distance(user_id, token)
    score = clean_distance(distance)
    if current >= score:
        return True, "Your existing best is higher.", current

    query = urllib.parse.urlencode({
        "game": f"eq.{GAME_SLUG}",
        "user_id": f"eq.{user_id}",
    })
    payload = {
        "game": GAME_SLUG,
        "user_id": user_id,
        "player_name": clean_name(name),
        "score": score,
        "wave": 1,
        "difficulty": "Endless",
        "kills": 0,
    }

    method = "PATCH" if current > 0 else "POST"
    url = f"{ENDPOINT}?{query}" if method == "PATCH" else ENDPOINT
    ok, status, text = await _request(method, url, token, payload, "return=minimal")
    if ok and status in (200, 201, 204):
        return True, f"New personal best: {score:,} m", score
    return False, f"Distance was not saved ({status}): {text}", current
