# Task-40: Government chrome through theme keys, the one stylesheet seam, page intros

Status: DONE

> **Execution:** agent `codex` · effort `medium`
> *Why:* Blueprint Fidelity was amended 2026-09-14 to name the exact mechanism (theme keys, one `theme.css` via `st.html`); the copy is drafted in `reports/research-ui-hitl-guidance-2026-09-14.md`.

**Lane**
- OWNS: `.streamlit/config.toml`, `fair_turn/app/theme.py`, `fair_turn/app/static/theme.css` (new), `fair_turn/app/main.py`, `fair_turn/app/components/intro.py` (new), `fair_turn/app/pages/*.py` (only: one `intro.purpose(...)` call under the title, one `intro.about()` call at the end), `tests/test_theme.py`, `tests/test_app_smoke.py`
- MUST NOT TOUCH: any other component, `fair_turn/core/`, `fair_turn/data/`, `design/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: none

## Objective

Make the app read as a government internal tool and say on every page what it is for, with
zero JavaScript: `[theme]` keys first, one scoped stylesheet second, and a shared intro
component carrying the purpose lines and the "About this AI" footer.

## Execution Guide

- `.streamlit/config.toml`: keep every existing value. Add, after verifying each key exists in
  the installed Streamlit (`from streamlit.config import _config_options` or
  `venv/Scripts/streamlit config show`; drop any key that does not exist and say so in NOTES):
  `[theme.sidebar] backgroundColor = "#f4f4f4"` (surface-1 from `tokens.json`), `borderColor`
  as the main border, `showSidebarBorder = true`, `showWidgetBorder = true`,
  `dataframeHeaderBackgroundColor = "#f4f4f4"`, `dataframeBorderColor = "#e0e0e0"`,
  `headingFontSizes` with a smaller h1 (about 1.75rem; the current 42 px title dominates the
  page), `baseFontSize = 15`, `metricValueFontSize` if it exists. Every hex must already be in
  `design/design-system/tokens.json`; cite the token name in a TOML comment.
- `fair_turn/app/static/theme.css` (new, under 40 lines, LF): the active tab underline and tab
  text in the primary colour, the sidebar nav's active item weight 600, metric label size.
  Each selector carries a comment "checked against Streamlit 1.63.0; unofficial". No
  `@import`, no `url(`.
- `theme.py`: `inject_css()` reads `theme.css` with `pathlib` (`read_text("utf-8")`) and calls
  `st.html(f"<style>{css}</style>")`; `main.py` calls it once after `set_page_config`. Keep
  `layout="wide"`; set `initial_sidebar_state="expanded"`. Remove the
  `st.sidebar.caption(theme.PROVENANCE_LINE)` in `main.py` (every page already prints the
  caption under its title, so it showed twice).
- `components/intro.py` (new): `COPY: dict[str, str]` keyed by page (`workspace`,
  `review_queue`, `visit_plan`, `tenant`, `evidence_lab`, `about`) with exactly these texts:
  workspace "Fair Turn reads today's repair reports and puts them in a suggested order. You decide the order that is signed. Nothing here is sent to a crew until you sign it."
  review_queue "Some reports do not say enough for the system to fill a field. Those jobs come here so a person can fill it in. The system never fills a field on its own."
  visit_plan "This is the run sheet for the jobs you signed. The order is yours. Distance suggestions are only suggestions, and each one shows its reason."
  tenant "Here is where your repair sits today, and what moved it there. A housing officer checked and signed this list."
  evidence_lab "This page shows how well the system reads reports, measured on the synthetic set. It shows what it gets wrong as well as what it gets right."
  about "Fair Turn reads free-text repair reports and suggests an order. It does not approve, refuse or schedule a repair. A housing coordinator decides and signs. Every decision is logged with who made it and when. The data in this demo is made up. The geography is real (BushTel/ABS)." (all six strings measured 2026-09-14 with `core.wording.check`: no findings; the earlier About text scored FK 7.62 and was rewritten)
  `purpose(page)` renders `st.markdown(COPY[page])` directly under the title;
  `about()` renders `st.expander("About this AI")` with `COPY["about"]` at the end of the page.
  Run every string through `core.wording.check` in a test (no deficit language, FK grade at most 7).
- Pages: insert the two calls; change nothing else in the pages (Tasks 38 and 39 own their
  bodies). `tenant.py`'s title stays as is (Task-39 renames it).
- Tests: `tests/test_theme.py` adds (a) every hex in `config.toml` and `theme.css` appears in
  `tokens.json` or `chart-palette.json`; (b) no module under `fair_turn/app` except `theme.py`
  calls `st.html` with `<style` or passes `unsafe_allow_html`; (c) `theme.css` has no `url(` or
  `@import`. `tests/test_app_smoke.py` asserts on every page: one `html` node (`at.get("html")`)
  whose body contains `<style>`, the purpose text, and an "About this AI" status/expander node
  (`st.expander` emits a `status` node on 1.63; find it through `at.get("status")` or the
  markdown it contains).

## Acceptance Criteria (DoD)

- [ ] Theme keys verified against the installed build; every hex traced to a design token (test).
- [ ] One stylesheet, injected once through `st.html`; no other module injects CSS (test).
- [ ] Every page carries its purpose line and the About expander; sidebar caption no longer duplicated (smoke test).
- [ ] All copy passes the wording check.
- [ ] Gate green.
