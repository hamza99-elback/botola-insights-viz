"""Player top 5: player leaderboard with the leader's photo on the right."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ..brand import NAVY, W, H, crest_image, font, load_teams, logo
from ..fields import Column, Photo, Placement, Row, Table, Template, Text
from ..primitives import as_image, fit_text, guides, slug, tagline

# photo is 1430 px tall at zoom 1, with the point 56% across its width at x = 790
PLACEMENT = Placement(height=1430, anchor=(790, -30), pivot=(0.56, 0))
X0, X1, TOP, RH = 54, 511, 193, 80  # list column and rows


def guide_boxes(values: dict | None = None) -> list[tuple[int, int, int, int]]:
    """Areas the photo should stay clear of: the list and the logo / tagline."""
    return [(X0, 150, X1, TOP + 5 * (RH + 2)), (300, 1170, 780, H)]


@lru_cache(maxsize=1)
def _fade():
    """Navy fade from the left, bottom and top (same for every post): (keep, navy) factors."""
    xs = np.linspace(0, 1, W)[None, :]
    ys = np.linspace(0, 1, H)[:, None]
    tl = np.clip(xs / 0.80, 0, 1)
    a_left = (1 - tl * tl * (3 - 2 * tl)) * 0.94
    a_bot = np.clip((ys - 0.80) / 0.20, 0, 1) ** 1.5 * 0.85
    a_top = np.clip((0.10 - ys) / 0.10, 0, 1) * 0.35
    alpha = 1 - (1 - a_left) * (1 - a_bot) * (1 - a_top)
    return 1 - alpha[..., None], np.array(NAVY, np.float32) * alpha[..., None]


@lru_cache(maxsize=1)
def _lines() -> Image.Image:
    """Decorative circles and line (same for every post)."""
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    for cx, cy, r in [(-60, 60, 260), (-60, 60, 330), (120, -140, 300)]:
        ld.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(40, 90, 170, 60), width=3)
    ld.line((0, 1150, 160, 1290), fill=(40, 90, 170, 70), width=3)
    return lines.filter(ImageFilter.GaussianBlur(1.2))


def render_top5(
    header_left: str,
    header_right: str,
    rows: list[dict],
    photo,
    photo_zoom: float = 1.0,
    photo_x: int = 0,
    photo_y: int = 0,
    show_guides: bool = False,
) -> Image.Image:
    """Player leaderboard with the leader's photo on the right.

    rows: up to 5 dicts {"name": "S. Ganvoula", "value": "5.0", "team": "WYDAD AC"}
          (or "crest": PIL image / path instead of "team").
    photo_zoom: 1.0 = default size; photo_x / photo_y: shift in pixels (+ = right / down).
    """
    teams = load_teams()
    photo = as_image(photo).convert("RGB")
    ox, oy, pw, PH = PLACEMENT.box(photo.width, photo.height, photo_zoom, photo_x, photo_y)
    photo = photo.resize((pw, PH), Image.LANCZOS)

    canvas = Image.new("RGB", (W, H), NAVY)
    if ox > 0:  # mirror the photo's edge into the gap, then blur the seam (no hard line)
        canvas.paste(photo.crop((0, 0, min(ox, pw), PH)).transpose(Image.FLIP_LEFT_RIGHT), (0, oy))
    canvas.paste(photo, (ox, oy))
    if ox > 0:  # blur only the strip the seam fade touches (+ the blur's reach: same pixels, faster)
        strip = min(W, ox + 120 + 3 * 28 + 12)
        region = canvas.crop((0, 0, strip, H))
        m = np.clip(1 - (np.arange(strip)[None, :].repeat(H, 0) - ox) / 120.0, 0, 1)
        mask = Image.fromarray((m * 255).astype(np.uint8))
        canvas.paste(Image.composite(region.filter(ImageFilter.GaussianBlur(28)), region, mask), (0, 0))

    keep, navy = _fade()
    arr = np.asarray(canvas).astype(np.float32) * 0.88 + np.array(NAVY, np.float32) * 0.12
    arr = arr * keep + navy
    canvas = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    canvas = Image.alpha_composite(canvas, _lines())

    d = ImageDraw.Draw(canvas)
    hl, f_hl = fit_text(d, header_left.upper(), "Montserrat-Regular.ttf", 21, 200)
    d.text((64, 167), hl, font=f_hl, fill="white", anchor="lm")
    hr, f_hr = fit_text(d, header_right.upper(), "Montserrat-Bold.ttf", 22, X1 - 64 - d.textlength(hl, font=f_hl) - 24)
    d.text((X1, 166), hr, font=f_hr, fill="white", anchor="rm")
    f_val = font("Montserrat-ExtraBold.ttf", 44)
    rows = rows[:5]
    top, rh = TOP, RH
    for i, row in enumerate(rows):
        y = top + i * (rh + 2)
        cy = y + rh // 2
        if i == 0:
            g = np.zeros((rh, X1 - X0, 4), np.uint8)
            t = np.linspace(0, 1, X1 - X0)[None, :, None] ** 1.6
            g[..., :3] = (np.array([2, 104, 225]) * (1 - t) + np.array([6, 62, 140]) * t).astype(np.uint8)
            g[..., 3] = 255
            mask = Image.new("L", (X1 - X0, rh), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, X1 - X0 - 1, rh - 1), 7, fill=255)
            canvas.paste(Image.fromarray(g, "RGBA"), (X0, y), mask)
        if i < len(rows) - 1:
            d.line((X0, y + rh + 1, X1, y + rh + 1), fill=(182, 190, 213), width=3)
        c = as_image(row.get("crest")) or crest_image(row.get("team", ""), teams)
        if c is not None:
            c = c.convert("RGBA")
            c = c.crop(c.getbbox())
            s = 58 / max(c.size)
            c = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
            canvas.alpha_composite(c, (89 - c.width // 2, cy - c.height // 2))
        value = str(row["value"])
        name, f_name = fit_text(d, str(row["name"]).upper(), "Montserrat-Bold.ttf", 32,
                                497 - d.textlength(value, font=f_val) - 20 - 124)
        d.text((124, cy + 2), name, font=f_name, fill="white", anchor="lm")
        d.text((497, cy - 2), value, font=f_val, fill="white", anchor="rm")

    canvas.alpha_composite(logo(), (W // 2 - logo().width // 2 - 1, 1176))
    tagline(canvas, 1325, 23, 2.4)
    if show_guides:
        guides(canvas, guide_boxes())
    return canvas.convert("RGB")


TEMPLATE = Template(
    key="t1",
    name="Player top 5",
    order=20,
    category="Rankings",
    description="Top 5 players on one stat, with the leader's photo.",
    render=render_top5,
    filename=lambda v: f"top5_{slug(v['header_right'])}",
    fields=[
        Row(Text("header_left", "Left label", "UP TO GW04"),
            Text("header_right", "Stat name", "SHOTS PER MATCH")),
        Table(
            "rows", "Top 5 players (in order)",
            columns=[
                Column("name", "Player", help="Initial. Surname"),
                Column("team", "Team", kind="team"),
                Column("value", "Value"),
            ],
            default_rows=[
                {"name": "S. Ganvoula", "team": "WYDAD AC", "value": "5.0"},
                {"name": "T. Mabasa", "team": "MAS DE FES", "value": "4.3"},
                {"name": "A. Maamouri", "team": "KAC MARRAKECH", "value": "3.5"},
                {"name": "Y. El Fahli", "team": "AS FAR", "value": "3.0"},
                {"name": "A. Ennakouss", "team": "DH EL JADIDI", "value": "3.0"},
            ],
            required=["name", "value"],
            max_rows=5,
        ),
        Photo(
            "photo", "Photo of the #1 player", title="Leader photo",
            placement=PLACEMENT, guides=guide_boxes,
            guides_help="Pink boxes = list and logo areas. Keep the player's face and body out of them.",
        ),
    ],
)
