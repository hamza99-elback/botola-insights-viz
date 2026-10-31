"""BI Studio: Streamlit page that generates Botola Insights Instagram posts.

    from bi_studio.page import bi_studio_page
    bi_studio_page()

The page has one tab per template (see `bi_studio/templates/`). Each tab's form is built
from the template's declared fields, so templates contain no Streamlit code.

Speed: Streamlit reruns the whole page (every tab) on each interaction, so finished posts
are cached by their inputs. Only the post whose inputs changed is rendered again.
"""
from __future__ import annotations

import base64
import glob
import hashlib
import inspect
import io
import os

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from .brand import load_teams
from .fields import Color, Photo, Row, Table, Team, Template, Text
from .photo_editor import photo_editor
from .primitives import guides
from .templates import load_templates_with_errors

MAX_PHOTO_SIDE = 3600   # enough for zoom 2.5 on a full-height photo; bigger uploads are shrunk
EDITOR_PHOTO_SIDE = 1000
PREVIEW_WIDTH = 900


def _wide(fn, *args, **kwargs):
    """Call a Streamlit element full-width on both new (width="stretch") and older versions."""
    params = inspect.signature(fn).parameters
    width = params.get("width")
    if width is not None and isinstance(width.default, str):  # new API: width="stretch" / "content"
        return fn(*args, width="stretch", **kwargs)
    if "use_container_width" in params:
        return fn(*args, use_container_width=True, **kwargs)
    if "use_column_width" in params:  # older st.image
        return fn(*args, use_column_width=True, **kwargs)
    return fn(*args, **kwargs)


def _jpeg(img: Image.Image, width: int = PREVIEW_WIDTH, quality: int = 88) -> bytes:
    buf = io.BytesIO()
    img.resize((width, round(img.height * width / img.width)), Image.LANCZOS).save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", compress_level=1)  # ~3x faster than the default; Instagram re-encodes anyway
    return buf.getvalue()


def _code_version() -> tuple[float, ...]:
    """Modification times of the BI Studio code, so cached posts refresh after a template edit."""
    here = os.path.dirname(os.path.abspath(__file__))
    return tuple(os.path.getmtime(p) for p in sorted(glob.glob(os.path.join(here, "**", "*.py"), recursive=True)))


@st.cache_resource(max_entries=8, show_spinner=False)
def _load_photo(data: bytes) -> tuple[Image.Image, str, str]:
    """Uploaded file bytes -> (photo for rendering, small data URL for the editor, photo id)."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")  # phone photos: apply rotation
    if max(img.size) > MAX_PHOTO_SIDE:
        img.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE), Image.LANCZOS)
    small = img.copy()
    small.thumbnail((EDITOR_PHOTO_SIDE, EDITOR_PHOTO_SIDE), Image.LANCZOS)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=82)
    url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return img, url, hashlib.sha1(data).hexdigest()


@st.cache_data(max_entries=32, show_spinner=False)
def _render_cached(template_key: str, values: dict, photo_ids: dict, boxes: list, code_version: tuple,
                   _template: Template, _photos: dict) -> tuple[bytes, bytes | None, bytes]:
    """(preview JPEG, preview JPEG with safe-area guides or None, download PNG).

    Cached by everything except the `_`-prefixed arguments (photos are keyed by photo_ids).
    """
    img = _template.render(**values, **_photos)
    with_guides = None
    if boxes:
        g = img.convert("RGBA")
        guides(g, boxes)
        with_guides = _jpeg(g.convert("RGB"))
    return _jpeg(img), with_guides, _png(img)


def _clean_rows(df: pd.DataFrame, required: list[str]) -> list[dict]:
    """Table rows -> list of dicts, skipping rows with an empty required cell."""
    rows = []
    for rec in df.to_dict("records"):
        if all(str(rec.get(k, "") or "").strip() and str(rec.get(k)) != "nan" for k in required):
            rows.append(rec)
    return rows


# --------------------------------------------------------------------------- field widgets
def _text(f: Text, prefix: str) -> dict:
    return {f.key: st.text_input(f.label, f.default, key=f"{prefix}_{f.key}", help=f.help)}


def _team(f: Team, prefix: str, team_names: list[str]) -> dict:
    index = team_names.index(f.default) if f.default in team_names else 0
    return {f.key: st.selectbox(f.label, team_names, index=index, key=f"{prefix}_{f.key}", help=f.help)}


def _color(f: Color, prefix: str) -> dict:
    k = f"{prefix}_{f.key}"
    if f.default is not None:
        return {f.key: st.color_picker(f.label, f.default, key=k, help=f.help)}
    if not st.checkbox(f"Custom {f.label.lower()}", key=f"{k}_on", help=f.help):
        return {f.key: None}
    return {f.key: st.color_picker(f.label, "#FFFFFF", key=k)}


def _column_config(f: Table, team_names: list[str]) -> dict:
    config = {}
    for c in f.columns:
        if c.kind == "team":
            config[c.key] = st.column_config.SelectboxColumn(c.label, options=team_names, required=True, help=c.help)
        elif c.kind == "number":
            config[c.key] = st.column_config.NumberColumn(
                c.label, min_value=c.min_value, max_value=c.max_value, step=c.step, help=c.help)
        else:
            config[c.key] = st.column_config.TextColumn(c.label, help=c.help)
    return config


def _table(f: Table, prefix: str, team_names: list[str]) -> dict:
    st.markdown(f"**{f.label}**")
    keys = [c.key for c in f.columns]
    default = pd.DataFrame([{k: r.get(k) for k in keys} for r in f.default_rows], columns=keys)
    for c in f.columns:  # empty text cells as "" so they stay editable as text
        if c.kind != "number":
            default[c.key] = default[c.key].fillna("")
    df = _wide(st.data_editor, default, key=f"{prefix}_{f.key}", num_rows="dynamic",
               column_config=_column_config(f, team_names))
    if f.max_rows and len(df) > f.max_rows:
        st.warning(f"Only the first {f.max_rows} rows are drawn.")
    return {f.key: _clean_rows(df, f.required)}


def _photo_keys(f: Photo, k: str) -> tuple[dict, dict]:
    """Session-state keys of the zoom / x / y values, and their defaults."""
    keys = {"zoom": f"{k}_zoom", "x": f"{k}_x", "y": f"{k}_y"}
    defaults = {"zoom": float(f.zoom[2]), "x": int(f.x[2]), "y": int(f.y[2])}
    return keys, defaults


def _apply_editor_event(event, f: Photo, k: str) -> bool:
    """Copy a new editor change into the zoom / x / y values. Returns True if it was new."""
    if not event or event.get("seq") == st.session_state.get(f"{k}_seq"):
        return False
    keys, _ = _photo_keys(f, k)
    st.session_state[f"{k}_seq"] = event["seq"]
    st.session_state[keys["zoom"]] = float(min(max(event["zoom"], f.zoom[0]), f.zoom[1]))
    st.session_state[keys["x"]] = int(min(max(event["x"], f.x[0]), f.x[1]))
    st.session_state[keys["y"]] = int(min(max(event["y"], f.y[0]), f.y[1]))
    return True


def _reset_position(f: Photo, k: str):
    keys, defaults = _photo_keys(f, k)
    for name, key in keys.items():
        st.session_state[key] = defaults[name]


def _photo(f: Photo, prefix: str, values: dict) -> dict:
    st.markdown(f"**{f.title}**")
    k = f"{prefix}_{f.key}"
    keys, defaults = _photo_keys(f, k)
    for name, key in keys.items():
        st.session_state.setdefault(key, defaults[name])

    upload = st.file_uploader(f.label, type=["png", "jpg", "jpeg", "webp"], key=k)
    photo = photo_id = None
    if upload is not None:
        photo, url, photo_id = _load_photo(upload.getvalue())
        # the editor's last change arrives in session_state before it is drawn again:
        # apply it first so the editor and the sliders get the new values in this run
        _apply_editor_event(st.session_state.get(f"{k}_editor"), f, k)
        event = photo_editor(
            f, url, photo_id, photo.size,
            st.session_state[keys["zoom"]], st.session_state[keys["x"]], st.session_state[keys["y"]],
            f.guides(values) if f.guides else [], key=f"{k}_editor",
        )
        if _apply_editor_event(event, f, k):
            st.rerun()  # fallback if the change wasn't in session_state yet: redraw with it

    with st.expander("Fine-tune position (exact values)"):
        st.slider("Zoom", f.zoom[0], f.zoom[1], step=f.zoom[3], key=keys["zoom"])
        st.slider("Horizontal (← left / right →)", f.x[0], f.x[1], step=f.x[3], key=keys["x"])
        st.slider("Vertical (↑ up / down ↓)", f.y[0], f.y[1], step=f.y[3], key=keys["y"])
        st.button("Reset position", key=f"{k}_reset", on_click=_reset_position, args=(f, k))

    out = {f.key: photo, f"{f.key}_id": photo_id, f"{f.key}_zoom": st.session_state[keys["zoom"]],
           f"{f.key}_x": st.session_state[keys["x"]], f"{f.key}_y": st.session_state[keys["y"]]}
    if f.guides:
        out["show_guides"] = st.checkbox("Show safe-area guides on the preview (not exported)", value=True,
                                         key=f"{k}_guides", help=f.guides_help)
    return out


def _field(f, prefix: str, team_names: list[str], values: dict) -> dict:
    """Draw one field's widgets; `values` = what the fields above it returned (e.g. for guides)."""
    if isinstance(f, Row):
        out = {}
        for col, sub in zip(st.columns(len(f.fields)), f.fields):
            with col:
                out.update(_field(sub, prefix, team_names, values))
        return out
    if isinstance(f, Text):
        return _text(f, prefix)
    if isinstance(f, Team):
        return _team(f, prefix, team_names)
    if isinstance(f, Color):
        return _color(f, prefix)
    if isinstance(f, Table):
        return _table(f, prefix, team_names)
    if isinstance(f, Photo):
        return _photo(f, prefix, values)
    raise TypeError(f"Unknown field type: {type(f).__name__}")


def _missing(t: Template, values: dict) -> str | None:
    """Message to show instead of the preview while required input is missing."""
    for f in t.fields:
        if isinstance(f, Photo) and values.get(f.key) is None:
            return f"Upload the {f.title.lower()} to see the preview."
        if isinstance(f, Table) and not values.get(f.key):
            return "Fill at least one row."
    return None


# --------------------------------------------------------------------------- template tab
def _template_ui(t: Template, team_names: list[str]):
    left, right = st.columns([1, 1], gap="large")
    with left:
        if t.description:
            st.caption(t.description)
        values = {}
        for f in t.fields:
            values.update(_field(f, t.key, team_names, values))

    with right:
        message = _missing(t, values)
        if message:
            st.info(message)
            return
        show_guides = values.pop("show_guides", False)
        photo_fields = [f for f in t.fields if isinstance(f, Photo)]
        photos = {f.key: values.pop(f.key) for f in photo_fields}
        photo_ids = {f.key: values.pop(f"{f.key}_id") for f in photo_fields}
        boxes = [b for f in photo_fields if f.guides for b in f.guides(values)]
        preview, preview_guides, png = _render_cached(
            t.key, values, photo_ids, boxes, _code_version(), _template=t, _photos=photos)
        _wide(st.image, preview_guides if show_guides and preview_guides else preview,
              caption="Preview (1080 x 1350)")
        st.download_button("Download PNG", png, file_name=f"{t.filename(values)}.png",
                           mime="image/png", type="primary", key=f"{t.key}_download")


# --------------------------------------------------------------------------- entry
def bi_studio_page():
    st.header("BI Studio")
    st.caption("Generate Botola Insights Instagram posts (1080 x 1350 PNG).")
    team_names = sorted(load_teams().keys())
    templates, errors = load_templates_with_errors()
    for name, error in errors.items():
        st.error(f"Template `{name}.py` could not be loaded and is hidden: {error}\n\n"
                 "If the code looks right, restart Streamlit (Ctrl+C, then `streamlit run streamlit_app.py`).")
    if not templates:
        return
    for tab, t in zip(st.tabs([t.name for t in templates]), templates):
        with tab:
            _template_ui(t, team_names)
