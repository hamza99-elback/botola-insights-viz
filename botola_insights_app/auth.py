"""Team login: one shared username and password, kept in Streamlit secrets.

Create the [auth_basic] secrets block (the password is typed at a prompt, never stored in clear):

    python -m botola_insights_app.auth

Put the block in .streamlit/secrets.toml locally and in the app's Secrets settings on the cloud.
"""
from __future__ import annotations

import getpass
import hashlib
import hmac
import secrets

import streamlit as st

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000


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
        return True
    credentials = _credentials()
    if credentials is None:
        st.error("Login is not configured: add the [auth_basic] secrets (see .streamlit/secrets.toml.example).")
        return False

    # Keeps the columns out of the page's first position: st.tabs replacing a block there can
    # crash the browser to a white page after login (Streamlit reuses the old block's children).
    st.empty()
    _, center, _ = st.columns(3)
    with center:
        if logo:
            st.image(logo, width=150)
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary")
        if submitted:
            user_ok = hmac.compare_digest(username.strip().encode("utf-8"), credentials[0].encode("utf-8"))
            password_ok = verify_password(password, credentials[1])
            if user_ok and password_ok:
                st.session_state["logged_in"] = True
                st.rerun()
            st.error("Wrong username or password.")
    return False


def logout_button():
    st.button("Log out", key="logout", on_click=st.session_state.clear)


if __name__ == "__main__":
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    if not username or not password or password != getpass.getpass("Repeat password: "):
        raise SystemExit("Username or password empty, or the passwords don't match. Nothing created.")
    print(f'\n[auth_basic]\nusername = "{username}"\npassword_hash = "{hash_password(password)}"')
