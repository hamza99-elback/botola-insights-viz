"""Botola Insights brand: post size, colors, tagline, fonts, logo, background and clubs.

Shared by every template so all posts look like one series.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from PIL import Image, ImageFont

W, H = 1080, 1350
NAVY = (4, 21, 42)
CYAN = (25, 183, 244)
TAGLINE = "EMPOWERING MOROCCAN LEAGUE WITH DATA"

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")


@lru_cache(maxsize=None)
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(ASSETS, "fonts", name), size)


@lru_cache(maxsize=1)
def logo() -> Image.Image:
    return Image.open(os.path.join(ASSETS, "botola_logo.png")).convert("RGBA")


@lru_cache(maxsize=1)
def background() -> Image.Image:
    return Image.open(os.path.join(ASSETS, "background.jpg")).convert("RGB").resize((W, H), Image.LANCZOS)


def load_teams() -> dict:
    with open(os.path.join(HERE, "teams.json"), encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_help", None)
    return data


def crest_image(team: str, teams: dict | None = None) -> Image.Image | None:
    teams = teams or load_teams()
    info = teams.get(team)
    if not info:
        return None
    path = os.path.join(ASSETS, "crests", info["crest"])
    return Image.open(path).convert("RGBA") if os.path.exists(path) else None
