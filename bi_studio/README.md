# BI Studio

Generates the Botola Insights Instagram posts (1080 x 1350 PNG) from values typed into a table.
Runs fully offline, with no AI service or subscription needed.

Opened from the **BI Studio** section in the app sidebar:

```bash
streamlit run streamlit_app.py
```

## Templates

| Template | Renderer |
|---|---|
| Team ranking | `render_team_ranking` |
| Player top 5 | `render_top5` |
| Match stats | `render_match_stats` |

The renderers can be used without the UI (e.g. for batch generation):

```python
from bi_studio import render_team_ranking, render_top5

img = render_team_ranking("BALL", "POSSESSION", rows=[
    {"team": "RS BERKANE", "value": "68.0%"},
    {"team": "AS FAR", "value": "58.9%"},
])
img.save("ball_possession.png")

img = render_top5("UP TO GW04", "SHOTS PER MATCH",
                  rows=[{"name": "S. Ganvoula", "team": "WYDAD AC", "value": "5.0"}],
                  photo="samples/ganvoula.jpg", photo_zoom=1.0, photo_x=0, photo_y=0)
```

## Positioning a photo (Player top 5, Match stats)

After uploading the photo, an editor shows the post frame with the photo, the template's
safe areas (pink boxes) and the photo's outline with corner handles:

| Action | What it does |
|---|---|
| **Drag the photo** | Moves it. The part outside the post is shown dimmed. |
| **Scroll** (or trackpad pinch) | Zooms in/out around the cursor. |
| **Drag a corner handle** | Resizes; the opposite corner stays put. |
| **Double-click** | Back to the default placement. |

The preview on the right re-renders when you release the mouse (or stop scrolling).
Keep faces out of the pink boxes; they are never in the downloaded PNG.

**Fine-tune position (exact values)** under the editor has Zoom / Horizontal / Vertical
sliders, synced with the editor, and **Reset position**. Zoom 1.0 = the template's default
size; Horizontal / Vertical are shifts in post pixels (post is 1080 x 1350; negative = left / up).
When a photo looks right, note the three values: a photo from the same photographer usually
needs similar values next time.

Without the UI, pass the same three settings as `photo_zoom`, `photo_x` and `photo_y` to the
render function (`render_top5`, `render_match_stats`).

## Match stats

Background photo with a card showing the two crests, the Botola Insights logo, and one
stacked bar per stat (home share = home / (home + away)).

- **Stats table:** values are printed as typed (`61%`, `12`, `1.84`); the bar uses the number
  inside each value. `0`–`0` or text without a number gives a 50/50 bar.
- **Bar colors:** the home bar uses the home team's color from `teams.json` unless you tick
  "Custom home bar color". The away bar is white by default.
- **Background photo:** positioned with the same editor as Player top 5.
  Zoom 1.0 = the photo covers the whole post. If you zoom out or move it past an edge, the
  gap is filled with a blurred copy of the photo. The guides mark the card, league logo and tagline.
- **League logo (top-left):** drawn when `bi_studio/assets/league_logo.png` exists
  (transparent PNG, white logo). Skipped otherwise.

## Adjusting a crest (Team ranking)

Crests are zoomed and clipped into the badge shape. Each team has default settings in `teams.json`. To change one post only, use the table columns:
- **Crest zoom**: bigger = more zoomed in (default 1.18; AS FAR uses 1.6).
- **Crest focus Y**: which part of the crest fills the badge (0.3 = top, 0.5 = middle, 0.7 = bottom).

Leave a cell empty to use the team's default.

## Adding a club

1. Put its transparent PNG crest in `bi_studio/assets/crests/` (e.g. `husa.png`).
2. Add a line to `bi_studio/teams.json`:
   ```json
   "HUS AGADIR": {"crest": "husa.png", "color": [225, 40, 45], "crest_zoom": 1.18, "crest_focus_y": 0.5}
   ```
   `color` is the accent line under the team's card (RGB).

The club then appears in the Team dropdown of both tables.

## Adding a template

Create one file in `bi_studio/templates/` (e.g. `match_result.py`) with a render function and
a `TEMPLATE` declaration. It appears as a new tab in BI Studio. No UI code is needed.

```python
from PIL import Image, ImageDraw

from ..brand import NAVY, W, H, font                  # brand colors, post size, fonts
from ..fields import Column, Photo, Placement, Row, Table, Template, Text
from ..primitives import fit_text, slug, tagline       # shared drawing helpers


def render_match_result(title: str, rows: list[dict]) -> Image.Image:
    img = Image.new("RGBA", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    text, f = fit_text(d, title.upper(), "BebasNeue-Regular.ttf", 96, max_width=W - 80)
    d.text((W / 2, 240), text, font=f, fill="white", anchor="mm")
    ...
    tagline(img, 1315, 24, 2.6)
    return img.convert("RGB")


TEMPLATE = Template(
    key="match_result",                 # unique
    name="Match result",                # tab label
    order=30,                           # tab position
    render=render_match_result,
    filename=lambda v: slug(v["title"]),
    fields=[                            # each field's key = a render() argument
        Text("title", "Title", "RAJA 2-1 WYDAD"),
        Table("rows", "Stats", columns=[Column("team", "Team", kind="team"), Column("value", "Value")],
              default_rows=[], required=["team", "value"], max_rows=6),
    ],
)
```

Field types (`bi_studio/fields.py`):

| Field | Form widget | Passed to `render()` |
|---|---|---|
| `Text(key, label, default)` | text input | `key=str` |
| `Team(key, label, default)` | club dropdown (from `teams.json`) | `key=str` |
| `Color(key, label, default)` | color picker; with `default=None` it is optional (checkbox) | `key="#RRGGBB"` or `None` |
| `Row(...)` | puts `Text` / `Team` / `Color` fields side by side | each field's value |
| `Table(key, label, columns, default_rows, required, max_rows)` | editable table; a `Column` is `text`, `team` (club dropdown) or `number` | `key=list[dict]`, one dict per filled row |
| `Photo(key, label, placement=..., guides=...)` | upload + drag-and-zoom editor + fine-tune sliders | `key` (PIL image), `key_zoom`, `key_x`, `key_y` |

For a `Photo`, declare where it sits and what to keep clear, and use the same `Placement`
in the render function so the editor matches the post exactly:

```python
PLACEMENT = Placement(height=1430, anchor=(790, -30), pivot=(0.56, 0))  # or Placement() = cover the post

def guide_boxes(values):              # areas to keep faces out of, in post pixels (x0, y0, x1, y1)
    return [(54, 150, 511, 603)]

# in render(): left, top, pw, ph = PLACEMENT.box(photo.width, photo.height, photo_zoom, photo_x, photo_y)
Photo("photo", "Photo", placement=PLACEMENT, guides=guide_boxes)
```

Use `fit_text()` for any text whose length depends on the input, so long names shrink and then
end with "…" instead of overflowing.

## Contents

- `bi_studio/templates/`: one file per template (`team_ranking.py`, `player_top5.py`, `match_stats.py`), auto-registered
- `bi_studio/fields.py`: the field types a template declares
- `bi_studio/brand.py`: post size, colors, tagline, fonts, logo, background, clubs
- `bi_studio/primitives.py`: shared drawing helpers (`fit_text`, letter-spaced text, tagline, guides)
- `bi_studio/page.py`: the Streamlit page (`bi_studio_page()`), builds each tab from the template's fields; caches finished posts
- `bi_studio/photo_editor/`: the drag-and-zoom photo editor (Streamlit component, plain HTML/JS, no build step)
- `bi_studio/teams.json`: clubs, crests, colors, crest crop defaults
- `bi_studio/assets/`: fonts (Montserrat, Bebas Neue, SIL Open Font License), logo, background, crests
- `samples/ganvoula.jpg`: sample photo for testing
