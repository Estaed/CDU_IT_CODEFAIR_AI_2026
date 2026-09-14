# Task-46: Visual identity: logo, page icons, dark sidebar, contrast, legend

Status: TODO

> **Execution:** agent `claude` · effort `high` · plan mode **no**
> *Why:* Tarik (2026-09-14): "more colour, a real identity, logos and icons", still a government internal tool. The direction is fixed by `reports/research-ui-visual-examples-2026-09-14.md` ("Recommended visual direction"): dark sidebar chrome through `[theme.sidebar]` keys, white canvas, terracotta used structurally, a text-based wordmark (no crest), bundled Material icons.

**Lane**
- OWNS: `.streamlit/config.toml`, `fair_turn/app/static/theme.css`, `fair_turn/app/static/logo.svg` (new), `fair_turn/app/static/logo-mark.svg` (new), `fair_turn/app/theme.py`, `fair_turn/app/main.py`, `tests/test_theme.py`, `tests/test_app_smoke.py`
- MUST NOT TOUCH: `fair_turn/app/pages/`, `fair_turn/app/components/`, `fair_turn/core/`, `design/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 40

## Objective

The app gets a recognisable identity with zero JavaScript and no downloaded asset: a dark
sidebar with the wordmark and icon-led navigation, a white working canvas, one accent in a
few fixed places, greys that do distinct jobs, and a legend that names what colours mean.

## Execution Guide

- `.streamlit/config.toml` `[theme.sidebar]`: `backgroundColor = "#161616"`, `textColor =
  "#f4f4f4"`, `secondaryBackgroundColor = "#262626"`, `borderColor = "#393939"`, `primaryColor =
  "#b4462a"`. Verify each key exists in `streamlit.config._config_options_template`
  (45 sidebar keys on 1.63; `showSidebarBorder` is app-level only, leave it where it is).
  `[theme]`: add `linkColor = "#b4462a"`. Every hex must be in `design/design-system/tokens.json`
  or `chart-palette.json` or already in `config.toml`; #262626 and #393939 are Carbon gray-90 /
  gray-80 — if they are absent from `tokens.json`, use the nearest token that is present and say
  so in NOTES (the theme test traces every hex to a token).
- Logo: `fair_turn/app/static/logo.svg` (wordmark, about 160×32 viewBox: a solid #b4462a square
  mark with one white diagonal cut, then "Fair Turn" in IBM Plex Sans SemiBold #f4f4f4 for the
  dark sidebar; use `font-family="IBM Plex Sans, sans-serif"` and `font-weight="600"`, no
  embedded font, no external reference) and `logo-mark.svg` (the square mark alone, 32×32).
  Hand-written SVG, under 25 lines each, no `<script>`, no `xlink:href` to a URL. `main.py`:
  `st.logo(<path to logo.svg>, size="large", icon_image=<path to logo-mark.svg>, link=None)`
  (verify the signature; paths through `pathlib` relative to `main.py`). Note the wordmark
  renders at 32 px tall at most.
- Navigation: `st.navigation({"Today's work": [workspace, review queue, visit plan], "Evidence":
  [tenant answer, evidence lab]})` with `st.Page(..., icon=":material/<name>:")`: workspace
  `dashboard`, review queue `rule`, visit plan `route`, tenant answer `question_answer`,
  evidence lab `analytics`. Material Symbols are bundled (`MaterialSymbols-Rounded.*.woff2`
  under `venv/Lib/site-packages/streamlit/static/static/media`); assert that in the theme test
  so the offline claim is checked, and pick names that exist in that font's set (any name from
  the Material Symbols Rounded set is fine; verify by rendering through AppTest that no
  exception is raised).
- `theme.css` (still the single stylesheet, under 60 lines, each selector commented "checked
  against Streamlit 1.63.0; unofficial"): (a) KPI tiles `[data-testid="stMetric"]` get a 3 px
  top rule in #b4462a and a #f4f4f4 fill; (b) secondary text: captions `[data-testid=
  "stCaptionContainer"]` in #525252 (raise contrast one step; #8d8d8d stays for disabled and
  meta only); (c) keep the existing tab underline and nav weight rules. No `url(`, no
  `@import`.
- Legend: `theme.py` gains `legend() -> None` rendering one `st.caption` line: "Colour key —
  class: Immediate red, Urgent orange, Routine grey · badges: Needs a human yellow, Set by
  coordinator grey · map: one dot per community, size = open jobs, colour = region." `main.py`
  renders it in the sidebar under the navigation (`with st.sidebar: theme.legend()`), so every
  page shows it without page edits.
- Tests: `tests/test_theme.py` — sidebar keys present and traced to tokens; both SVGs parse as
  XML, contain no `script`/`http`; the Material font file exists in the installed Streamlit;
  `theme.css` has no `url(`/`@import`. `tests/test_app_smoke.py` — `main.py` runs offline
  with the logo and grouped navigation (no exception; five pages registered; the legend caption
  present in the sidebar).

## Acceptance Criteria (DoD)

- [ ] Dark sidebar through `[theme.sidebar]` keys only; every hex traced to a token (test).
- [ ] Wordmark and mark SVGs, hand-written, offline; `st.logo` renders (smoke test).
- [ ] Grouped navigation with Material icons, offline (test asserts the bundled font).
- [ ] KPI tile rule and caption contrast in the single stylesheet; legend caption in the sidebar (tests).
- [ ] Gate green.
