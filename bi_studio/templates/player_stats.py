"""Player stats: one player's numbers in a match, with the photo on the right, score and rating."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from PIL import Image, ImageColor, ImageDraw

from ..brand import NAVY, W, H, background, crest_image, font, load_teams, logo
from ..fields import Color, Column, Photo, Placement, Row, Table, Team, Template, Text
from ..primitives import as_image, blend_photo, fit_text, guides, slug, spaced, spaced_len, tagline

# photo is as tall as the post at zoom 1, its center at x = 760 (the text column is on the left)
PLACEMENT = Placement(height=H, anchor=(760, 0), pivot=(0.5, 0))
TEXT_X, TEXT_MAX_X = 90, 700          # name / title column
VALUE_RIGHT, LABEL_GAP = 119, 17      # stat values are right-aligned; labels follow
KPI_BASELINE, KPI_PITCH = 665, 44.0   # first stat row baseline, distance between rows
MAX_KPIS = 10
GOLD = "#DFC448"  # default title color
RED = "#C4313C"   # default stat value color
SCORE_Y = 1173                        # center line of the crests + score row
RATING_TOP, RATING_H, RATING_RIGHT = 1201, 40, 1045

# Sofascore-style rating colors (approximate), highest threshold first
RATING_COLORS = [(9.0, (55, 77, 245)), (8.0, (16, 170, 211)), (7.0, (0, 196, 36)),
                 (6.5, (217, 175, 0)), (6.0, (237, 126, 7)), (0.0, (220, 12, 0))]


def guide_boxes(values: dict | None = None) -> list[tuple[int, int, int, int]]:
    """Areas to keep the player's face out of: logo, name + stats, score row, rating, tagline."""
    n = len((values or {}).get("kpis") or []) or 9
    kpi_bottom = int(KPI_BASELINE + (min(n, MAX_KPIS) - 1) * KPI_PITCH + 12)
    return [(480, 40, 600, 185), (60, 385, TEXT_MAX_X, kpi_bottom), (70, 1105, 470, 1240),
            (740, 1190, 1060, 1252), (130, 1292, 950, 1340)]


def rating_color(rating: str):
    """Badge color for a rating like "8.7"; None if it isn't a number."""
    try:
        value = float(str(rating).replace(",", "."))
    except ValueError:
        return None
    return next(color for threshold, color in RATING_COLORS if value >= threshold)


@lru_cache(maxsize=1)
def _photo_fade() -> Image.Image:
    """Photo opacity across the post: hidden behind the text column, full on the right."""
    t = np.clip((np.arange(W) - 260) / (640 - 260), 0, 1)
    row = (t * t * (3 - 2 * t) * 255).astype(np.uint8)
    return Image.fromarray(np.repeat(row[None, :], H, 0))


@lru_cache(maxsize=1)
def _shade():
    """Darker left side (text readability) and bottom (score + tagline), as out = img * keep + add."""
    xs = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    tl = np.clip(xs / 0.62, 0, 1)
    a_left = (1 - tl * tl * (3 - 2 * tl)) * 0.55
    a_bot = np.clip((ys - 0.80) / 0.20, 0, 1) ** 1.5 * 0.6
    a_top = np.clip((0.12 - ys) / 0.12, 0, 1) * 0.3
    alpha = (1 - (1 - a_left) * (1 - a_bot) * (1 - a_top))[..., None]
    return (1 - alpha).astype(np.float32), (np.array(NAVY, np.float32) * alpha).astype(np.float32)


def _paste_fit(canvas, img, cx, cy, box):
    """Paste img scaled to fit a box x box square, centered on (cx, cy)."""
    img = img.convert("RGBA")
    img = img.crop(img.getbbox())
    s = box / max(img.size)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    canvas.alpha_composite(img, (round(cx - img.width / 2), round(cy - img.height / 2)))


def render_player_stats(
    first_name: str,
    last_name: str,
    title: str,
    kpis: list[dict],
    home_team: str,
    away_team: str,
    home_score: str,
    away_score: str,
    photo,
    photo_zoom: float = 1.0,
    photo_x: int = 0,
    photo_y: int = 0,
    rating: str = "",
    rating_label: str = "Sofascore Rating",
    rating_color_override=None,
    title_color: str = GOLD,
    value_color: str = RED,
    show_guides: bool = False,
) -> Image.Image:
    """Player stats post.

    kpis: up to 10 dicts {"value": "0.75", "label": "Expected assists (xA)"}; both printed as typed.
    title_color / value_color: "#RRGGBB" for the title and the stat values.
    rating: e.g. "8.7"; empty hides the badge. Its color follows the rating (Sofascore-style scale)
            unless rating_color_override ("#RRGGBB") is given.
    photo_zoom: 1.0 = photo as tall as the post; photo_x / photo_y: shift in pixels (+ = right / down).
    """
    teams = load_teams()
    canvas = background().copy()
    photo = as_image(photo).convert("RGB")
    canvas = blend_photo(canvas, photo, PLACEMENT.box(photo.width, photo.height, photo_zoom, photo_x, photo_y),
                         fade=_photo_fade())
    keep, add = _shade()
    canvas = Image.fromarray((np.asarray(canvas, dtype=np.float32) * keep + add).clip(0, 255).astype(np.uint8))
    canvas = canvas.convert("RGBA")
    d = ImageDraw.Draw(canvas)

    canvas.alpha_composite(logo(), (W // 2 - logo().width // 2 + 1, 48))

    # name + title (fit the column; long names shrink)
    max_w = TEXT_MAX_X - TEXT_X
    first, f_first = fit_text(d, first_name.upper().strip(), "Montserrat-Regular.ttf", 60, max_w)
    d.text((TEXT_X, 439), first, font=f_first, fill="white", anchor="ls")
    last, f_last = fit_text(d, last_name.upper().strip(), "Montserrat-ExtraBold.ttf", 76, max_w, min_size=44)
    d.text((TEXT_X, 511), last, font=f_last, fill="white", anchor="ls")
    head, f_head = fit_text(d, title.upper().strip(), "Montserrat-ExtraBoldItalic.ttf", 46, max_w)
    d.text((TEXT_X, 577), head, font=f_head, fill=ImageColor.getrgb(title_color or GOLD)[:3], anchor="ls")

    # stats: red values right-aligned on one column, labels after them
    kpis = kpis[:MAX_KPIS]
    value_rgb = ImageColor.getrgb(value_color or RED)[:3]
    f_val = font("Montserrat-ExtraBold.ttf", 30)
    widest = max((d.textlength(str(k.get("value", "")), font=f_val) for k in kpis), default=0)
    value_right = max(VALUE_RIGHT, round(46 + widest))
    label_x = value_right + LABEL_GAP
    for i, k in enumerate(kpis):
        y = round(KPI_BASELINE + i * KPI_PITCH)
        d.text((value_right, y), str(k.get("value", "")), font=f_val, fill=value_rgb, anchor="rs")
        label, f_label = fit_text(d, str(k.get("label", "")), "Montserrat-Medium.ttf", 30, 690 - label_x, sp=2.0)
        spaced(d, (label_x, y), label, f_label, "white", 2.0, anchor="ls")

    # crests + score
    score = f"{str(home_score).strip()} - {str(away_score).strip()}"
    f_score = font("Montserrat-Bold.ttf", 40)
    home_cx = 145
    score_x = home_cx + 59 + 14
    score_w = d.textlength(score, font=f_score)
    home_crest = crest_image(home_team, teams)
    if home_crest is not None:
        _paste_fit(canvas, home_crest, home_cx, SCORE_Y, 118)
    d.text((score_x, SCORE_Y + 2), score, font=f_score, fill="white", anchor="lm")
    away_crest = crest_image(away_team, teams)
    if away_crest is not None:
        _paste_fit(canvas, away_crest, score_x + score_w + 12 + 59, SCORE_Y, 118)

    # rating badge: colored number box + dark pill with the label
    if str(rating).strip():
        color = (ImageColor.getrgb(rating_color_override)[:3] if rating_color_override
                 else rating_color(rating) or (16, 170, 211))
        f_num = font("Montserrat-Bold.ttf", 26)
        label, f_lab = fit_text(d, rating_label.strip(), "Montserrat-Medium.ttf", 24, 380)
        lab_w = d.textlength(label, font=f_lab)
        box_w = max(60, round(d.textlength(str(rating).strip(), font=f_num) + 24))
        x_box = RATING_RIGHT - (lab_w + 32) - box_w
        y0r, y1r = RATING_TOP, RATING_TOP + RATING_H
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((x_box + box_w - 12, y0r, RATING_RIGHT, y1r), 10, fill=(19, 23, 15, 225))
        canvas.alpha_composite(pill)
        d.rounded_rectangle((x_box, y0r, x_box + box_w, y1r), 10, fill=color)
        d.text((x_box + box_w / 2, (y0r + y1r) / 2 + 1), str(rating).strip(), font=f_num, fill="white", anchor="mm")
        d.text((x_box + box_w + 14, (y0r + y1r) / 2 + 1), label, font=f_lab, fill="white", anchor="lm")

    tagline(canvas, 1311, 26, 2.6)
    if show_guides:
        guides(canvas, guide_boxes({"kpis": kpis}))
    return canvas.convert("RGB")


TEMPLATE = Template(
    key="t4",
    name="Player stats",
    order=40,
    category="Match",
    description="A player's numbers in a match, with score and rating.",
    render=render_player_stats,
    filename=lambda v: f"{slug(v['first_name'] + ' ' + v['last_name'])}_stats",
    fields=[
        Row(Text("first_name", "First name", "YAHYA"),
            Text("last_name", "Last name", "ATTIATALLAH")),
        Text("title", "Title", "PLAYER BY NUMBERS"),
        Row(Color("title_color", "Title color", GOLD),
            Color("value_color", "Stat numbers color", RED)),
        Table(
            "kpis", f"Stats (up to {MAX_KPIS} rows, in order)",
            columns=[
                Column("value", "Value", help="Printed as typed, e.g. 0.75, 85, 7 (5)"),
                Column("label", "Stat", help="e.g. Expected assists (xA)"),
            ],
            default_rows=[
                {"value": "1", "label": "Assists"},
                {"value": "0.75", "label": "Expected assists (xA)"},
                {"value": "5", "label": "Def. contributions"},
                {"value": "1", "label": "Big chances created"},
                {"value": "85", "label": "Accurate passes %"},
                {"value": "50", "label": "Acc. Long balls %"},
                {"value": "7 (5)", "label": "Ground duels (won)"},
                {"value": "4", "label": "Recoveries"},
                {"value": "4 (3)", "label": "Crosses (accurate)"},
            ],
            required=["value", "label"],
            max_rows=MAX_KPIS,
        ),
        Row(Team("home_team", "Home team", "DH EL JADIDI"),
            Team("away_team", "Away team", "WYDAD AC")),
        Row(Text("home_score", "Home score", "0"),
            Text("away_score", "Away score", "2")),
        Row(Text("rating", "Rating", "8.7", help="Empty = no rating badge"),
            Text("rating_label", "Rating label", "Sofascore Rating")),
        Color("rating_color_override", "Rating color",
              help="Off = color follows the rating (Sofascore-style scale)"),
        Photo(
            "photo", "Player photo", title="Player photo",
            placement=PLACEMENT, guides=guide_boxes,
            guides_help="Pink boxes = logo, name and stats, score, rating and tagline. Keep the face out of them.",
            zoom=(0.5, 3.0, 1.0, 0.01), x=(-800, 800, 0, 1), y=(-800, 600, 0, 1),
        ),
    ],
)
