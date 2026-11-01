# Botola Insights Viz: Enhancement Plan

> Goal: turn the current Streamlit prototype into a clean, maintainable chart studio that
> produces **Instagram-ready graphics** (heatmaps, shot maps, radars, match-stat bars,
> goal-location maps) quickly and consistently.

This plan is based on a full read of the current codebase (branch `dev`, commit `01c94ce`).
Each phase ends in a working app, so it can be merged on its own.

**Done so far:**
- The standalone posts app (`botola_posts_app`) was merged into this project as
  **BI Studio** (`bi_studio/`). It opens from the app sidebar (**Charts** | **BI Studio**).
- Phase 7.1–7.3: template registry (one file per template), shared brand/primitives, `fit_text`.
  Existing posts render pixel-identical to before.
- New BI Studio template **Match stats** (photo background + home/away stacked bars),
  plus `Team` and `Color` field types.
- Deploy blockers (2026-11-01): `.env` and the Azure DB code removed, radar font path, console
  logging, one pinned `requirements.txt` tested in a clean Python 3.11 env. Open items are in
  `personal_notes.txt` section 1 (the passwords are still in the git history).
- Drag-and-zoom photo editor (Player top 5, Match stats) + rendering speed-ups: finished posts
  are cached per input, renderers 2–9x faster (team ranking 577 → 63 ms), light JPEG previews.

---

## 0. Current state (audit summary)

### What the app does today
`botola_insights_app/app.py` is one 658-line Streamlit file with 5 tabs. Each tab takes an
uploaded or pasted JSON/CSV and renders a matplotlib figure through a class in `charts/`:

| Tab | Input | Chart class |
|---|---|---|
| Heatmap | Sofascore heatmap JSON (`points` / `heatmap`) | `charts/heatmap.py::Heatmap.draw` |
| Shootmap | Sofascore shotmap JSON | `charts/shootmap.py::ShootMap.draw_v2` + `ShootmapProcessor` |
| Radarchart | CSV (`;`-separated, 2 rows) | `charts/radarchart.py::Radarchart.draw_v2` |
| Stacked barchart | 12 manual text inputs | `charts/stackedbarchart.py::StackedBarChart` |
| Goal Location | Sofascore shotmap JSON | `charts/shot_goal_location.py::ShotGoalLocation` |

### Critical issues
1. **Secrets are committed.** `.env` is tracked in git (and pushed to GitHub) even though it
   is listed in `.gitignore`. It holds 4 Azure SQL connection strings **with passwords**.
   → Rotate the credentials, run `git rm --cached .env`, and consider purging it from history.
2. **Hard-coded absolute path.** `radarchart.py:162` loads the font from
   `C:/Users/hp/Documents/...`, so the radar chart breaks on any other machine or deployment.
3. **Real xG is thrown away.** `ShootmapProcessor.process_data()` sets `df["xg"] = 1`, so
   marker sizes on shot maps and goal-location charts never reflect xG.
4. **The app crashes on bad input.** Invalid JSON, missing keys, or non-numeric stacked-bar
   values raise exceptions instead of showing a message.
5. **Environment can't install on Python 3.13** (the local interpreter). `numpy==1.26.4` and
   `pandas==2.2.1` have no 3.13 wheels. `scipy` and `Pillow` are imported but not listed. There
   are 3 competing requirement files (`requirements.txt`, `botola_insights_app/requirements.txt`
   (UTF-16 encoded), and the untracked `old_requirements.txt`).

### Bugs and smaller defects
- `ShotGoalLocation.draw()` calls `plt.show()` unconditionally and uses `cm.get_cmap`
  (removed in matplotlib ≥ 3.9).
- Figures are never closed (`plt.close`), so memory grows with every Streamlit rerun.
- `ShootMap` draws the pitch inside `__init__`, so constructing it has side effects.
- `ShootmapProcessor` mutates the input and triggers pandas `SettingWithCopyWarning`. It also
  has leftover `print()` calls.
- Logging writes to `./../logs/…` relative to the CWD and fails silently.
- In the stacked bar, input labels and `itemName` order don't match (inputs are reversed but
  names aren't), and the item names are never drawn on the chart.
- Radar `high = max(player1, player2)` puts one player on the outer ring for every metric.
  There are no custom ranges and no legend or player names.
- UI typos and wrong copy: "Shoose a Team", Goal-Location selectbox labelled "Shoose a season"
  (it is Home/Away), Goal-Location text area says "Paste the heatmap".
- Duplicate color-picker labels ("Color" / "Color") with no indication of which team is which.

### Unused / dead code (removal candidates)
| Item | Why it's dead |
|---|---|
| `main.py` | Scratch script: commented-out CLI, generator demos, one-off pass→xlsx conversion |
| `charts/batch_shootmap.py`, `new_shootmap.py`, `player_shootmap.py`, `shootmap_ready.py` | Four copy-pasted variants of `ShootMap`, imported nowhere |
| `charts/passing_network.py` | Standalone script (needs `networkx`, not in requirements), not wired to the app |
| `charts/pizzachart.py` + `pizzachart_visualisations()` | Tab commented out; depends on the removed DB cursor |
| DB layer in `app.py`: `get_all_teams_list`, `get_seasons_list*`, `get_all_players_list`, `get_players_list`, `get_teams_by_season`, `get_matches_list`, `team/player/kpis_*` widgets, `CONN`, `cursor`, `*_LIST` globals | All stubbed with `""`; `get_query_result` is undefined |
| `goal_keeper_vizualisations()` | Never called; depends on the DB cursor |
| `data/azure_data_extraction.py`, `botola_insights_app/queries.sql`, `botola_insights_app/packages.txt` (ODBC drivers) | Only used by the abandoned DB path |
| `tools/json_tool.py` | Only used by `__main__` demo blocks |
| Unused methods: `ShootMap.draw`, `ShootMap.draw_v3`, `Heatmap.draw_v2`, `Radarchart.draw`, `ShootmapProcessor.process_data_mono` | Not called by the app |
| `__main__` demo blocks in every chart file | They reference local data files that aren't in the repo |
| `fonts/Roboto-Medium.ttf` | Duplicate of `assets/fonts/roboto/Roboto-Medium.ttf` |
| `images/goal_location/*.png` | Generated output committed to git |
| `charts/__init__.py` imports | Re-exports unused mplsoccer symbols |
| `random.seed(42)`, `uuid` usage in `app.py` | No randomness in the app |

---

## 1. Target architecture

```
botola-insights-viz/
├── app/                          # Streamlit UI layer (no plotting logic here)
│   ├── main.py                   # entry: page config, theme, navigation
│   ├── pages/
│   │   ├── heatmap.py
│   │   ├── shotmap.py
│   │   ├── goal_location.py
│   │   ├── radar.py
│   │   ├── match_stats.py        # (was "stacked barchart")
│   │   └── bi_studio.py          # template picker → form → preview → download
│   └── components/
│       ├── data_input.py         # upload / paste / load-sample + validation + errors
│       ├── color_controls.py     # team-preset picker + custom colors
│       ├── export_panel.py       # format preset, background, DPI, download
│       └── layout.py             # header/logo, two-column "controls | preview" layout
│
├── botola_viz/                   # Pure Python library: importable, testable, UI-agnostic
│   ├── charts/
│   │   ├── base.py               # BaseChart: figure creation, theme, fonts, render()->Figure
│   │   ├── heatmap.py
│   │   ├── shotmap.py
│   │   ├── goal_location.py
│   │   ├── radar.py
│   │   └── match_stats.py
│   ├── parsers/
│   │   ├── sofascore.py          # shotmap / heatmap JSON → typed DataFrames (keeps real xG)
│   │   └── csv_stats.py          # radar CSV parsing (comma/percent cleanup)
│   ├── core/
│   │   ├── theme.py              # brand palette, fonts, text styles
│   │   ├── teams.py              # Botola club color presets (loaded from teams.json)
│   │   ├── export.py             # fig → PNG/SVG bytes, Instagram size presets
│   │   ├── composer.py           # place chart on a branded 1080×1350 canvas (title, logo…)
│   │   └── fonts.py              # resolve fonts relative to package (no absolute paths)
│   ├── studio/                   # BI Studio (today: bi_studio/)
│   │   ├── brand.py              # NAVY/CYAN, tagline, logo, fonts: shared by posts AND charts
│   │   ├── registry.py           # template registry: name → fields + render()
│   │   ├── primitives.py         # spaced text, fit-to-width text, crest badge, gradients
│   │   └── templates/
│   │       ├── team_ranking.py
│   │       ├── player_top5.py
│   │       └── chart_post.py     # NEW: wrap any chart from the Charts section in the brand frame
│   └── cli.py                    # batch generation from the command line (replaces main.py)
│
├── assets/
│   ├── fonts/                    # Roboto + Montserrat + Bebas Neue (one place)
│   ├── logos/                    # Botola Insights logos (moved from botola_insights_app/assets)
│   ├── crests/                   # club crests (moved from bi_studio/assets/crests)
│   └── teams.json                # ONE club file: names, crest, colors, crest crop (used by charts too)
├── samples/                      # small sample JSON/CSV per chart (for demo + tests)
├── tests/                        # pytest: parsers + smoke-render every chart
├── .streamlit/config.toml        # brand theme for the UI
├── pyproject.toml                # single source of deps + ruff/pytest config
└── README.md
```

**Design principles**
- **Keep the Streamlit entry script at the project root** (`streamlit_app.py`). Streamlit only
  hot-reloads modules inside the entry script's folder; an entry in a subfolder (like
  `botola_insights_app/app.py` or `app/main.py`) leaves `bi_studio/` and `charts/` stale after edits.
- **Separate the UI from the plotting.** Chart classes take clean data and options and return
  a `matplotlib.figure.Figure`. They never call `plt.show()`, `savefig()`, or Streamlit.
- **One parser per data source.** Column renaming and coordinate flipping happen once in
  `parsers/`, not in every chart.
- **Shared theme.** Fonts, colors, and text styles come from `core/theme.py`, so all posts
  look like one series.
- **Export is a concern of its own.** Every chart goes through the same export and composer
  path, so Instagram sizing is handled in one place.

---

## 2. Phases and steps

### Phase 1: Safety and cleanup (no visible changes)
1. ✅ `.env` removed. Still to do: purge it from git history (see `personal_notes.txt`).
2. Delete the dead code listed in §0 (duplicate shotmaps, `main.py`, DB layer, pizza and
   goalkeeper stubs, `json_tool`, unused methods, `__main__` demos, duplicate font, committed PNGs).
3. ✅ One pinned `requirements.txt` at the root (tested on Python 3.11).
4. Fix `.gitignore` (keep ignoring generated `images/` and `logs/`, but allow `samples/*.json`).
5. Add `ruff` (lint + format) and a minimal `pytest` setup.

**Done when:** the app runs exactly as before from a fresh venv, with no secrets in the repo.

### Phase 2: Restructure into the target architecture
1. Create the `botola_viz` package and move the 5 chart classes into it. Keep only the
   methods the app uses and rename them to a single `render()` (or `draw()`).
2. Introduce `BaseChart` (figure size, theme, transparent background, font loading, `close()`).
3. Move all Sofascore parsing into `parsers/sofascore.py`:
   - keep the real `xg` / `xgot` (optional "uniform marker size" toggle in the UI instead),
   - no input mutation, no `SettingWithCopyWarning`, no `print`,
   - schema validation with clear error messages ("missing key `shotmap`").
4. Load fonts relative to the package (fixes the absolute radar font path).
5. Split `app.py` into `app/main.py` + `app/pages/*` + `app/components/*`.
6. Replace `sys.path.append` hacks with proper package imports.
7. Replace `print` with `logging` and configure it once in `app/main.py`.

**Done when:** the same 5 charts render identically and every module imports cleanly.

### Phase 3: Bug fixes and chart improvements
1. **All charts:** close figures after rendering, never call `plt.show()`, and replace
   `cm.get_cmap` with `matplotlib.colormaps[...]`.
2. **Shot map:** real xG sizing; legend (goal / on target / off target; size = xG); filters by
   half, by situation (open play / set piece / penalty), and optional "exclude penalties";
   optional team names and xG totals.
3. **Goal location:** fix labels; add a **Player / Goalkeeper** mode (the existing
   `player_type="goal_keeper"` logic plus the TODO in the app); filter by team and player.
4. **Radar:** custom min/max per metric (default: sensible scale, not max-of-two), legend with
   player names, optional value labels, configurable ring and background colors.
5. **Match stats bar:** draw metric names and values on the chart; fix the label/value order
   mismatch; enter values in an editable table (`st.data_editor`) instead of 12 text boxes;
   let users add or remove metrics.
6. **Heatmap:** expose smoothing (Gaussian sigma) and pitch orientation, plus color-palette presets.

### Phase 4: UI overhaul
1. `st.set_page_config(layout="wide", page_title="Botola Insights Studio", page_icon=logo)`.
2. Brand theme in `.streamlit/config.toml` (Botola Insights red/blue, dark background).
3. Sidebar navigation (`st.navigation`) instead of tabs, with the logo at the top.
4. A consistent **two-column layout** on every page: **controls on the left, live preview on
   the right**, with the export panel under the preview.
5. One reusable **data input** component: Upload file / Paste JSON / **Load sample**, with
   inline validation errors (`st.error`) instead of crashes and a collapsible data preview table.
6. **Team color presets:** pick "Raja" / "Wydad" / "AS FAR" etc. from `teams.json`, which
   auto-fills home and away colors (still overridable with color pickers). Clear labels such
   as "Home color" and "Away color".
7. Cache parsing with `st.cache_data` so color tweaks don't re-parse the input.
8. Fix all copy and typos, and add short help tooltips for each control.

### Phase 5: New utilities for Instagram production
1. **Export presets** (`core/export.py`): Instagram portrait **1080×1350**, square 1080×1080,
   story/reel 1080×1920, or "chart only (transparent)". PNG and SVG, and a selectable DPI.
2. **Post composer** (now Phase 7.5, built on BI Studio's brand): place the chart on a branded canvas with title,
   subtitle (e.g. "Raja 2-1 Wydad · Botola Pro J12"), Botola Insights logo, data-source credit,
   and an optional background color/gradient. This is the ready-to-post image.
3. **Smart file names:** `shotmap_raja-vs-wydad_2026-10-25.png` instead of `Shootmap.png`.
4. **Batch mode:**
   - multi-file upload to build a **player shot map / goal-location map over several matches**
     (covers the existing TODOs and what `batch_shootmap.py` was for),
   - "Download all" as a ZIP.
5. **CLI** (`python -m botola_viz.cli shotmap match.json --preset ig-portrait -o out/`) for
   scripted generation, replacing the old commented-out `main.py`.
6. **Sample data** in `samples/` so every page can be demoed in one click.

### Phase 6: Quality and docs
1. `pytest` tests: parser unit tests plus a smoke test that renders every chart from `samples/`.
2. Optional GitHub Action: ruff + pytest on push.
3. `README.md`: setup, running the app, input formats for each chart, and how to add a new
   chart or team preset.

### Phase 7: BI Studio (post templates)
Current state: two Pillow templates (**Team ranking**, **Player top 5**) in `bi_studio/render.py`,
UI in `bi_studio/page.py`, clubs in `bi_studio/teams.json`. Clean code that works as it is.
Since more templates will be added, the goal is to make **adding a template a one-file job**.

1. ✅ **Template registry.** Each template is one module that declares its fields (title, table
   columns, photo, …) and a `render(**fields) -> Image`. The page builds the form from the
   declaration, so a new template needs no UI code.
2. ✅ **Shared brand module.** Move `NAVY`, `CYAN`, the tagline, the logo, the fonts, and the
   helpers (`_spaced`, gradients, crest badge) out of `render.py` into `brand.py` /
   `primitives.py`, so new templates reuse them instead of copying.
3. ✅ **Text that fits.** Long team or player names currently run into the value column (no
   width check). Add a `fit_text()` helper that shrinks the font or truncates to a max width.
4. **One `teams.json` for the whole project.** The charts use the same club colors (shot map
   home/away presets), and crests and colors live in one place.
5. **"Chart post" template.** Take any chart from the Charts section (shot map, heatmap, radar…)
   and place it in the BI Studio frame (logo, title, subtitle, tagline). This connects the
   two halves of the app and replaces the "post composer" from Phase 5.2.
6. **Productivity:**
   - paste or upload a CSV into the ranking table (copy from Sofascore/FBref),
   - "Sort by value" and number formatting (decimals, %),
   - **save/load a post** as JSON (re-edit last week's post; remember a photo's zoom/x/y per player),
   - "Download all" as a ZIP when making a series,
   - optional Instagram caption + hashtags generator next to the download button.
7. **Snapshot tests.** Render each template from fixed inputs and compare with a reference PNG,
   so refactors never silently change a post.

---

## 3. Suggested order and size

| Phase | Effort | Risk | Depends on |
|---|---|---|---|
| 1. Safety and cleanup | S | Low | none |
| 2. Restructure | M | Medium (big moves) | 1 |
| 3. Bug fixes and charts | M | Low | 2 |
| 4. UI overhaul | M | Low | 2 |
| 5. Instagram utilities | M–L | Low | 2 (3 and 4 recommended) |
| 6. Quality and docs | S | Low | ongoing |
| 7. BI Studio templates | M | Low | 1 (7.5 needs 2) |

Each phase gets its own commit or PR on top of `dev`.

---

## 4. Open questions (please confirm before I start)

1. **Database:** the Azure SQL path is fully stubbed out. Remove it completely (proposed), or
   keep it for a future "load match from DB" feature?
2. **Pizza chart and passing network:** delete (proposed), or revive them as new pages with
   CSV/JSON input?
3. **Brand:** which colors and fonts should the theme and composer use? (Logos exist in red and
   blue; the current charts use Roboto.)
4. **Post composer / chart post:** should charts get a BI Studio "chart post" template
   (Phase 7.5), or will you keep exporting transparent charts and finishing them elsewhere?
5. **Deployment:** is the app hosted (e.g. Streamlit Community Cloud) or only run locally?
   This affects the Python version pin.
