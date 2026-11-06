"""Match stats: full-bleed match photo with a card of home/away stacked bars."""
from __future__ import annotations

import os
import re
from functools import lru_cache

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter

from ..brand import ASSETS, NAVY, W, H, crest_image, font, load_teams, logo
from ..fields import Color, Column, Photo, Placement, Row, Table, Team, Template
from ..primitives import as_image, blur_composite, fit_text, guides, slug, spaced, spaced_len, tagline

LEAGUE_LOGO = os.path.join(ASSETS, "league_logo.png")  # optional, drawn top-left when present

CARD_W, CARD_BOTTOM = 604, 1212
PANEL_X0, PANEL_X1, PANEL_TOP = 93, 510, 170  # stats panel inside the card (card coordinates)
ROW_FIRST, ROW_PITCH = 40, 48                 # first label center / distance between rows (panel coordinates)
BAR_OFFSET, BAR_H, BAR_PAD = 10, 9, 12        # bar top below the label center, bar height, side padding

PLACEMENT = Placement()  # zoom 1.0 = photo covers the post, centered


def _card_geometry(n_rows: int) -> tuple[int, int, int]:
    """(card x0, card y0, panel height) for n stat rows; the card grows upward from CARD_BOTTOM."""
    n = max(min(n_rows, 8), 1)
    panel_h = ROW_FIRST + (n - 1) * ROW_PITCH + BAR_OFFSET + BAR_H + 14
    return (W - CARD_W) // 2, CARD_BOTTOM - (PANEL_TOP + panel_h + 43), panel_h


def guide_boxes(values: dict | None = None) -> list[tuple[int, int, int, int]]:
    """Areas to keep faces out of: the stats card, the league logo and the tagline."""
    x0, y0, _ = _card_geometry(len((values or {}).get("rows") or []) or 6)
    return [(x0, y0, x0 + CARD_W, CARD_BOTTOM), (0, 0, 130, 160), (120, 1285, 960, 1330)]


def _number(text) -> float:
    """First number in a cell: "61%" -> 61, "1,5" -> 1.5, "" -> 0."""
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(text or ""))
    return float(m.group().replace(",", ".")) if m else 0.0


def _rgb(color, fallback) -> tuple[int, int, int]:
    if color is None:
        return tuple(fallback)
    return ImageColor.getrgb(color)[:3] if isinstance(color, str) else tuple(color)[:3]


def _cover(photo: Image.Image, zoom: float, dx: int, dy: int) -> Image.Image:
    """Photo placed with PLACEMENT (zoom 1.0 covers the post), shifted by dx/dy.

    Gaps left by zooming out or shifting are filled with a blurred, darkened cover-fit copy
    of the same photo, so there is never a hard edge.
    """
    left, top, pw, ph = PLACEMENT.box(photo.width, photo.height, zoom, dx, dy)
    if left <= 0 and top <= 0 and left + pw >= W and top + ph >= H:
        canvas = Image.new("RGB", (W, H))  # photo covers everything: no fill needed
    else:  # blur at quarter size: same soft look, ~16x less work
        cover = max(W / photo.width, H / photo.height) / 4
        bw, bh = max(1, round(photo.width * cover)), max(1, round(photo.height * cover))
        qw, qh = W // 4, H // 4
        small = photo.resize((bw, bh), Image.BILINEAR)
        small = small.crop(((bw - qw) // 2, (bh - qh) // 2, (bw - qw) // 2 + qw, (bh - qh) // 2 + qh))
        small = Image.blend(small.filter(ImageFilter.GaussianBlur(30 / 4)), Image.new("RGB", (qw, qh), NAVY), 0.45)
        canvas = small.resize((W, H), Image.BILINEAR)
    # resize only the part of the photo that lands inside the post (zoomed in, most of it doesn't)
    x0, y0, x1, y1 = max(0, left), max(0, top), min(W, left + pw), min(H, top + ph)
    if x0 < x1 and y0 < y1:
        sx, sy = photo.width / pw, photo.height / ph
        src = ((x0 - left) * sx, (y0 - top) * sy, (x1 - left) * sx, (y1 - top) * sy)
        canvas.paste(photo.resize((x1 - x0, y1 - y0), Image.LANCZOS, box=src), (x0, y0))
    return canvas


@lru_cache(maxsize=1)
def _shade_grid_factors():
    """Top/bottom darkening and the bottom pitch grid (same for every post) as out = img * keep + add."""
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a_bot = np.clip((ys - 0.58) / 0.42, 0, 1) ** 1.3 * 0.72
    a_top = np.clip((0.14 - ys) / 0.14, 0, 1) * 0.35
    alpha = np.broadcast_to(1 - (1 - a_bot) * (1 - a_top), (H, W))[..., None]
    grid = np.zeros((H, W), np.float32)
    grid[:, 13::27] = 1
    grid[13::27, :] = 1
    grid = (grid * np.clip((ys - 0.60) / 0.22, 0, 1) * 0.16)[..., None]
    keep = (1 - alpha) * (1 - grid)
    add = np.array((2, 8, 16), np.float32) * alpha * (1 - grid) + np.array((200, 225, 200), np.float32) * grid
    # rows that change at all (the middle of the post is untouched): only those are computed
    changed = np.nonzero((keep != 1).any(axis=(1, 2)) | (add != 0).any(axis=(1, 2)))[0]
    bands = [(int(a[0]), int(a[-1]) + 1) for a in np.split(changed, np.nonzero(np.diff(changed) > 1)[0] + 1)]
    return keep.astype(np.float32), add.astype(np.float32), bands


def _shade_and_grid(canvas: Image.Image) -> Image.Image:
    """Darken top and bottom, and fade a thin pitch grid into the bottom of the post."""
    keep, add, bands = _shade_grid_factors()
    arr = np.array(canvas, dtype=np.uint8)
    for y0, y1 in bands:
        arr[y0:y1] = (arr[y0:y1].astype(np.float32) * keep[y0:y1] + add[y0:y1]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")


def _paste_fit(canvas, img, cx, cy, box):
    """Paste img scaled to fit a box x box square, centered on (cx, cy)."""
    img = img.convert("RGBA")
    img = img.crop(img.getbbox())
    s = box / max(img.size)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    canvas.alpha_composite(img, (round(cx - img.width / 2), round(cy - img.height / 2)))


def _card(canvas, x0, y0, x1, y1):
    """Dark rounded card with a lighter left half and a thin border."""
    sh = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 3), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((0, 0, x1 - x0, y1 - y0 + 2), 14, fill=(0, 0, 0, 140))
    blur_composite(canvas, sh, (x0, y0 + 8), 14)

    # work in the card's area only (+ a margin so the soft left-half edge blurs as on a full frame)
    pad = 24
    size = (x1 - x0 + 1 + 2 * pad, y1 - y0 + 1 + 2 * pad)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), 14, fill=255)
    left = Image.new("L", size, 0)
    ImageDraw.Draw(left).rectangle((pad, pad, pad + (x0 + x1) // 2 - x0, pad + y1 - y0), fill=95)
    left = left.filter(ImageFilter.GaussianBlur(5))
    layer = Image.composite(Image.new("RGBA", size, (18, 40, 86, 238)), Image.new("RGBA", size, (5, 14, 36, 238)), left)
    layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.getchannel("A")), np.asarray(mask))))
    canvas.alpha_composite(layer, (x0 - pad, y0 - pad))
    ImageDraw.Draw(canvas).rounded_rectangle((x0, y0, x1, y1), 14, outline=(62, 82, 118), width=2)


def render_match_stats(
    home_team: str,
    away_team: str,
    rows: list[dict],
    photo,
    photo_zoom: float = 1.0,
    photo_x: int = 0,
    photo_y: int = 0,
    home_color=None,
    away_color="#FFFFFF",
    show_guides: bool = False,
) -> Image.Image:
    """Match stats post: photo background, crests + logo, one stacked bar per stat.

    rows: up to 8 dicts {"label": "Possession", "home": "61%", "away": "39%"}. Values are
          printed as typed; the bar split is home / (home + away) using the numbers in them.
    home_color / away_color: bar colors ("#RRGGBB" or [r, g, b]); home_color=None uses the
          home team's color from teams.json.
    photo_zoom: 1.0 = photo covers the post; photo_x / photo_y: shift in pixels (+ = right / down).
    """
    teams = load_teams()
    home_rgb = _rgb(home_color, teams.get(home_team, {}).get("color", (20, 140, 60)))
    away_rgb = _rgb(away_color, (255, 255, 255))

    canvas = _shade_and_grid(_cover(as_image(photo).convert("RGB"), photo_zoom, photo_x, photo_y))
    if os.path.exists(LEAGUE_LOGO):
        _paste_fit(canvas, Image.open(LEAGUE_LOGO), 57, 79, 111)

    rows = rows[:8]
    x0, y0, panel_h = _card_geometry(len(rows))
    _card(canvas, x0, y0, x0 + CARD_W, CARD_BOTTOM)

    cx = x0 + CARD_W // 2
    for team, dx in ((home_team, -120), (away_team, 120)):
        crest = crest_image(team, teams)
        if crest is not None:
            _paste_fit(canvas, crest, cx + dx, y0 + 90, 118)
    _paste_fit(canvas, logo(), cx, y0 + 92, 124)

    d = ImageDraw.Draw(canvas)
    px0, px1, py0 = x0 + PANEL_X0, x0 + PANEL_X1, y0 + PANEL_TOP
    d.rounded_rectangle((px0, py0, px1, py0 + panel_h), 10, outline=(150, 165, 192), width=2)

    f_val = font("Montserrat-Bold.ttf", 21)
    bx0, bx1 = px0 + BAR_PAD, px1 - BAR_PAD
    for i, row in enumerate(rows):
        ty = py0 + ROW_FIRST + i * ROW_PITCH
        home, away = str(row.get("home", "")), str(row.get("away", ""))
        d.text((bx0, ty), home, font=f_val, fill="white", anchor="lm")
        d.text((bx1, ty), away, font=f_val, fill="white", anchor="rm")
        side = max(d.textlength(home, font=f_val), d.textlength(away, font=f_val)) + 16
        label, f_label = fit_text(d, str(row.get("label", "")), "Montserrat-Medium.ttf", 20,
                                  (bx1 - bx0) - 2 * side, sp=1.2, min_size=16)
        spaced(d, ((bx0 + bx1) / 2 - spaced_len(d, label, f_label, 1.2) / 2, ty), label, f_label, "white", 1.2)

        h, a = max(_number(home), 0), max(_number(away), 0)
        share = h / (h + a) if h + a > 0 else 0.5
        split = round(bx0 + (bx1 - bx0) * share)
        by = ty + BAR_OFFSET
        d.rectangle((bx0, by, bx1, by + BAR_H - 1), fill=away_rgb)
        if split > bx0:
            d.rectangle((bx0, by, split - 1, by + BAR_H - 1), fill=home_rgb)

    tagline(canvas, 1307, 27, 2.6)
    if show_guides:
        guides(canvas, guide_boxes({"rows": rows}))
    return canvas.convert("RGB")


TEMPLATE = Template(
    key="t3",
    name="Match stats",
    order=30,
    category="Match",
    description="Home vs away stats as bars, over a match photo.",
    render=render_match_stats,
    filename=lambda v: f"{slug(v['home_team'])}_vs_{slug(v['away_team'])}_stats",
    fields=[
        Row(Team("home_team", "Home team", "RAJA CA"),
            Team("away_team", "Away team", "HUS AGADIR")),
        Table(
            "rows", "Stats (up to 8 rows, in order)",
            columns=[
                Column("label", "Stat"),
                Column("home", "Home", help="Printed as typed, e.g. 61% or 12. The bar uses the number in it."),
                Column("away", "Away", help="Printed as typed, e.g. 39% or 8. The bar uses the number in it."),
            ],
            default_rows=[
                {"label": "Goals", "home": "1", "away": "1"},
                {"label": "Possession", "home": "61%", "away": "39%"},
                {"label": "Goal attempts", "home": "12", "away": "8"},
                {"label": "Shots on target", "home": "3", "away": "3"},
                {"label": "Shots off target", "home": "7", "away": "3"},
                {"label": "Corners", "home": "5", "away": "2"},
            ],
            required=["label", "home", "away"],
            max_rows=8,
        ),
        Row(Color("home_color", "Home bar color", help="Off = the home team's color from teams.json"),
            Color("away_color", "Away bar color", "#FFFFFF")),
        Photo(
            "photo", "Match photo (background)", title="Background photo",
            placement=PLACEMENT, guides=guide_boxes,
            guides_help="Pink boxes = stats card, league logo and tagline. Keep faces out of them.",
            zoom=(0.5, 3.0, 1.0, 0.01), x=(-800, 800, 0, 1), y=(-800, 800, 0, 1),
        ),
    ],
)
