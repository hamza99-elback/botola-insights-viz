"""Team login: one shared username and password, kept in Streamlit secrets.

Create the [auth_basic] secrets block (the password is typed at a prompt, never stored in clear):

    python -m botola_insights_app.auth

Put the block in .streamlit/secrets.toml locally and in the app's Secrets settings on the cloud.

"Remember me": the browser keeps a signed token (expiry + HMAC signature), never the username or
password. The signing key is derived from the password hash, so changing the password logs out
every remembered device. Log out deletes the token from the browser.
"""
from __future__ import annotations

import getpass
import hashlib
import hmac
import secrets
import time

import streamlit as st

from botola_insights_app.login_storage import login_storage

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
REMEMBER_DAYS = 7
TOKEN_VERSION = "v1"


def hash_password(password: str, salt: bytes | None = None, iterations: int = ITERATIONS) -> str:
    """Salted hash stored as "pbkdf2_sha256$iterations$salt$digest"."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """True if password matches a hash_password() value. A malformed hash never matches."""
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        expected = bytes.fromhex(digest)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
    except (AttributeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


def _sign(username: str, password_hash: str, expiry: int) -> str:
    key = hashlib.sha256(b"bi-studio-remember-me|" + password_hash.encode("utf-8")).digest()
    return hmac.new(key, f"{username}|{expiry}".encode("utf-8"), hashlib.sha256).hexdigest()


def make_token(username: str, password_hash: str, days: float = REMEMBER_DAYS, now: float | None = None) -> str:
    """Signed "remember me" token: "v1.<expiry unix time>.<signature>". Holds no credentials."""
    expiry = int((time.time() if now is None else now) + days * 86400)
    return f"{TOKEN_VERSION}.{expiry}.{_sign(username, password_hash, expiry)}"


def token_valid(token, username: str, password_hash: str, now: float | None = None) -> bool:
    """True if the token was made with these credentials and hasn't expired."""
    try:
        version, expiry, signature = str(token).split(".")
        expiry = int(expiry)
    except ValueError:
        return False
    if version != TOKEN_VERSION or expiry < (time.time() if now is None else now):
        return False
    return hmac.compare_digest(signature, _sign(username, password_hash, expiry))


def _credentials() -> tuple[str, str] | None:
    """(username, password hash) from the secrets, or None if they aren't configured."""
    if not st.secrets.load_if_toml_exists():  # avoids Streamlit's own error, which shows server paths
        return None
    try:
        auth = st.secrets["auth_basic"]
        return str(auth["username"]), str(auth["password_hash"])
    except (KeyError, FileNotFoundError):
        return None


def require_login(logo: str | None = None) -> bool:
    """True once the user has logged in; until then draws the login form and returns False.

    The caller must stop drawing the page when this returns False. No credentials configured =
    no access. Returns instead of calling st.stop(): Streamlit's health check (used by Community
    Cloud) only counts a script run as healthy if the script ends normally.
    """
    if st.session_state.get("logged_in"):
        token = st.session_state.pop("_remember_token", None)
        if token:  # just logged in with "Remember me": store the token in the browser
            with st.sidebar:
                login_storage("set", token, key="login_storage_set")
        return True
    credentials = _credentials()
    if credentials is None:
        st.error("Login is not configured: add the [auth_basic] secrets (see .streamlit/secrets.toml.example).")
        return False

    # Keeps the columns out of the page's first position: st.tabs replacing a block there can
    # crash the browser to a white page after login (Streamlit reuses the old block's children).
    st.empty()
    # a token remembered by this browser logs in without the form (after logout: delete it instead)
    action = "clear" if st.session_state.pop("_forget_login", False) else "read"
    stored = login_storage(action, key=f"login_storage_{action}")
    token = (stored or {}).get("token")
    if token and token_valid(token, *credentials):
        st.session_state["logged_in"] = True
        st.rerun()

    _, center, _ = st.columns(3)
    with center:
        if logo:
            st.image(logo, width=150)
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember = st.checkbox(f"Remember me on this device ({REMEMBER_DAYS} days)", value=True,
                                   help="Untick on a shared computer.")
            submitted = st.form_submit_button("Log in", type="primary")
        if submitted:
            user_ok = hmac.compare_digest(username.strip().encode("utf-8"), credentials[0].encode("utf-8"))
            password_ok = verify_password(password, credentials[1])
            if user_ok and password_ok:
                st.session_state["logged_in"] = True
                if remember:
                    st.session_state["_remember_token"] = make_token(*credentials)
                st.rerun()
            st.error("Wrong username or password.")
    return False


def _logout():
    st.session_state.clear()
    st.session_state["_forget_login"] = True  # the login page then deletes the browser's token


def logout_button():
    st.button("Log out", key="logout", on_click=_logout)


if __name__ == "__main__":
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    if not username or not password or password != getpass.getpass("Repeat password: "):
        raise SystemExit("Username or password empty, or the passwords don't match. Nothing created.")
    print(f'\n[auth_basic]\nusername = "{username}"\npassword_hash = "{hash_password(password)}"')
