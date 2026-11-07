"""Invisible component that keeps the "Remember me" login token in the browser (localStorage).

Plain HTML/JS, no build step. One action per call:
    login_storage("read", key=...)          -> {"token": str | None} once the browser answers, else None
    login_storage("set", token, key=...)    -> stores the token (returns None)
    login_storage("clear", key=...)         -> deletes it (returns None)
"""
from __future__ import annotations

import os

import streamlit.components.v1 as components

_component = components.declare_component(
    "bi_login_storage", path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
)


def login_storage(action: str, token: str | None = None, key: str | None = None):
    return _component(action=action, token=token, key=key, default=None)
