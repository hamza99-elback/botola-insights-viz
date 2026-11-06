"""Drawing helpers shared by the templates (Pillow only)."""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

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


def blend_photo(canvas: Image.Image, photo: Image.Image, box: tuple[int, int, int, int],
                fade: Image.Image | None = None, soft_edge: int = 30) -> Image.Image:
    """Blend photo (any size) into canvas at box = (left, top, width, height) from Placement.box().

    Only the part inside the canvas is resized. fade: optional full-canvas "L" mask of the photo's
    opacity (e.g. hidden behind a text column). When the photo doesn't cover the whole canvas, its
    inner edges are softened over `soft_edge` px; edges on the canvas border stay sharp.
    Returns a new RGB image.
    """
    cw, ch = canvas.size
    canvas = canvas.convert("RGB")
    left, top, pw, ph = box
    x0, y0, x1, y1 = max(0, left), max(0, top), min(cw, left + pw), min(ch, top + ph)
    if x0 >= x1 or y0 >= y1:
        return canvas
    sx, sy = photo.width / pw, photo.height / ph
    src = ((x0 - left) * sx, (y0 - top) * sy, (x1 - left) * sx, (y1 - top) * sy)
    layer = canvas.copy()
    layer.paste(photo.resize((x1 - x0, y1 - y0), Image.LANCZOS, box=src), (x0, y0))
    mask = Image.new("L", (cw, ch), 0)
    mask.paste(fade.crop((x0, y0, x1, y1)) if fade else 255, (x0, y0, x1, y1))
    if (x0, y0, x1, y1) != (0, 0, cw, ch) and soft_edge:
        e = soft_edge
        inset = (x0 + (e if x0 > 0 else 0), y0 + (e if y0 > 0 else 0),
                 x1 - 1 - (e if x1 < cw else 0), y1 - 1 - (e if y1 < ch else 0))
        pad = 2 * e  # blur on a padded canvas so the border sides really stay at full opacity
        edge = Image.new("L", (cw + 2 * pad, ch + 2 * pad), 0)
        ImageDraw.Draw(edge).rectangle(
            (inset[0] + (pad if x0 > 0 else 0), inset[1] + (pad if y0 > 0 else 0),
             inset[2] + (pad if x1 < cw else 2 * pad), inset[3] + (pad if y1 < ch else 2 * pad)), fill=255)
        edge = edge.filter(ImageFilter.GaussianBlur(e * 0.6)).crop((pad, pad, pad + cw, pad + ch))
        mask = ImageChops.multiply(mask, edge)
    return Image.composite(layer, canvas, mask)


def draw_condensed(canvas: Image.Image, xy, text: str, f: ImageFont.FreeTypeFont, fill, condense: float,
                   anchor: str = "ls", stroke: int = 0):
    """Draw text squeezed horizontally to `condense` x its width (same height), on an RGBA canvas.

    anchor: "ls" (x = left) or "rs" (x = right) on the baseline y. Measure with condensed_len().
    """
    if not text:
        return
    d = ImageDraw.Draw(canvas)
    l, t, r, b = d.textbbox((0, 0), text, font=f, anchor="ls", stroke_width=stroke)
    pad = 4
    layer = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((pad - l, pad - t), text, font=f, fill=fill, anchor="ls",
                               stroke_width=stroke, stroke_fill=fill)
    layer = layer.resize((max(1, round(layer.width * condense)), layer.height), Image.LANCZOS)
    x, y = xy
    left = x + round(l * condense) if anchor == "ls" else x - layer.width + round(pad * condense)
    canvas.alpha_composite(layer, (round(left - pad * condense), y + t - pad))


def condensed_len(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, condense: float) -> float:
    return d.textlength(text, font=f) * condense


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
