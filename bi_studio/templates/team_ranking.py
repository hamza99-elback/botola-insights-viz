"""Team ranking: up to 6 clubs with clipped crest badges."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from ..brand import CYAN, W, H, crest_image, font, load_teams, logo
from ..brand import background as default_background
from ..fields import Column, Row, Table, Template, Text
from ..primitives import as_image, blur_composite, fit_text, num, slug, spaced, spaced_len, tagline


def render_team_ranking(
    title_white: str,
    title_blue: str,
    rows: list[dict],
    subtitle: str = "BOTOLA PRO 2026-27",
    background=None,
) -> Image.Image:
    """Team ranking with clipped crest badges.

    rows: up to 6 dicts {"team": "AS FAR", "value": "58.9%"} plus optional overrides
          "name" (printed name), "color" [r,g,b], "crest_zoom", "crest_focus_y", "crest" (image).
    """
    teams = load_teams()
    bg = as_image(background)
    canvas = (bg.convert("RGB").resize((W, H), Image.LANCZOS) if bg else default_background().copy()).convert("RGBA")
    d = ImageDraw.Draw(canvas)

    mark = logo()
    s = 124 / mark.height
    mark = mark.resize((round(mark.width * s), 124), Image.LANCZOS)
    canvas.alpha_composite(mark, (W // 2 - mark.width // 2, 28))

    w1, w2 = title_white.upper().strip(), title_blue.upper().strip()
    SP, gap, ty, wing = 4, 22, 240, 30 + 68
    # one font size for both words, shrunk until title + side lines fit the post
    for size in range(96, 59, -2):
        f_title = font("BebasNeue-Regular.ttf", size)
        L1 = spaced_len(d, w1, f_title, SP) if w1 else 0
        L2 = spaced_len(d, w2, f_title, SP) if w2 else 0
        total = L1 + L2 + (gap if w1 and w2 else 0)
        if total + 2 * wing <= W - 60:
            break
    x = W / 2 - total / 2
    if w1:
        x = spaced(d, (x, ty), w1, f_title, "white", SP, stroke=2) + gap
    if w2:
        spaced(d, (x, ty), w2, f_title, CYAN, SP, stroke=2)
    lx0, lx1 = W / 2 - total / 2 - 30, W / 2 + total / 2 + 30
    d.line((lx0 - 68, ty + 3, lx0, ty + 3), fill=CYAN, width=4)
    d.line((lx1, ty + 3, lx1 + 68, ty + 3), fill=CYAN, width=4)

    sub, f_sub = fit_text(d, subtitle.upper(), "Montserrat-Medium.ttf", 36, W - 80, sp=2.5)
    spaced(d, (W / 2 - spaced_len(d, sub, f_sub, 2.5) / 2, 305), sub, f_sub, "white", 2.5)

    f_rank = font("Montserrat-ExtraBoldItalic.ttf", 52)
    f_val = font("Montserrat-Bold.ttf", 40)
    rows = rows[:6]
    BX0, BX1, BH = 225, 988, 84
    CX0, CX1 = 205, 350
    for i, row in enumerate(rows):
        info = teams.get(row.get("team", ""), {})
        cy = int(497 + i * 124.6)
        acc = tuple(row.get("color") or info.get("color", [230, 60, 60]))

        sh = Image.new("RGBA", (BX1 - BX0 + 1, BH + 3), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((0, 0, BX1 - BX0, BH + 2), 12, fill=(0, 0, 0, 120))
        blur_composite(canvas, sh, (BX0, cy - BH // 2 + 6), 8)
        d.rounded_rectangle((BX0, cy - BH // 2, BX1, cy + BH // 2), 12, fill=acc)  # accent edge
        g = np.zeros((BH, BX1 - BX0, 4), np.uint8)
        tt = np.linspace(0, 1, BH)[:, None, None]
        g[..., :3] = (np.array([1, 36, 78]) * (1 - tt) + np.array([1, 28, 62]) * tt).astype(np.uint8)
        g[..., 3] = 255
        mask = Image.new("L", (BX1 - BX0 - 3, BH - 3), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, mask.width - 1, mask.height - 1), 11, fill=255)
        canvas.paste(Image.fromarray(g[: BH - 3, : BX1 - BX0 - 3], "RGBA"), (BX0, cy - BH // 2), mask)
        d.line((BX0 + 12, cy - BH // 2 + 1, BX1 - 16, cy - BH // 2 + 1), fill=(40, 80, 140), width=1)

        # crest clipped into the pentagon badge (clipping-mask look, nothing behind it)
        c = as_image(row.get("crest")) or crest_image(row.get("team", ""), teams)
        if c is not None:
            c = c.convert("RGBA")
            c = c.crop(c.getbbox())
            pw, rise = CX1 - CX0, 22
            ph = BH - 3 + rise
            shape = [(int(pw * 0.44), 0), (int(pw * 0.70), rise), (pw, rise), (pw, ph),
                     (int(pw * 0.17), ph), (int(pw * 0.03), rise + 12)]
            zoom = num(row.get("crest_zoom"), info.get("crest_zoom", 1.18))
            fy = num(row.get("crest_focus_y"), info.get("crest_focus_y", 0.5))
            sc = max(pw / c.width, ph / c.height) * zoom
            c = c.resize((max(1, round(c.width * sc)), max(1, round(c.height * sc))), Image.LANCZOS)
            panel = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            panel.alpha_composite(c, (pw // 2 - c.width // 2, int(ph * 0.55 - c.height * fy)))
            clip = Image.new("L", (pw * 4, ph * 4), 0)
            ImageDraw.Draw(clip).polygon([(px * 4, py * 4) for px, py in shape], fill=255)
            clip = clip.resize((pw, ph), Image.LANCZOS)
            a = np.minimum(np.asarray(panel.getchannel("A")), np.asarray(clip)).astype(np.uint8)
            panel.putalpha(Image.fromarray(a))
            px, py = CX0, cy - BH // 2 - rise
            sm = Image.new("RGBA", panel.size, (0, 0, 0, 255))
            sm.putalpha(Image.fromarray((a * 0.55).astype(np.uint8)))
            blur_composite(canvas, sm, (px - 6, py + 6), 7)
            canvas.alpha_composite(panel, (px, py))

        d.text((128, cy - 3), f"{i + 1:02d}", font=f_rank, fill=(247, 200, 60) if i == 0 else "white", anchor="mm")
        value = str(row["value"])
        name, f_name = fit_text(d, str(row.get("name") or row.get("team", "")).upper(), "Montserrat-Medium.ttf", 37,
                                962 - d.textlength(value, font=f_val) - 28 - 390, sp=2.2)
        spaced(d, (390, cy + 1), name, f_name, "white", 2.2)
        d.text((962, cy + 3), value, font=f_val, fill="white", anchor="rm")

    tagline(canvas, 1315, 24, 2.6)
    return canvas.convert("RGB")


TEMPLATE = Template(
    key="t2",
    name="Team ranking",
    order=10,
    category="Rankings",
    description="Up to 6 clubs ranked on one stat, with their crests.",
    render=render_team_ranking,
    filename=lambda v: slug(f"{v['title_white']} {v['title_blue']}"),
    fields=[
        Row(Text("title_white", "Title (white part)", "BALL"),
            Text("title_blue", "Title (blue part)", "POSSESSION")),
        Text("subtitle", "Subtitle", "BOTOLA PRO 2026-27"),
        Table(
            "rows", "Ranking (up to 6 rows, in order)",
            columns=[
                Column("team", "Team", kind="team"),
                Column("value", "Value", help="Printed as typed, e.g. 58.9% or 2.52"),
                Column("name", "Display name", help="Optional: overrides the team name"),
                Column("crest_zoom", "Crest zoom", kind="number", min_value=0.8, max_value=3.0, step=0.05,
                       help="Empty = team default from teams.json. Bigger = crest more zoomed in the badge."),
                Column("crest_focus_y", "Crest focus Y", kind="number", min_value=0.0, max_value=1.0, step=0.02,
                       help="Which part of the crest sits in the badge: 0.3 = top part, 0.5 = middle, 0.7 = lower part."),
            ],
            default_rows=[
                {"team": "RS BERKANE", "value": "68.0%"},
                {"team": "MAS DE FES", "value": "61.1%"},
                {"team": "AS FAR", "value": "58.9%"},
                {"team": "WYDAD TEMARA", "value": "58.0%"},
                {"team": "FUS RABAT", "value": "56.6%"},
                {"team": "WYDAD AC", "value": "55.6%"},
            ],
            required=["team", "value"],
            max_rows=6,
        ),
    ],
)
