from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from typing import Any

from config import (
    ALLOW_DESKTOP_TEST_ACCOUNT,
    DESKTOP_TEST_USERNAME,
    REQUIRE_WEBSITE_ACCOUNT,
    SUPABASE_PROFILES_TABLE,
    SUPABASE_PROJECT_URL,
    SUPABASE_PUBLISHABLE_KEY,
)


# ============================================================
# TUNNEL RUNNER
# PLAYER SESSION SYSTEM
# VERSION 0.1.0
# ============================================================
#
# Handles:
#
# - Website login detection
# - Supabase access token loading
# - Supabase account verification
# - Profile loading
# - Username loading
# - Role loading
# - Admin detection
# - Browser / Pygbag support
# - Desktop test account support
# - Non-blocking asynchronous account loading
#
# Tunnel Runner does NOT ask the player to type a username.
#
# On the website, the game automatically uses the account that
# is already signed into Matthew's Games.
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
# SUPABASE ENDPOINTS
# ============================================================

SUPABASE_AUTH_USER_ENDPOINT = (
    f"{SUPABASE_PROJECT_URL}"
    "/auth/v1/user"
)

SUPABASE_PROFILES_ENDPOINT = (
    f"{SUPABASE_PROJECT_URL}"
    f"/rest/v1/{SUPABASE_PROFILES_TABLE}"
)


# ============================================================
# SUPABASE PROJECT REFERENCE
# ============================================================

def get_supabase_project_reference(
) -> str:
    url = (
        SUPABASE_PROJECT_URL
        .replace(
            "https://",
            "",
        )
        .replace(
            "http://",
            "",
        )
    )

    return (
        url.split(
            "."
        )[0]
    )


SUPABASE_PROJECT_REFERENCE = (
    get_supabase_project_reference()
)


# ============================================================
# SUPABASE LOCAL STORAGE KEY
# ============================================================

SUPABASE_AUTH_STORAGE_KEY = (
    f"sb-"
    f"{SUPABASE_PROJECT_REFERENCE}"
    f"-auth-token"
)


# ============================================================
# SESSION DATA
# ============================================================

@dataclass
class PlayerSession:
    signed_in: bool = False

    verified: bool = False

    user_id: str = ""

    username: str = ""

    email: str = ""

    role: str = "player"

    access_token: str = ""

    message: str = ""

    desktop_test_account: bool = False

    # ========================================================
    # DISPLAY NAME
    # ========================================================

    @property
    def display_name(
        self,
    ) -> str:
        username = (
            self.username.strip()
        )

        if username:
            return username

        return "Player"

    # ========================================================
    # ADMIN
    # ========================================================

    @property
    def is_admin(
        self,
    ) -> bool:
        return (
            self.role
            .strip()
            .lower()
            == "admin"
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


def clean_email(
    value: Any,
) -> str:
    email = (
        str(
            value
            if value is not None
            else ""
        )
        .strip()
    )

    return email[:200]


def clean_role(
    value: Any,
) -> str:
    role = (
        str(
            value
            if value is not None
            else ""
        )
        .strip()
        .lower()
    )

    if role == "admin":
        return "admin"

    return "player"


# ============================================================
# LOGGED OUT SESSION
# ============================================================

def create_logged_out_session(
    message: str = (
        "Sign in to Matthew's Games "
        "to play Tunnel Runner."
    ),
) -> PlayerSession:
    return PlayerSession(
        signed_in=False,

        verified=False,

        user_id="",

        username="",

        email="",

        role="player",

        access_token="",

        message=message,

        desktop_test_account=False,
    )


# ============================================================
# DESKTOP TEST SESSION
# ============================================================

def create_desktop_test_session(
) -> PlayerSession:
    return PlayerSession(
        signed_in=True,

        verified=True,

        user_id=(
            "desktop-test-user"
        ),

        username=(
            DESKTOP_TEST_USERNAME
        ),

        email="",

        role="player",

        access_token="",

        message=(
            "Desktop test account active."
        ),

        desktop_test_account=True,
    )


# ============================================================
# GUEST SESSION
# ============================================================

def create_guest_session(
) -> PlayerSession:
    return PlayerSession(
        signed_in=True,

        verified=True,

        user_id="guest",

        username="Guest",

        email="",

        role="player",

        access_token="",

        message="Guest mode active.",

        desktop_test_account=False,
    )


# ============================================================
# RECURSIVE ACCESS TOKEN FINDER
# ============================================================

def find_access_token(
    value: Any,
) -> str:
    """
    Supabase auth data can have slightly different JSON layouts.

    Search recursively until an access_token is found.
    """

    if isinstance(
        value,
        dict,
    ):
        direct_token = value.get(
            "access_token"
        )

        if direct_token:
            return str(
                direct_token
            )

        for nested_value in (
            value.values()
        ):
            token = find_access_token(
                nested_value
            )

            if token:
                return token

    elif isinstance(
        value,
        list,
    ):
        for nested_value in value:
            token = find_access_token(
                nested_value
            )

            if token:
                return token

    return ""


# ============================================================
# READ TOKEN FROM WEBSITE
# ============================================================

def read_browser_access_token(
) -> str:
    if not IS_WEB:
        return ""

    try:
        import platform

        raw_value = (
            platform.window
            .localStorage
            .getItem(
                SUPABASE_AUTH_STORAGE_KEY
            )
        )

        if not raw_value:
            return ""

        raw_text = str(
            raw_value
        )

        parsed = json.loads(
            raw_text
        )

        return find_access_token(
            parsed
        )

    except Exception:
        return ""


# ============================================================
# JAVASCRIPT FETCH BRIDGE
# ============================================================

_BROWSER_FETCH_BRIDGE_INSTALLED = False


def install_browser_fetch_bridge(
) -> None:
    global _BROWSER_FETCH_BRIDGE_INSTALLED

    if not IS_WEB:
        return

    if _BROWSER_FETCH_BRIDGE_INSTALLED:
        return

    try:
        import platform

        javascript = r"""
            window.TunnelRunnerSessionAPI = {

                request: function* (
                    method,
                    url,
                    apiKey,
                    accessToken,
                    bodyText
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

        _BROWSER_FETCH_BRIDGE_INSTALLED = (
            True
        )

    except Exception:
        _BROWSER_FETCH_BRIDGE_INSTALLED = (
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
                "Browser request attempted "
                "outside the web version."
            ),
        )

    install_browser_fetch_bridge()

    if not (
        _BROWSER_FETCH_BRIDGE_INSTALLED
    ):
        return (
            False,
            0,
            (
                "Could not install the "
                "browser network bridge."
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
                .TunnelRunnerSessionAPI
                .request(
                    method.upper(),

                    url,

                    SUPABASE_PUBLISHABLE_KEY,

                    access_token,

                    body_text,
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
# VERIFY AUTH USER
# ============================================================

async def verify_supabase_user(
    access_token: str,
) -> tuple[
    bool,
    str,
    str,
    str,
]:
    """
    Return:

        success
        user_id
        email
        message
    """

    if not access_token:
        return (
            False,
            "",
            "",
            "No website login session was found.",
        )

    (
        success,
        status,
        response_text,
    ) = await browser_request(
        "GET",

        SUPABASE_AUTH_USER_ENDPOINT,

        access_token=(
            access_token
        ),
    )

    if not success:
        return (
            False,
            "",
            "",
            (
                "Your login session "
                "could not be verified "
                f"({status})."
            ),
        )

    try:
        user_data = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        return (
            False,
            "",
            "",
            (
                "Supabase returned invalid "
                "account information."
            ),
        )

    if not isinstance(
        user_data,
        dict,
    ):
        return (
            False,
            "",
            "",
            (
                "Supabase returned invalid "
                "account information."
            ),
        )

    user_id = clean_user_id(
        user_data.get(
            "id",
            "",
        )
    )

    email = clean_email(
        user_data.get(
            "email",
            "",
        )
    )

    if not user_id:
        return (
            False,
            "",
            email,
            (
                "The signed-in account "
                "has no user ID."
            ),
        )

    return (
        True,
        user_id,
        email,
        "Account verified.",
    )


# ============================================================
# LOAD PROFILE
# ============================================================

async def load_player_profile(
    user_id: str,
    access_token: str,
) -> tuple[
    bool,
    str,
    str,
    str,
]:
    """
    Return:

        success
        username
        role
        message
    """

    user_id = clean_user_id(
        user_id
    )

    if not user_id:
        return (
            False,
            "",
            "player",
            "Missing user ID.",
        )

    url = (
        f"{SUPABASE_PROFILES_ENDPOINT}"
        "?select=username,role"
        f"&id=eq.{user_id}"
        "&limit=1"
    )

    (
        success,
        status,
        response_text,
    ) = await browser_request(
        "GET",

        url,

        access_token=(
            access_token
        ),
    )

    if not success:
        return (
            False,
            "",
            "player",
            (
                "Your player profile "
                "could not be loaded "
                f"({status})."
            ),
        )

    try:
        rows = json.loads(
            response_text
        )

    except json.JSONDecodeError:
        return (
            False,
            "",
            "player",
            (
                "Supabase returned invalid "
                "profile information."
            ),
        )

    if not isinstance(
        rows,
        list,
    ):
        return (
            False,
            "",
            "player",
            (
                "Supabase returned invalid "
                "profile information."
            ),
        )

    if not rows:
        return (
            False,
            "",
            "player",
            (
                "No Matthew's Games profile "
                "was found for this account."
            ),
        )

    profile = rows[0]

    if not isinstance(
        profile,
        dict,
    ):
        return (
            False,
            "",
            "player",
            "Invalid player profile.",
        )

    username = clean_username(
        profile.get(
            "username",
            "Player",
        )
    )

    role = clean_role(
        profile.get(
            "role",
            "player",
        )
    )

    return (
        True,
        username,
        role,
        "Player profile loaded.",
    )


# ============================================================
# LOAD COMPLETE PLAYER SESSION
# ============================================================

async def load_player_session(
) -> PlayerSession:
    # ========================================================
    # DESKTOP
    # ========================================================

    if not IS_WEB:
        if (
            ALLOW_DESKTOP_TEST_ACCOUNT
        ):
            return (
                create_desktop_test_session()
            )

        return (
            create_logged_out_session(
                (
                    "Tunnel Runner requires "
                    "the website version."
                )
            )
        )

    # ========================================================
    # GUEST MODE
    # ========================================================

    if not REQUIRE_WEBSITE_ACCOUNT:
        return create_guest_session()

    # ========================================================
    # READ WEBSITE TOKEN
    # ========================================================

    access_token = (
        read_browser_access_token()
    )

    if not access_token:
        return (
            create_logged_out_session(
                (
                    "You are not signed in. "
                    "Return to Matthew's Games "
                    "and sign in first."
                )
            )
        )

    # ========================================================
    # VERIFY AUTH ACCOUNT
    # ========================================================

    (
        verified,
        user_id,
        email,
        verification_message,
    ) = await verify_supabase_user(
        access_token
    )

    if not verified:
        return (
            create_logged_out_session(
                verification_message
            )
        )

    # ========================================================
    # LOAD WEBSITE PROFILE
    # ========================================================

    (
        profile_loaded,
        username,
        role,
        profile_message,
    ) = await load_player_profile(
        user_id,
        access_token,
    )

    if not profile_loaded:
        return (
            create_logged_out_session(
                profile_message
            )
        )

    # ========================================================
    # COMPLETE SESSION
    # ========================================================

    return PlayerSession(
        signed_in=True,

        verified=True,

        user_id=user_id,

        username=username,

        email=email,

        role=role,

        access_token=access_token,

        message=(
            f"Signed in as {username}."
        ),

        desktop_test_account=False,
    )


# ============================================================
# PLAYER SESSION MANAGER
# ============================================================

class PlayerSessionManager:
    """
    Non-blocking account loader.

    main.py should call begin_loading() once, then call update()
    each frame until loaded becomes True.
    """

    def __init__(
        self,
    ):
        self.session = (
            PlayerSession(
                signed_in=False,

                verified=False,

                message=(
                    "Checking your account..."
                ),
            )
        )

        self.task: (
            asyncio.Task[
                PlayerSession
            ]
            | None
        ) = None

        self.loading = False

        self.loaded = False

        self.last_error = ""

    # ========================================================
    # BEGIN LOADING
    # ========================================================

    def begin_loading(
        self,
    ) -> None:
        if (
            self.task is not None
            and not self.task.done()
        ):
            return

        self.loading = True

        self.loaded = False

        self.last_error = ""

        self.session = (
            PlayerSession(
                signed_in=False,

                verified=False,

                message=(
                    "Checking your account..."
                ),
            )
        )

        self.task = (
            asyncio.create_task(
                load_player_session()
            )
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
    ) -> bool:
        """
        Return True on the frame account loading finishes.
        """

        if self.task is None:
            return False

        if not self.task.done():
            return False

        try:
            self.session = (
                self.task.result()
            )

            self.last_error = ""

        except Exception as error:
            self.last_error = str(
                error
            )

            self.session = (
                create_logged_out_session(
                    (
                        "Account error: "
                        f"{error}"
                    )
                )
            )

        self.task = None

        self.loading = False

        self.loaded = True

        return True

    # ========================================================
    # RELOAD
    # ========================================================

    def reload(
        self,
    ) -> None:
        if (
            self.task is not None
            and not self.task.done()
        ):
            self.task.cancel()

        self.task = None

        self.begin_loading()

    # ========================================================
    # SIGNED IN
    # ========================================================

    @property
    def signed_in(
        self,
    ) -> bool:
        return (
            self.session.signed_in
        )

    # ========================================================
    # VERIFIED
    # ========================================================

    @property
    def verified(
        self,
    ) -> bool:
        return (
            self.session.verified
        )

    # ========================================================
    # USER ID
    # ========================================================

    @property
    def user_id(
        self,
    ) -> str:
        return (
            self.session.user_id
        )

    # ========================================================
    # USERNAME
    # ========================================================

    @property
    def username(
        self,
    ) -> str:
        return (
            self.session.display_name
        )

    # ========================================================
    # EMAIL
    # ========================================================

    @property
    def email(
        self,
    ) -> str:
        return (
            self.session.email
        )

    # ========================================================
    # ROLE
    # ========================================================

    @property
    def role(
        self,
    ) -> str:
        return (
            self.session.role
        )

    # ========================================================
    # ADMIN
    # ========================================================

    @property
    def is_admin(
        self,
    ) -> bool:
        return (
            self.session.is_admin
        )

    # ========================================================
    # ACCESS TOKEN
    # ========================================================

    @property
    def access_token(
        self,
    ) -> str:
        return (
            self.session.access_token
        )

    # ========================================================
    # MESSAGE
    # ========================================================

    @property
    def message(
        self,
    ) -> str:
        return (
            self.session.message
        )

    # ========================================================
    # DESKTOP TEST ACCOUNT
    # ========================================================

    @property
    def desktop_test_account(
        self,
    ) -> bool:
        return (
            self.session
            .desktop_test_account
        )


# ============================================================
# SAFE DEBUG INFO
# ============================================================

def get_session_debug_info(
    session: PlayerSession,
) -> dict[str, Any]:
    """
    Access token is intentionally excluded.
    """

    return {
        "signed_in": (
            session.signed_in
        ),

        "verified": (
            session.verified
        ),

        "user_id": (
            session.user_id
        ),

        "username": (
            session.display_name
        ),

        "email": (
            session.email
        ),

        "role": (
            session.role
        ),

        "is_admin": (
            session.is_admin
        ),

        "desktop_test_account": (
            session
            .desktop_test_account
        ),

        "message": (
            session.message
        ),
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_player_session_config(
) -> None:
    if not SUPABASE_PROJECT_URL:
        raise ValueError(
            "SUPABASE_PROJECT_URL is empty."
        )

    if not SUPABASE_PUBLISHABLE_KEY:
        raise ValueError(
            "SUPABASE_PUBLISHABLE_KEY is empty."
        )

    if not SUPABASE_PROJECT_REFERENCE:
        raise ValueError(
            (
                "Could not determine the "
                "Supabase project reference."
            )
        )

    if not SUPABASE_PROFILES_TABLE:
        raise ValueError(
            "SUPABASE_PROFILES_TABLE is empty."
        )


validate_player_session_config()