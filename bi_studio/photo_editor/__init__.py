"""Drag-and-zoom photo editor: a Streamlit custom component in plain HTML/JS (no build step).

Shows the post frame with the photo, the template's safe areas and corner handles. Drag to
move, scroll or drag a corner to resize, double-click to reset. Returns
{"zoom", "x", "y", "seq"} after each change (seq is new for every change), else None.
"""
from __future__ import annotations

import os

import streamlit.components.v1 as components

from ..brand import NAVY, W, H
from ..fields import Photo

_component = components.declare_component(
    "bi_studio_photo_editor", path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
)


def photo_editor(
    field: Photo,
    image_url: str,
    image_id: str,
    size: tuple[int, int],
    zoom: float,
    x: int,
    y: int,
    boxes: list[tuple[int, int, int, int]],
    key: str,
) -> dict | None:
    """image_url: small preview of the photo (data URL); size: the photo's real (w, h)."""
    p = field.placement
    w, h = size
    return _component(
        image=image_url,
        image_id=image_id,
        img_w=w,
        img_h=h,
        placement={"base_height": p.base_height(w, h, (W, H)), "anchor": list(p.anchor),
                   "pivot": list(p.pivot), "min_height": p.min_height},
        post=[W, H],
        navy="#%02x%02x%02x" % NAVY,
        zoom=zoom,
        x=x,
        y=y,
        defaults={"zoom": field.zoom[2], "x": field.x[2], "y": field.y[2]},
        limits={"zoom": list(field.zoom[:2]), "x": list(field.x[:2]), "y": list(field.y[:2])},
        boxes=[list(b) for b in boxes],
        key=key,
        default=None,
    )
