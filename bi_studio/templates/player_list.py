"""Player list: top 10 players for one stat, list on the left, photo on the right."""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from ..brand import ASSETS, NAVY, W, H, background, crest_image, font, load_teams, logo
from ..fields import Column, Photo, Placement, Row, Table, Template, Text
from ..primitives import as_image, blend_photo, draw_condensed, fit_text, guides, slug, spaced, tagline

# optional logos, drawn when the files exist
LEAGUE_LOGO = os.path.join(ASSETS, "league_logo.png")    # top-right
PARTNER_LOGO = os.path.join(ASSETS, "partner_logo.png")  # bottom-right, next to the Botola Insights logo

# photo is as tall as the post at zoom 1, its center at x = 900 (right of the list panel)
PLACEMENT = Placement(height=H, anchor=(900, 0), pivot=(0.5, 0))
PANEL_RIGHT = 715                     # the list panel's right edge; the photo shows to its right
PANEL_TOP_X, PANEL_CUT_Y = 642, 128   # top-right corner is cut diagonally: from (642, 0) down to (715, 128)
TEXT_X = 62
CREST_X, CREST_BOX = 368, 74          # team column center, crest size
VALUE_RIGHT = 700
ROW0_TOP, ROW_PITCH = 283, 96.75      # cap top of the first row's first name, distance between rows
MAX_ROWS = 10
HIGHLIGHT = ((6, 84, 186), (12, 106, 210))   # row 1 band: left / right color
SOFT = (215, 222, 235)                       # subtitle and footnote
CONDENSE, VALUE_CONDENSE = 0.86, 0.9        # Bebas Neue squeezed to match the design's narrower letters


def _row_top(i: int) -> int:
    return round(ROW0_TOP + i * ROW_PITCH)


def guide_boxes(values: dict | None = None) -> list[tuple[int, int, int, int]]:
    """Areas to keep the player's face out of: the list panel, logos, footnote and tagline."""
    n = min(len((values or {}).get("players") or []) or MAX_ROWS, MAX_ROWS)
    return [(0, 30, PANEL_RIGHT, _row_top(n - 1) + 85), (PANEL_RIGHT, 271, 755, 366),
            (995, 15, 1075, 115), (915, 1228, 1075, 1320), (40, 1250, 960, 1340)]


@lru_cache(maxsize=1)
def _panel_background() -> Image.Image:
    """Brand background with a larger copy of its ball outline behind the title and list (as in the design)."""
    bg = background().copy()
    ball = bg.crop((730, 0, 1080, 560))
    ball = ball.resize((round(ball.width * 1.3), round(ball.height * 1.3)), Image.LANCZOS)
    layer = Image.new("RGB", bg.size, (0, 0, 0))
    layer.paste(ball, (270, -140))
    return ImageChops.lighter(bg, layer)


@lru_cache(maxsize=1)
def _photo_mask() -> Image.Image:
    """The photo only shows right of the list panel (whose top-right corner is cut diagonally)."""
    k = 4  # draw 4x larger and shrink, so the diagonal edge is smooth
    mask = Image.new("L", (W * k, H * k), 0)
    ImageDraw.Draw(mask).polygon([(PANEL_TOP_X * k, 0), (W * k, 0), (W * k, H * k), (PANEL_RIGHT * k, H * k),
                                  (PANEL_RIGHT * k, PANEL_CUT_Y * k)], fill=255)
    return mask.resize((W, H), Image.LANCZOS)


@lru_cache(maxsize=1)
def _shade():
    """Darker bottom (logos + tagline), as out = img * keep + add. The list panel is not darkened:
    the background texture shows through, as in the design."""
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a_bot = np.clip((ys - 0.85) / 0.15, 0, 1) ** 1.5 * 0.55
    alpha = np.broadcast_to(a_bot, (H, W))[..., None]
    return (1 - alpha).astype(np.float32), (np.array(NAVY, np.float32) * alpha).astype(np.float32)


def _paste_fit(canvas, img, cx, cy, box_w, box_h=None):
    """Paste img scaled to fit box_w x box_h (square if box_h is None), centered on (cx, cy)."""
    img = img.convert("RGBA")
    img = img.crop(img.getbbox())
    s = min(box_w / img.width, (box_h or box_w) / img.height)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    canvas.alpha_composite(img, (round(cx - img.width / 2), round(cy - img.height / 2)))


def _highlight(canvas, cy):
    """Blue band with pointed ends behind the first row (its right tip reaches over the photo)."""
    x0, x1, h_top, h_bot = 13, 751, 47, 48
    shape = [(59, cy - h_top), (705, cy - h_top), (x1, cy), (705, cy + h_bot), (59, cy + h_bot), (x0, cy)]
    t = np.linspace(0, 1, x1 - x0 + 1)[None, :, None]
    grad = (np.array(HIGHLIGHT[0]) * (1 - t) + np.array(HIGHLIGHT[1]) * t).astype(np.uint8)
    band = Image.fromarray(np.repeat(grad, h_top + h_bot + 1, 0), "RGB")
    mask = Image.new("L", band.size, 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - (cy - h_top)) for x, y in shape], fill=255)
    canvas.paste(band, (x0, cy - h_top), mask)


def render_player_list(
    title: str,
    subtitle: str,
    header_player: str,
    header_team: str,
    header_value: str,
    players: list[dict],
    footnote: str,
    photo,
    photo_zoom: float = 1.0,
    photo_x: int = 0,
    photo_y: int = 0,
    show_guides: bool = False,
) -> Image.Image:
    """Top-10 player list.

    players: up to 10 dicts {"first_name": "Othman", "last_name": "Sabri", "team": "WYDAD TEMARA",
             "value": "3.99"}, in order; the first row is highlighted. Values are printed as typed.
    footnote: small line above the tagline (e.g. "* z-value shows ..."); empty hides it.
    photo_zoom: 1.0 = photo as tall as the post; photo_x / photo_y: shift in pixels (+ = right / down).
    """
    teams = load_teams()
    photo = as_image(photo).convert("RGB")
    canvas = blend_photo(_panel_background().copy(), photo,
                         PLACEMENT.box(photo.width, photo.height, photo_zoom, photo_x, photo_y), fade=_photo_mask())
    keep, add = _shade()
    canvas = Image.fromarray((np.asarray(canvas, dtype=np.float32) * keep + add).clip(0, 255).astype(np.uint8))
    canvas = canvas.convert("RGBA")
    d = ImageDraw.Draw(canvas)

    if os.path.exists(LEAGUE_LOGO):
        _paste_fit(canvas, Image.open(LEAGUE_LOGO), 1035, 65, 60, 86)

    # title, subtitle, column headers
    t, f_t = fit_text(d, title.upper().strip(), "BebasNeue-Regular.ttf", 130, (PANEL_RIGHT - 40 - TEXT_X) / CONDENSE,
                      min_size=70)
    draw_condensed(canvas, (TEXT_X + 3, 141), t, f_t, "white", CONDENSE, stroke=1)
    sub, f_sub = fit_text(d, subtitle.upper().strip(), "Montserrat-Regular.ttf", 19, PANEL_RIGHT - 40 - TEXT_X, sp=1)
    spaced(d, (TEXT_X + 2, 168), sub, f_sub, SOFT, 1, anchor="ls")
    f_h = font("Montserrat-Bold.ttf", 16)
    d.text((TEXT_X, 255), header_player.upper().strip(), font=f_h, fill="white", anchor="ls")
    d.text((CREST_X - 4, 255), header_team.upper().strip(), font=f_h, fill="white", anchor="ms")
    d.text((685, 255), header_value.upper().strip(), font=f_h, fill="white", anchor="rs")

    # rows
    players = players[:MAX_ROWS]
    if players:
        _highlight(canvas, _row_top(0) + 35)
    for i, p in enumerate(players):
        top = _row_top(i)
        first, f_first = fit_text(d, str(p.get("first_name") or "").upper().strip(), "Montserrat-Regular.ttf", 23,
                                  CREST_X - CREST_BOX // 2 - 16 - TEXT_X, sp=2)
        spaced(d, (TEXT_X, top + 16), first, f_first, "white", 2, anchor="ls")
        last, f_last = fit_text(d, str(p.get("last_name") or "").upper().strip(), "BebasNeue-Regular.ttf", 67,
                                (CREST_X - CREST_BOX // 2 - 12 - TEXT_X) / CONDENSE, min_size=44)
        draw_condensed(canvas, (TEXT_X, top + 71), last, f_last, "white", CONDENSE, stroke=1)
        crest = crest_image(str(p.get("team") or ""), teams)
        if crest is not None:
            _paste_fit(canvas, crest, CREST_X, top + 35, CREST_BOX)
        value, f_v = fit_text(d, str(p.get("value") or "").strip(), "BebasNeue-Regular.ttf", 80,
                              (VALUE_RIGHT - (CREST_X + CREST_BOX // 2 + 30)) / VALUE_CONDENSE, min_size=48)
        draw_condensed(canvas, (VALUE_RIGHT, top + 71), value, f_v, "white", VALUE_CONDENSE, anchor="rs", stroke=1)

    if footnote.strip():
        note, f_note = fit_text(d, footnote.strip(), "Montserrat-Regular.ttf", 21, 900 - TEXT_X)
        d.text((TEXT_X + 2, 1276), note, font=f_note, fill=SOFT, anchor="ls")

    # bottom-right logos
    mark = logo()
    s = 81 / mark.height
    mark = mark.resize((round(mark.width * s), 81), Image.LANCZOS)
    has_partner = os.path.exists(PARTNER_LOGO)
    canvas.alpha_composite(mark, ((954 if has_partner else 1032) - mark.width // 2, 1234))
    if has_partner:
        _paste_fit(canvas, Image.open(PARTNER_LOGO), 1032, 1275, 70, 54)

    tagline(canvas, 1316, 27, 2.6)
    if show_guides:
        guides(canvas, guide_boxes({"players": players}))
    return canvas.convert("RGB")


TEMPLATE = Template(
    key="t5",
    name="Player list",
    order=50,
    category="Rankings",
    description="Top 10 players on one stat, with a photo and a footnote.",
    render=render_player_list,
    filename=lambda v: f"top10_{slug(v['title'])}",
    fields=[
        Text("title", "Title", "BOX THREAT"),
        Text("subtitle", "Subtitle", "BOTOLA PRO 2026-2027 - ROUND 1"),
        Row(Text("header_player", "Player column header", "PLAYER NAME"),
            Text("header_team", "Team column header", "TEAM"),
            Text("header_value", "Stat column header", "Z-VALUES")),
        Table(
            "players", f"Players (up to {MAX_ROWS} rows, in order; the first row is highlighted)",
            columns=[
                Column("first_name", "First name"),
                Column("last_name", "Last name"),
                Column("team", "Team", kind="team"),
                Column("value", "Value", help="Printed as typed, e.g. 3.99"),
            ],
            default_rows=[
                {"first_name": "Othman", "last_name": "Sabri", "team": "WYDAD TEMARA", "value": "3.99"},
                {"first_name": "Taoufik", "last_name": "Razko", "team": "CODM MEKNES", "value": "3.99"},
                {"first_name": "Salah", "last_name": "Benyachou", "team": "HUS AGADIR", "value": "3.99"},
                {"first_name": "Ayoub", "last_name": "Maamouri", "team": "KAC MARRAKECH", "value": "2.69"},
                {"first_name": "Ayoub", "last_name": "Ajerrar", "team": "UTS RABAT", "value": "2.57"},
                {"first_name": "Tshegofatso", "last_name": "Mabasa", "team": "MAS DE FES", "value": "2.45"},
                {"first_name": "Saleh", "last_name": "Sellami", "team": "KAC MARRAKECH", "value": "2.35"},
                {"first_name": "Achraf", "last_name": "Eddahbi", "team": "RCA ZEMAMRA", "value": "2.30"},
                {"first_name": "Anas", "last_name": "El Mahraoui", "team": "MAS DE FES", "value": "2.19"},
                {"first_name": "Youssef", "last_name": "Zghoudi", "team": "KAC MARRAKECH", "value": "2.07"},
            ],
            required=["last_name", "value"],
            max_rows=MAX_ROWS,
        ),
        Text("footnote", "Footnote (bottom text)", "* z-value shows how far a number is from the average",
             help="Small line above the tagline. Empty = no footnote."),
        Photo(
            "photo", "Player photo", title="Player photo",
            placement=PLACEMENT, guides=guide_boxes,
            guides_help="Pink boxes = list panel, logos, footnote and tagline. The photo only shows right of the list.",
            zoom=(0.5, 3.0, 1.0, 0.01), x=(-800, 800, 0, 1), y=(-800, 600, 0, 1),
        ),
    ],
)
