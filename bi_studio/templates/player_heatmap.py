"""Player heatmap: a player's heatmap and key stats (one match or a season) in a card over the photo."""
from __future__ import annotations

import io
import random

import matplotlib

matplotlib.use("Agg")  # no display on the server

import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import VerticalPitch
from PIL import Image, ImageColor, ImageDraw

from charts.heatmap import Heatmap

from ..brand import NAVY, W, H, background, font, logo
from ..fields import Color, Column, Data, Photo, Placement, Table, Template, Text
from ..primitives import as_image, blend_photo, fit_text, guides, photo_backdrop, shade_and_grid, slug, tagline

PLACEMENT = Placement()                    # zoom 1.0 = photo covers the post, centered
CARD = (34, 538, 680, 1242)                # dark card: title + panel
PANEL = (54, 636, 658, 1205)               # panel with the theme-color border
PITCH = (65, 670, 392, 1172)               # heatmap pitch (vertical, attacking upwards)
KPI_X, KPI_TOP, KPI_PITCH = 402, 700, 52.4  # stat labels column, first label's cap top, row distance
MAX_KPIS = 9
THEME = "#0FC94E"


def guide_boxes(values: dict | None = None) -> list[tuple[int, int, int, int]]:
    """Areas to keep the player's face out of: the card, the logo and the tagline."""
    return [CARD, (30, 20, 125, 145), (230, 1295, 850, 1332)]


def sample_heatmap() -> list[dict]:
    """Made-up touches of a central midfielder (catalog thumbnail only)."""
    rng = random.Random(7)
    centers = [(50, 48, 30), (42, 56, 25), (60, 40, 18), (32, 50, 15), (68, 62, 14), (55, 28, 12), (22, 44, 10)]
    return [{"x": min(99, max(1, rng.gauss(cx, 7))), "y": min(99, max(1, rng.gauss(cy, 8)))}
            for cx, cy, n in centers for _ in range(n)]


def _usable_points(points) -> pd.DataFrame:
    """The points that have numeric x and y, as a DataFrame with columns x, y."""
    rows = [p for p in points or [] if isinstance(p, dict)]
    df = pd.DataFrame(rows, columns=["x", "y"]).apply(pd.to_numeric, errors="coerce").dropna()
    return df


def check_heatmap(points: list) -> str | None:
    """Error message for the form if no point has numeric x and y."""
    if _usable_points(points).empty:
        return 'No usable points: each item needs numeric "x" and "y", like {"x": 52.1, "y": 40.3}.'
    return None


def _heatmap_image(points: list[dict], color: str, size: tuple[int, int]) -> Image.Image:
    """Transparent heatmap on a vertical pitch with white lines, drawn by charts.heatmap.Heatmap.

    points: Sofascore-style {"x", "y"} (0-100): x along the pitch (0 = own goal), y across it.
    """
    df = _usable_points(points)
    if df.empty:  # nothing to draw: pitch lines only
        df = pd.DataFrame({"x": [-50.0], "y": [-50.0]})  # one point off the pitch keeps the heatmap empty
    r, g, b = ImageColor.getrgb(color)[:3]
    c = (r / 255, g / 255, b / 255)
    light = tuple(min(1.0, v + (1 - v) * 0.45) for v in c)
    w, h = size
    hm = Heatmap(pitch=VerticalPitch, data=df, pitch_color="none", figsize=(2 * w / 100, 2 * h / 100))
    fig, _ = hm.draw(color_palette=[(*c, 0.0), (*c, 0.7), (*c, 1.0), (*light, 1.0)], line_color="white", alpha=None)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, transparent=True, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return Image.open(buf).convert("RGBA").resize(size, Image.LANCZOS)


def _card(canvas: Image.Image):
    """Dark rounded card, with a faint touch of the brand background texture."""
    x0, y0, x1, y1 = CARD
    tint = Image.blend(Image.new("RGB", (W, H), (5, 14, 34)), background(), 0.22).crop(CARD).convert("RGBA")
    tint.putalpha(240)
    mask = Image.new("L", tint.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), 14, fill=255)
    canvas.paste(tint, (x0, y0), mask)
    ImageDraw.Draw(canvas).rounded_rectangle(CARD, 14, outline=(40, 58, 92), width=1)


def render_player_heatmap(
    title: str,
    subtitle: str,
    heatmap: list[dict],
    kpis: list[dict],
    photo,
    photo_zoom: float = 1.0,
    photo_x: int = 0,
    photo_y: int = 0,
    theme_color: str = THEME,
    show_guides: bool = False,
) -> Image.Image:
    """Player heatmap post.

    heatmap: Sofascore heatmap points [{"x": .., "y": ..}, ...] (0-100).
    kpis: up to 9 dicts {"label": "Touches", "value": "58"}, printed as typed.
    theme_color: "#RRGGBB" for the heatmap, the panel border and the stat labels.
    """
    theme = ImageColor.getrgb(theme_color or THEME)[:3]
    photo = as_image(photo).convert("RGB")
    box = PLACEMENT.box(photo.width, photo.height, photo_zoom, photo_x, photo_y)
    left, top, pw, ph = box
    base = (Image.new("RGB", (W, H)) if left <= 0 and top <= 0 and left + pw >= W and top + ph >= H
            else photo_backdrop(photo, (W, H)))
    canvas = shade_and_grid(blend_photo(base, photo, box))
    d = ImageDraw.Draw(canvas)

    mark = logo()
    s = 105 / mark.height
    canvas.alpha_composite(mark.resize((round(mark.width * s), 105), Image.LANCZOS), (39, 30))

    _card(canvas)
    t, f_t = fit_text(d, title.upper().strip(), "BebasNeue-Regular.ttf", 46, CARD[2] - 30 - 61, min_size=30)
    d.text((61, 592), t, font=f_t, fill="white", anchor="ls", stroke_width=1, stroke_fill="white")
    sub, f_sub = fit_text(d, subtitle.upper().strip(), "Montserrat-Regular.ttf", 22, CARD[2] - 30 - 61)
    d.text((61, 619), sub, font=f_sub, fill=(225, 230, 240), anchor="ls")

    d.rounded_rectangle(PANEL, 8, outline=theme, width=2)
    pw_, ph_ = PITCH[2] - PITCH[0], PITCH[3] - PITCH[1]
    canvas.alpha_composite(_heatmap_image(heatmap, theme_color or THEME, (pw_, ph_)), PITCH[:2])
    for i in range(4):  # attacking direction: upwards
        cy = 1012 + i * 24
        d.line((363, cy + 8, 370, cy, 377, cy + 8), fill="white", width=2, joint="curve")

    f_val = font("Montserrat-Bold.ttf", 24)
    for i, k in enumerate(kpis[:MAX_KPIS]):
        top = round(KPI_TOP + i * KPI_PITCH)
        label, f_label = fit_text(d, str(k.get("label", "")).strip(), "Montserrat-Regular.ttf", 16,
                                  PANEL[2] - 12 - KPI_X, min_size=12)
        d.text((KPI_X, top + 11), label, font=f_label, fill=theme, anchor="ls")
        value, f_v = fit_text(d, str(k.get("value", "")).strip(), "Montserrat-Bold.ttf", 24, PANEL[2] - 12 - KPI_X)
        d.text((KPI_X, top + 39), value, font=f_v, fill="white", anchor="ls")

    tagline(canvas, 1315, 22, 2.2)
    if show_guides:
        guides(canvas, guide_boxes())
    return canvas.convert("RGB")


TEMPLATE = Template(
    key="t6",
    name="Player heatmap",
    order=60,
    category="Players",
    description="A player's heatmap and key stats, for a match or a season.",
    render=render_player_heatmap,
    filename=lambda v: f"{slug(v['title'])}_heatmap",
    fields=[
        Text("title", "Title", "A. MICHAEL", help="Usually the player's name"),
        Text("subtitle", "Subtitle", "VS RCAZ | BOTOLA PRO 26/27", help="e.g. the opponent and competition, or the season"),
        Color("theme_color", "Theme color", THEME, help="Heatmap, panel border and stat labels"),
        Data("heatmap", "Heatmap data", keys=("heatmap", "points"), sample=sample_heatmap, validate=check_heatmap,
             help='Sofascore heatmap JSON: {"heatmap": [{"x": .., "y": ..}, ...]} (same as Charts > Heatmap)'),
        Table(
            "kpis", f"Stats (up to {MAX_KPIS} rows, in order)",
            columns=[Column("label", "Stat"), Column("value", "Value", help="Printed as typed, e.g. 90% or 7(6)")],
            default_rows=[
                {"label": "Touches", "value": "58"},
                {"label": "Accurate passes", "value": "90%"},
                {"label": "Passes in opposition half (acc.)", "value": "77%"},
                {"label": "Passes in own half (acc.)", "value": "94%"},
                {"label": "Dribbles (successful)", "value": "1(1)"},
                {"label": "Def. contributions", "value": "7"},
                {"label": "Clearances", "value": "5"},
                {"label": "Aerial duels (won)", "value": "7(7)"},
                {"label": "Ground duels (won)", "value": "7(6)"},
            ],
            required=["label", "value"],
            max_rows=MAX_KPIS,
        ),
        Photo(
            "photo", "Player photo", title="Player photo",
            placement=PLACEMENT, guides=guide_boxes,
            guides_help="Pink boxes = stats card, logo and tagline. Keep the player's face out of them.",
            zoom=(0.5, 3.0, 1.0, 0.01), x=(-800, 800, 0, 1), y=(-800, 800, 0, 1),
        ),
    ],
)
