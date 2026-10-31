"""Drawing helpers shared by the templates (Pillow only)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .brand import TAGLINE, W, H, font

ELLIPSIS = "…"


def as_image(x) -> Image.Image | None:
    if x is None:
        return None
    if isinstance(x, Image.Image):
        return x
    return Image.open(x)  # path or file-like (e.g. Streamlit UploadedFile)


def num(v, default):
    """Number from a table cell; falls back to default for empty / NaN cells."""
    try:
        v = float(v)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def slug(text: str) -> str:
    """File-name-safe version of text: "Ball possession" -> "ball_possession"."""
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_") or "post"


def spaced(d: ImageDraw.ImageDraw, xy, text, f, fill, sp, anchor="lm", stroke=0):
    """Draw letter-spaced text starting at xy; returns end x."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=fill)
        x += d.textlength(ch, font=f) + sp
    return x - sp


def spaced_len(d, text, f, sp):
    return sum(d.textlength(c, font=f) for c in text) + sp * (len(text) - 1)


def fit_text(
    d: ImageDraw.ImageDraw,
    text: str,
    font_name: str,
    size: int,
    max_width: float,
    sp: float = 0,
    min_size: int | None = None,
) -> tuple[str, ImageFont.FreeTypeFont]:
    """Largest font (size down to min_size) at which text fits max_width.

    If it still doesn't fit at min_size, the text is cut and ends with "…".
    Returns (text to draw, font to draw it with).
    """
    def width(t, f):
        return spaced_len(d, t, f, sp) if sp else d.textlength(t, font=f)

    min_size = min_size or round(size * 0.65)
    for s in range(size, min_size - 1, -1):
        f = font(font_name, s)
        if width(text, f) <= max_width:
            return text, f
    f = font(font_name, min_size)
    while len(text) > 1 and width(text.rstrip() + ELLIPSIS, f) > max_width:
        text = text[:-1]
    return text.rstrip() + ELLIPSIS, f


def blur_composite(canvas: Image.Image, layer: Image.Image, xy: tuple[int, int], radius: float):
    """Alpha-composite `layer`, blurred by `radius`, onto canvas at xy.

    Same pixels as blurring a full-size transparent layer, but only the area around the
    layer is blurred (much faster for shadows).
    """
    pad = int(3 * radius) + 8
    padded = Image.new("RGBA", (layer.width + 2 * pad, layer.height + 2 * pad), (0, 0, 0, 0))
    padded.paste(layer, (pad, pad))
    padded = padded.filter(ImageFilter.GaussianBlur(radius))
    x, y = xy[0] - pad, xy[1] - pad
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + padded.width), min(canvas.height, y + padded.height)
    if x0 < x1 and y0 < y1:
        canvas.alpha_composite(padded.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def tagline(canvas, y, size, sp):
    d = ImageDraw.Draw(canvas)
    f = font("Montserrat-Italic.ttf", size)
    spaced(d, (W / 2 - spaced_len(d, TAGLINE, f, sp) / 2, y), TAGLINE, f, (235, 240, 248), sp)


def guides(canvas, boxes):
    """Semi-transparent overlay marking areas the photo should stay clear of."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for b in boxes:
        od.rectangle(b, fill=(255, 0, 80, 45), outline=(255, 0, 80, 200), width=3)
    canvas.alpha_composite(ov)
