"""Building blocks a template uses to declare its form.

These are plain declarations (no Streamlit here): `page.py` turns them into widgets and
passes the values to the template's `render()` as keyword arguments named after `key`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from PIL import Image


@dataclass(frozen=True)
class Text:
    """One-line text input -> render(key=str)."""
    key: str
    label: str
    default: str = ""
    help: str | None = None


@dataclass(frozen=True)
class Team:
    """Club dropdown (clubs from teams.json) -> render(key=str)."""
    key: str
    label: str
    default: str | None = None
    help: str | None = None


@dataclass(frozen=True)
class Color:
    """Color picker -> render(key="#RRGGBB").

    With default=None the color is optional: a checkbox turns the picker on, and render
    gets key=None until it is ticked (e.g. "use the team's color").
    """
    key: str
    label: str
    default: str | None = None
    help: str | None = None


@dataclass(frozen=True)
class Column:
    """A column of a Table. `key` is the dict key the renderer reads in each row."""
    key: str
    label: str
    kind: Literal["text", "team", "number"] = "text"  # "team" = dropdown of clubs from teams.json
    help: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None


@dataclass(frozen=True)
class Table:
    """Editable table -> render(key=list[dict]). Rows with an empty `required` cell are skipped."""
    key: str
    label: str
    columns: list[Column]
    default_rows: list[dict]
    required: list[str]
    max_rows: int | None = None


Box = tuple[int, int, int, int]  # x0, y0, x1, y1 in post pixels


@dataclass(frozen=True)
class Placement:
    """Where a photo sits in the post for a given zoom / x / y.

    The renderer and the drag-and-drop editor both use this, so what you drag is exactly
    what gets drawn.

    height: photo height in post pixels at zoom 1.0; None = cover the whole post.
    anchor: post point (x, y) that the photo's `pivot` sits on at x = y = 0.
    pivot:  point of the photo, as fractions of its width / height (0.5, 0.5 = center).
    """
    height: int | None = None
    anchor: tuple[float, float] = (540, 675)
    pivot: tuple[float, float] = (0.5, 0.5)
    min_height: int = 200

    def base_height(self, w: int, h: int, post: tuple[int, int] = (1080, 1350)) -> float:
        return self.height if self.height is not None else h * max(post[0] / w, post[1] / h)

    def box(self, w: int, h: int, zoom: float, x: float, y: float) -> tuple[int, int, int, int]:
        """(left, top, width, height) of a w x h photo in the post."""
        # round(…, 6) first: 1440 * 1.4 is 2015.9999… in floating point and must give 2016
        ph = max(self.min_height, int(round(self.base_height(w, h) * zoom, 6)))
        pw = round(w * ph / h)
        left = int(self.anchor[0]) - int(self.pivot[0] * pw) + int(x)
        top = int(self.anchor[1]) - int(self.pivot[1] * ph) + int(y)
        return left, top, pw, ph


@dataclass(frozen=True)
class Photo:
    """Image upload, positioned with a drag-and-zoom editor (plus fine-tune sliders).

    -> render(key=file, key_zoom=float, key_x=int, key_y=int).
    guides: optional function values -> list of Box. The boxes are shown in the editor and,
            when "Show safe-area guides" is ticked, on the preview (never in the download).
    """
    key: str
    label: str
    title: str = "Photo"
    placement: Placement = Placement()
    guides: Callable[[dict], list[Box]] | None = None
    guides_help: str | None = None
    zoom: tuple[float, float, float, float] = (0.5, 2.5, 1.0, 0.01)  # min, max, default, step
    x: tuple[int, int, int, int] = (-600, 600, 0, 1)
    y: tuple[int, int, int, int] = (-800, 600, 0, 1)


@dataclass(frozen=True)
class Row:
    """Puts several small fields (Text, Team, Color) side by side."""
    fields: tuple[Text | Team | Color, ...]

    def __init__(self, *fields: Text | Team | Color):
        object.__setattr__(self, "fields", fields)


Field = Text | Team | Color | Table | Photo | Row


@dataclass(frozen=True)
class Template:
    """A post template: what the form asks for and how to draw the post.

    Put one in a module of `bi_studio/templates/` as `TEMPLATE = Template(...)` and it shows
    up in the BI Studio catalog automatically, with a thumbnail rendered from the field defaults.
    """
    key: str                                  # unique, used for widget keys
    name: str                                 # card title in the catalog
    render: Callable[..., Image.Image]
    fields: list[Field]
    filename: Callable[[dict], str]           # values -> download file name (without .png)
    order: int = 100                          # position in the catalog (lower = first)
    description: str = ""                     # one line on the catalog card
    category: str = "Other"                   # catalog group, e.g. "Match" or "Rankings"
