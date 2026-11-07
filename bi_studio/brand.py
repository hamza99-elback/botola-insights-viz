"""Botola Insights brand: post size, colors, tagline, fonts, logo, background and clubs.

Shared by every template so all posts look like one series.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter, ImageFont

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


LEAGUE_LOGO = os.path.join(ASSETS, "botolapro_logo.png")  # full-color Botola Pro logo


@lru_cache(maxsize=1)
def league_logo() -> Image.Image | None:
    """White one-color version of the Botola Pro logo (as in the designs), or None if the file is missing.

    Colored and dark parts become white; white parts become transparent (so "inwi" shows the background).
    The badge's thin outer frame is dropped, as in the designs.
    """
    if not os.path.exists(LEAGUE_LOGO):
        return None
    src = Image.open(LEAGUE_LOGO).convert("RGBA")
    rgba = np.asarray(src).astype(np.float32)
    ink = np.clip((255 - rgba[..., :3].min(-1)) / 60, 0, 1)  # 0 for white, 1 for any real color or black
    # keep only what's inside the frame: the badge outline shrunk by a bit more than the frame (~4 px)
    inside = np.asarray(src.getchannel("A").filter(ImageFilter.MinFilter(13))).astype(np.float32) / 255
    out = np.zeros_like(rgba)
    out[..., :3] = 255
    out[..., 3] = rgba[..., 3] * ink * inside
    img = Image.fromarray(out.astype(np.uint8), "RGBA")
    return img.crop(img.getbbox())


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
