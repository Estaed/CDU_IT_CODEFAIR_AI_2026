# Research — Streamlit 1.63 presentation toolkit, pydeck markers, government UI conventions

Checked 2026-09-14. Scope: what Fair Turn can do to stop looking like a bare demo, without an npm
build, without a custom component, and without breaking the offline AppTest gate.

**Source classes used.** (A) The installed packages themselves — `venv/Lib/site-packages/streamlit`
1.63.0 and `pydeck` 0.9.3, introspected and executed on this machine on 2026-09-14. This is the
strongest evidence available: it is the exact code the gate runs. (B) docs.streamlit.io, fetched
2026-09-14. (C) Release notes pages for 2025 and 2026, fetched 2026-09-14. (D) GOV.UK / NSW /
Design System AU pages, fetched 2026-09-14.

Where (A) and (B) disagree, both are reported. Nothing here has been applied to the repo.

---

## 1. Streamlit 1.63 presentation toolkit (no custom components)

**1.1 `st.metric` has `border`, `help`, `icon`, `chart_data`, `delta_description`, `format`.**
Verdict: **confirmed.** Live signature on this machine (A, 2026-09-14):
`st.metric(label, value, delta=None, delta_color='normal', *, help=None, icon=None,
label_visibility='visible', border=False, width='stretch', height='content', chart_data=None,
chart_type='line', delta_arrow='auto', format=None, delta_description=None)`.
Introduced: sparklines (`chart_data`) in **1.49.0, 2025-08-26**; `delta_description` in
**1.55.0, 2026-03-03**; `icon` in **1.61.0, 2026-08-04**; `delta_arrow` in **1.52.0, 2025-12-03**
(C). `border` is older than the 2025 notes and is present in 1.63 (A).
*For Fair Turn:* a KPI row is native. `st.metric(..., border=True)` gives the card outline with no
CSS at all; `chart_data` puts a sparkline inside the tile without a second chart element.

**1.2 `column_config` supports `ProgressColumn`, `BarChartColumn`, `LineChartColumn`,
`NumberColumn(format=...)`, per-column `width`, `pinned`, `alignment`, `help`.**
Verdict: **confirmed.** Live signatures (A): every one of these takes `width`, `help`, `pinned`;
`NumberColumn` and `ProgressColumn` take `format`, `min_value`, `max_value`; `ProgressColumn`,
`BarChartColumn`, `LineChartColumn` take `color`; `NumberColumn`/`TextColumn`/`Column` take
`alignment`. Full type list present in 1.63: Area/Audio/BarChart/Button/Checkbox/Column/Date/
Datetime/Image/Json/LineChart/Link/List/Markdown/Multiselect/Number/Progress/Selectbox/Text/Time/
Video. Introduced: `pinned` and pixel `width` in **1.47.0, 2025-07-16**; `ProgressColumn(color=)`
in **1.51.0, 2025-10-29**; `alignment` in **1.56.0, 2026-03-31**; `MarkdownColumn` in
**1.59.0, 2026-07-06**; `ButtonColumn` in **1.59.0** (C).
*Contradiction to report:* the concept page "Working with dataframes" (B, fetched 2026-09-14) says
pinning is a *user* action via the header menu and "does not mention `row_height` or explicit
column width parameters" — it is out of date relative to the API reference and the installed code.
Trust (A).
*For Fair Turn:* the horizontal-scroll problem is solvable without hiding columns —
`pinned=True` on the job id and the "needs a human" flag, `ProgressColumn` for the score (a bar
instead of six decimal places), `width="small"` on the rest, `column_order` to drop what the
coordinator never reads.

**1.3 `st.dataframe` has `row_height`, `hide_index`, `column_order`, `on_select`,
`selection_mode`, `placeholder`, `lazy`, `height="auto"`.**
Verdict: **confirmed** (A). `row_height` introduced **1.43.0, 2025-03-04**; cell selections
**1.49.0, 2025-08-26**; `placeholder` **1.52.0, 2025-12-03**; `lazy` **1.61.0, 2026-08-04**;
`"single-row-required"` selection mode **1.56.0, 2026-03-31** (C). Practical limit: Streamlit
disables column sorting above **150,000 rows** (B).
*For Fair Turn:* `row_height` raised slightly plus `hide_index=True` is the cheapest density fix.
`selection_mode="single-row-required"` is worth a look — it would remove the "page opens with an
empty details pane" state entirely by forcing a row to be selected.

**1.4 `st.badge` exists, but AppTest does not expose it as a badge.**
Verdict: **confirmed, with a trap.** `st.badge(label, *, icon=None, color=..., width, help)` (A);
introduced **1.44.0, 2025-03-25**; tooltip support added **1.52.0, 2025-12-03** (C). Colours:
red, orange, yellow, blue, green, violet, gray/grey, primary.
**Trap (A, measured 2026-09-14):** in the AppTest element tree `st.badge` appears as a **`markdown`**
node whose body is the directive `':red-badge[:material/warning: Needs a human]'`. `at.badge` raises
`AttributeError`. A test asserting on a badge must assert on markdown text containing `-badge[`.
*For Fair Turn:* `st.badge` is the right element for "Set by coordinator" and "Needs a human", and
it is free. But Part 2's verification rules currently assume elements are addressable by name — a
badge assertion has to go through `at.markdown`.

**1.5 `st.container(border=True, height=..., horizontal=..., gap=..., vertical_alignment=...)`.**
Verdict: **confirmed** (A): `st.container(*, border=None, key=None, width='stretch',
height='content', horizontal=False, wrap=True, horizontal_alignment='left',
vertical_alignment='top', gap='small', autoscroll=None)`. Horizontal flex containers introduced
**1.48.0, 2025-08-05**; `width="content"` **1.52.0, 2025-12-03**; `autoscroll` **1.56.0** (C).
Official guidance (B, 2026-09-14): `st.container(border=True)` is the card; `horizontal=True` is
**preferred over `st.columns`** because "elements in a horizontal container size themselves based
on their content"; "Set `height` on a container to a pixel value to create a scrollable region."
**AppTest note (A):** both bordered and horizontal containers emit node type `flex_container`.
*For Fair Turn:* this is the card system. No CSS needed for the selected-job pane, the sign-off
block, or the Evidence-lab metric groups.

**1.6 `st.columns(gap=..., vertical_alignment=..., border=..., wrap=...)`.**
Verdict: **confirmed** (A). `border` and `vertical_alignment` present; `gap` accepts
`"xxsmall"`…`"xxlarge"`, and pixel values since **1.60.0, 2026-07-21**; `gap=None` since
**1.46.0, 2025-06-18** (C). AppTest tree: `flex_container` → `column` nodes; `at.columns` works.

**1.7 `st.space` exists in 1.63.**
Verdict: **confirmed.** `st.space(size='small')`, sizes `xxsmall`(0.25rem)…`xxlarge`, `"stretch"`,
or an int; "adds space in the direction of its parent container" (A, docstring). Introduced
**1.51.0, 2025-10-29** (C). AppTest node type: `space` (A).

**1.8 `st.segmented_control` and `st.pills`.**
Verdict: **confirmed** (A), both with `selection_mode`, `required`, `format_func`, `width`,
`wrap`, `bind`, `persist_state`. `required` added **1.56.0, 2026-03-31**; `wrap` added
**1.63.0, 2026-09-01** (C). AppTest: node type `button_group`; accessors `at.segmented_control`
and `at.pills` both resolve (A).
*For Fair Turn:* replaces selectboxes for region / safety-class filters — one click, visible state,
and it reads like a filter bar rather than a form.

**1.9 `st.html` renders `<style>`; it is NOT stripped.**
Verdict: **confirmed, two independent sources.**
(i) Docstring (A): "If `body` is a `Path` to a CSS file, Streamlit will wrap the CSS content in
`<style>` tags automatically. When the resulting HTML content only contains style tags, Streamlit
will send the content to the event container instead of the main container to avoid taking up
space in the app." CSS-file-path support introduced **1.45.0, 2025-04-29** (C).
(ii) The shipped frontend bundle (A, grep of `venv/.../streamlit/static/static/js`, 2026-09-14):
the `stHtml` component's DOMPurify config is literally
`{...s, ADD_TAGS:["script","style"], ADD_ATTR:["src","type","async","defer","nonce","crossorigin","referrerpolicy","integrity"]}`.
`style` is explicitly **added** to the allowlist. The one `FORBID_TAGS:["style"]` in the bundle
belongs to the Mermaid renderer, not to `st.html`.
JavaScript is ignored unless `unsafe_allow_javascript=True` (added **1.52.0, 2025-12-03**, C).
**AppTest behaviour (A, measured):** a style-only `st.html` does **not** appear in `at.main`'s
children, but `at.get("html")` **does** return it (returned 2 html elements for one div + one
style block). There is no `at.html` accessor — `AttributeError`. So a CSS injection is invisible
to a tree walk but assertable via `at.get("html")`.
*For Fair Turn:* limited scoped CSS is available and is AppTest-safe, provided tests use
`at.get("html")` and do not assume element counts in `at.main`.

**1.10 `st.markdown(unsafe_allow_html=True)` with `<style>` also works but takes up space.**
Verdict: **confirmed** (A, measured): the style block appears as a `markdown` node **inside the
main tree**, i.e. it occupies a slot in the layout and shifts every index-based assertion.
*For Fair Turn:* if CSS is used at all, use `st.html`, not `st.markdown`. This is the difference
between an invisible injection and one that adds a phantom element to every page's tree.

**1.11 `st.page_link`, `st.status`, `st.expander`, `st.divider`, `st.caption`, `st.title(anchor)`,
`st.toast`.** Verdict: **confirmed** (A), all present with the parameters asked about:
`expander(label, expanded=False, *, key, icon, type, width, on_change)`,
`status(label, *, expanded, state, type, width)`, `title(body, anchor, *, help, icon, width,
text_alignment, wrap)`, `caption(body, unsafe_allow_html, *, help, width, text_alignment, wrap)`,
`toast(body, *, icon, duration)`, `divider(*, width)`,
`page_link(page, *, label, icon, icon_position, help, disabled, width, query_params)`.
`icon` on `st.title/header/subheader` is new in **1.63.0, 2026-09-01**; `type="step"` on expander
and status is new in **1.63.0**; `type` (compact) in **1.58.0, 2026-05-28**; `toast(duration)` in
**1.49.0, 2025-08-26**; `page_link(query_params)` in **1.52.0** (C).
**Two traps (A, measured 2026-09-14):**
- `st.expander` emits node type **`status`**, not `expander`. `at.expander` returned **0** while
  `at.status` returned **2** (one real `st.status`, one `st.expander`). Expanders and statuses are
  the same element in 1.63.
- `st.page_link` raises `StreamlitPageNotFoundError` unless the target was declared via `st.Page`
  and passed to `st.navigation`. It cannot link to an arbitrary file path.

**1.12 `st.navigation(position="top")`, sections, icons; `st.logo`.**
Verdict: **confirmed** (A): `st.navigation(pages, *, position='sidebar'|'hidden'|'top',
expanded=False)`; `pages` may be a `Mapping[SectionHeader, Sequence[Page]]`, which is how sections
are declared. `st.logo(image, *, size='small'|'medium'|'large', link=None, icon_image=None)`.
`position="top"` introduced **1.46.0, 2025-06-18**; `expanded` on navigation **1.56.0, 2026-03-31**;
Material icons/emoji in `st.logo` **1.54.0, 2026-02-04**; markdown in section labels
**1.55.0, 2026-03-03** (C).

**1.13 `st.set_page_config(layout="wide")`, sidebar width, `initial_sidebar_state="locked"`.**
Verdict: **confirmed** (A, docstring read on this machine). `initial_sidebar_state` accepts
`"auto" | "expanded" | "collapsed" | "locked" | int | None`; an **int sets the sidebar's starting
width in pixels and must be between 200 and 600 inclusive**. `"locked"` = expanded on desktop with
collapse controls hidden, degrading to collapsed on narrow viewports. `"locked"` introduced
**1.59.0, 2026-07-06**; sidebar width via `set_page_config` **1.53.0, 2026-01-14** (C).
Confirmed independently by the API reference page (B, 2026-09-14).
*For Fair Turn:* there is **no** separate `sidebar_width` parameter — it is the same argument. A
coordinator tool wants `layout="wide"` and `initial_sidebar_state="locked"` so the navigation
cannot be closed mid-demo.

**1.14 `st.dialog` limitations.** Verdict: **confirmed and unchanged.**
`st.dialog(title, *, width='small', dismissible=True, icon=None, on_dismiss='ignore')` (A).
Part 2 already records the blocking fact: AppTest's element tree has no dialog node. Nothing in
1.53–1.63 changes that (C). The in-page-container decision stands.

**1.15 `[theme]` config keys valid in 1.63.**
Verdict: **confirmed by enumeration.** 277 theme options are registered in the installed build (A,
`streamlit.config._config_options_template`, 2026-09-14). Every key the brief asked about exists at
top level: `baseFontSize`, `baseFontWeight`, `baseRadius`, `borderColor`, `buttonRadius`,
`chartCategoricalColors`, `chartDivergingColors`, `chartSequentialColors`, `codeBackgroundColor`,
`codeFont`, `codeFontSize`, `codeFontWeight`, `codeTextColor`, `dataframeBorderColor`,
`dataframeHeaderBackgroundColor`, `font`, `fontFaces`, `headingFont`, `headingFontSizes`,
`headingFontWeights`, `linkColor`, `linkUnderline`, `showSidebarBorder`, `showWidgetBorder`,
`primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, plus the full named
colour set (`red|orange|yellow|green|blue|violet|gray` × `Color|TextColor|BackgroundColor`).
Two keys the brief did **not** list and which matter here: **`theme.metricValueFontSize`** and
**`theme.metricValueFontWeight`** (added **1.55.0, 2026-03-03**, C).
The same keys are available scoped as `[theme.light]`, `[theme.dark]`, `[theme.sidebar]`,
`[theme.light.sidebar]`, `[theme.dark.sidebar]`. Advanced theming introduced **1.44.0/1.47.0**
(2025-03-25 / 2025-07-16); light+dark simultaneously **1.51.0, 2025-10-29**;
`dataframeBorderColor` and `buttonRadius` **1.46.0, 2025-06-18** (C).
*For Fair Turn:* the sidebar can be styled independently of the main area (`[theme.sidebar]
backgroundColor`) with **no CSS at all**. That single key is most of the "government tool" look.

---

## 2. Does CSS injection need the network?

**Claim: injecting CSS via `st.html`/`st.markdown` requires no network request.**
Verdict: **confirmed**, with one caveat. The CSS string is serialised into the element proto and
sanitised client-side by the DOMPurify already bundled in `streamlit/static` (A, §1.9). No fetch is
involved. Fair Turn's smoke test patches `socket.socket` to raise; an inline `<style>` never touches
it.
**Caveat / the one way to break it:** any `@import url(...)`, `url(https://...)` background, or
`@font-face { src: url(https://fonts.gstatic.com/...) }` inside that CSS *is* a browser fetch. It
would not fail the gate (the gate refuses sockets in the **server** process, not the browser), so
this is a silent offline break — exactly the class of failure Part 2's network rule exists to
prevent. Fair Turn already vendors IBM Plex through `theme.fontFaces`, so no font import is needed.
**Known strip trap:** none for `<style>` (§1.9, allowlisted by name). `<script>` is passed to
DOMPurify's allowlist too but is **not executed** unless `unsafe_allow_javascript=True` — so a
`<script>` will silently do nothing, which is a trap only if someone expects otherwise.

---

## 3. pydeck 0.9.3 / deck.gl ScatterplotLayer

**3.1 The marker-size props exist and reach deck.gl.**
Verdict: **confirmed.** `radiusMinPixels`, `radiusMaxPixels`, `radiusUnits`, `radiusScale`,
`lineWidthMinPixels`, `stroked` are all present in Streamlit's bundled deck.gl build (A, grep of
`static/js`, 2026-09-14: 9, 9, 18, 12, 19 and 43 occurrences respectively). `pydeck.Layer` takes
`**kwargs` and snake_cases them to camelCase, so any deck.gl prop passes through (A,
`pydeck/bindings/layer.py`).

**3.2 THE TRAP: pydeck turns every plain string kwarg into a data accessor.**
Verdict: **confirmed by reading the source and by executing it (A, 2026-09-14).** In
`pydeck/bindings/layer.py` (line 99–101), `elif isinstance(v, str): kwargs[k] = FUNCTION_IDENTIFIER + v`
where `FUNCTION_IDENTIFIER = "@@="`. Measured output:

```
Layer('ScatterplotLayer', radius_units='pixels', ...)  ->  "radiusUnits": "@@=pixels"
```

deck.gl reads `@@=` as a JS expression over the row, so `radius_units="pixels"` is sent as an
*accessor for a column named `pixels`*, not the literal string. The layer silently falls back to
metre units — which is precisely Fair Turn's symptom: markers invisible at NT zoom, then a single
marker swallowing a town when you zoom in.
**The fix, verified:** wrap the literal in quote characters. Lines 93–95 strip a matching
leading/trailing quote and pass the bare string. Measured:

```
radius_units="'pixels'"      ->  "radiusUnits": "pixels"       (correct)
size_units="'pixels'", get_alignment_baseline="'top'"  ->  "sizeUnits": "pixels", "getAlignmentBaseline": "top"
```

*For Fair Turn:* this is the single highest-value finding in this report. It is a one-character-class
change per prop and it fixes the map.

**3.3 Fixed pixel size at all zooms.**
Verdict: **confirmed** (mechanism, from the props above). Set `radius_units="'pixels'"` and
`get_radius` to the pixel radius; or keep metres and clamp with `radius_min_pixels` /
`radius_max_pixels`. Clamping alone (min 6 / max 14) also solves it and preserves a real-world
radius meaning. `line_width_min_pixels=1` with `stroked=True` keeps a 1 px outline at every zoom,
which is what makes small markers legible on a pale Carto basemap.
*Unknown:* which of the two reads better at NT extent — **TBD, needs validation** on screen.

**3.4 `TextLayer` for community ids.**
Verdict: **confirmed available.** `TextLayer` is in the bundle (A, 7 occurrences). Same `@@=` trap
applies to `size_units`, `get_alignment_baseline`, `get_text_anchor`, `font_family`. `get_text='id'`
is *correctly* an accessor and should stay unquoted.
*Caution:* deck.gl's TextLayer builds a font atlas in the browser from a local canvas — no network —
but labels on ~40 communities at NT extent will collide. TBD whether it reads.

**3.5 Cluster layers in pydeck 0.9.x.**
Verdict: **partially contradicted.** There is **no generic `ClusterLayer`** in the bundle. Present
and usable: `HexagonLayer`, `GridLayer` (aggregation layers), `IconLayer`, and from geo-layers
`H3HexagonLayer`, `H3ClusterLayer`, `MVTLayer`, `GeohashLayer`, `QuadkeyLayer`, `S2Layer`,
`GreatCircleLayer`, `TerrainLayer`, `Tile3DLayer` (A, grep 2026-09-14; the `ClusterLayer` hits are
`H3ClusterLayer`, which needs H3 indices, not lon/lat).
*For Fair Turn:* clustering is not worth it for a few dozen communities; aggregation would also hide
individual jobs, which is the opposite of what a coordinator needs.

**3.6 Carto `map_style` values.**
Verdict: **confirmed** (A, `pydeck.bindings.map_styles`, read 2026-09-14). Carto styles shipped:
`CARTO_LIGHT` → `https://basemaps.cartocdn.com/gl/positron-gl-style/style.json`;
`CARTO_DARK` → `dark-matter-gl-style`; `CARTO_ROAD` → `voyager-gl-style`; plus
`CARTO_LIGHT_NO_LABELS` and `CARTO_DARK_NO_LABELS`. **There is no Carto satellite style** —
`SATELLITE` resolves only under the Google and Mapbox providers, both of which need an API key.
`map_provider` defaults to `'carto'`; Carto became Streamlit's default tile provider in
**1.46.0, 2025-06-18** (C). Docs (B) note `map_style=None` aligns the map with the active Streamlit
theme, and that Carto keys are set via `Deck(api_keys={"carto": ...})` or `CARTO_API_KEY` — not
required for the public basemap styles.
**Attribution:** the Carto vector style JSONs carry their own `attribution` fields, which
MapLibre renders automatically in the map corner; deck.gl does not strip them. Fair Turn does not
need to hand-write attribution as long as the attribution control is not hidden.
*Unverified:* whether Carto's terms require additional visible credit for a non-commercial demo —
**TBD, needs validation** against Carto's basemap terms before the demo. Not checked here.

**3.7 `st.pydeck_chart` — `on_select`, `height`, `width`, zoom controls, tooltip.**
Verdict: **confirmed**, two sources. Live signature (A): `st.pydeck_chart(pydeck_obj=None, *,
width='stretch', use_container_width=None, height=500, selection_mode='single-object',
on_select='ignore', key=None)`. API reference (B, 2026-09-14): the returned `PydeckState` carries
`selection.indices` and `selection.objects`, both **`dict[str, list]` keyed by layer id** — so
**yes, selection is returned per layer, for every layer**, and "all layers must have a declared id
to keep the chart stateful". Docs also warn pydeck uses **two WebGL contexts per chart** and advise
"don't display more than eight Pydeck charts on a single page".
**Zoom controls exist natively:** the bundle contains `data-testid="stDeckGlJsonChartZoomButton"`
(A) — Streamlit renders its own +/− buttons over the deck.
`tooltip` accepts `{"html": ..., "style": {...}}`; the style dict is inline CSS on the tooltip div,
so it can carry Fair Turn's tokens without a stylesheet (A, verified in emitted JSON).
*For Fair Turn:* give the ScatterplotLayer an explicit stable `id` — pydeck otherwise generates a
random UUID per run (measured: `"id": "deb2b337-…"` changed between runs), which would make the
selection key unstable across reruns. That is a latent bug worth checking in the existing code.

---

## 4. Good-looking Streamlit dashboards — dated, credible, with the technique named

**4.1 Official: "Using layouts and containers", docs.streamlit.io (fetched 2026-09-14).**
Techniques quoted: `st.container(border=True)` as the card ("This has a border around it");
`st.container(horizontal=True)` preferred over `st.columns` because "elements in a horizontal
container size themselves based on their content"; "Set `height` on a container to a pixel value to
create a scrollable region"; `gap` from `"xxsmall"` to `"xxlarge"`; `st.space()` for manual gaps;
`horizontal_alignment="right"`; `st.columns([2, 1])` for unequal widths. No prescriptive dashboard
template is given — the page is explicit that structure is left to the author.

**4.2 Official: "How to build a real-time live dashboard with Streamlit", blog.streamlit.io.**
Techniques quoted (via search result summary, 2026-09-14; the article itself returned HTTP 403 to
automated fetch, so this is second-hand and should be re-read by a human): "divide your layout into
a 3 column layout by using `st.columns(3)`"; "`st.metric()` helps you create a KPI card"; the
`label`/`value`/`delta` split where delta compares against a goal; and for live updates, "put all
components inside a single-element container using `st.empty()`".
Verdict for the fetch: **unknown / degraded source.** Marked here because the technique is
corroborated by 4.1 and by the `st.metric` API itself, not because the page was read.

**4.3 Official: `st.metric` API reference (fetched 2026-09-14 indirectly via search).**
Technique: "add an icon before the label with the `icon` parameter"; "`st.metric()` supports
sparklines to show trends over time". Corroborates 1.1 from a second source.

**4.4 `streamlit-extras` — is it offline-safe?**
Verdict: **unknown — TBD, needs validation.** Search (2026-09-14) confirms it is a community
package on PyPI whose required dependencies include `plotly` and `streamlit`; no primary source was
found stating whether individual extras fetch from a CDN. Several well-known extras (`mention`,
`annotated_text`, `card`) build raw HTML strings, and some community card implementations pull
Google Fonts — which would be an offline break of exactly the kind described in §2.
**Recommendation regardless of the answer:** do not add it. Everything Fair Turn would have used it
for — bordered metric cards, badges, vertical space, a styled container — became native between
1.44 and 1.51 (C). Adding a dependency with an unaudited network story to a project whose gate
refuses sockets is a poor trade, and Part 2 already rejects dependencies on this reasoning.

**4.5 Release notes as design evidence, 2025-03-25 → 2026-09-01 (C).**
The direction of travel is explicit and worth stating: theming moved *out* of CSS
("Advanced theming: customize fonts, colors, and roundness **without CSS**", 1.47.0, 2025-07-16),
and layout moved from column arithmetic to flex containers (1.48.0, 2025-08-05). A 2026 app that
reaches for `unsafe_allow_html` for cards or spacing is using a 2023 idiom.

---

## 5. Empty state and onboarding patterns

**5.1 Official Streamlit guidance on empty states.**
Verdict: **unknown.** No dedicated empty-state or onboarding guidance page was found on
docs.streamlit.io on 2026-09-14. The building blocks exist and are documented individually;
the pattern is not prescribed. **TBD — needs validation** if a citable official pattern is wanted.

**5.2 The building blocks that do exist (all confirmed, A/C).**
- `st.dataframe(placeholder=...)` — text shown for null values (**1.52.0, 2025-12-03**).
- `st.skeleton` — animated loading placeholder (**1.59.0, 2026-07-06**). This is the closest
  native thing to a "preview of what will appear here".
- `help=` on every widget and on `st.metric`, `st.badge`, `st.title`, `st.caption` (A).
- `st.popover` for inline help without leaving the page; `type` parameter for button styling
  (**1.51.0, 2025-10-29**).
- `st.expander("How to use", icon=...)` — but see the §1.11 trap: it is a `status` node in AppTest.
- Alert elements gained a `title` parameter in **1.57.0, 2026-04-29** (C), so
  `st.info(body, title="Sign today's list first")` gives a headed banner natively.
- `st.container(border=True)` + `st.caption` is the cheapest "empty pane with an explanation".

**5.3 Cross-domain guidance that is citable: GOV.UK notification banner (fetched 2026-09-14).**
Quoted: use a banner for information "peripheral to the user's current task"; use headings like
"Success" "so that you're not relying on colour alone to convey meaning"; position it "immediately
before the page `<h1>`"; and the restraint warning — "there's evidence that people often miss them,
and using them too often is likely to make this problem worse"; never show a notification banner
and an error summary on the same page.
*For Fair Turn:* the "Sign today's list first" refusal is not a banner — it is the page's whole
content. It should be a bordered container holding a one-line reason, a disabled preview of the
plan table, and a `st.page_link` to the Workspace. A refusal that shows what it is refusing is the
difference between a bug and a designed state.

---

## 6. Making it look like a government internal tool

### 6(a) What the design systems actually say

**6a.1 GOV.UK Tag component (fetched 2026-09-14).** Purpose: "indicates the status of something".
Nine colours with assigned meanings: Grey (Inactive), Green (New), Teal (Active), Blue (Pending),
Purple (Received), Magenta (Sent), Red (Rejected), Orange (Declined), Yellow (Delayed). Two hard
rules quoted: tags must be **non-interactive** ("never make them into links or buttons"; use
adjectives, not verbs, so users do not read them as clickable), and "do not rely on colour alone to
convey information". Guidance on count: "start with the smallest number of statuses you think might
work, then add more if your user research shows there's a need". The page records a **brand refresh
in February 2026** that changed tag colour and styling "for improved contrast and visual distinction
from buttons".
*For Fair Turn:* `st.badge` is a tag. It must carry a word, not just a colour — "Needs a human",
"Set by coordinator", "Signed" — and must never be inside a button. Cap the set at three or four.

**6a.2 GOV.UK Summary list (fetched 2026-09-14).** A key–value list (`<dl>`) for "a user's
responses", paired with the Check answers pattern. Explicitly **not** for tabular data. Row actions
("Change") "rely on context from the surrounding content so may require additional accessible text"
— i.e. "Change name", not "Change". Summary **cards** are the variant for several similar lists.
*For Fair Turn:* the selected-job pane is a summary list, not a table and not prose. Field label on
the left, extracted value on the right, a "Set by coordinator" badge where a human overrode it, and
an empty row where verification failed. This maps exactly onto Fair Turn's constraint that an
unverified field renders empty.

**6a.3 GOV.UK type scale (fetched 2026-09-14).** Font: New Transport. Large screens: 48 / 36 / 24 /
19 / 16 px, with line heights 50 / 40 / 30 / 25 / 20 px — "all type scale points use line heights in
5px multiples to maintain consistent vertical rhythm". Body is **19 px**, not 16. The page
references GOV.UK Frontend **v6.0.0**; no explicit publication date shown.
*For Fair Turn:* the whole system is six sizes. `theme.baseFontSize` plus `theme.headingFontSizes`
can reproduce a restrained scale; the current default Streamlit scale is the "consumer product"
tell.

**6a.4 GOV.UK notification banner.** See §5.3 — restraint, heading not colour, one banner only.

**6a.5 NSW Design System (fetched 2026-09-14, designsystem.nsw.gov.au, version **3.27.0**).**
Confirmed: a toolkit "to help digital product teams create good customer experiences quickly";
core styles marked for brand compliance (Logo, Colour, Typography, Iconography, Pictograms, Graphic
elements, Grid, Layout, Section); 50+ components including tables, alerts, modals; plus "Methods"
for charts, maps, search and **easy-read formats**.
**Not confirmed:** the homepage did not state a WCAG target, font family, base size, or the status
colour set. **TBD — needs validation** against `designsystem.nsw.gov.au/accessibility` and its
typography page if NSW specifics are wanted. Note the old `digitalnsw.github.io/nsw-design-system`
URL now 301-redirects to the new domain.

**6a.6 Design System AU / GOLD (fetched 2026-09-14, designsystemau.org).**
Confirmed: GOLD ("Government Open Language for Design") **replaced the decommissioned Australian
Government Design System**; launch announced **2021-09-21**; code at `designsystemau/gold-design-system`
on GitHub and npm. The old `gold.designsystemau.org/about/principles/` URL 301-redirects to the
site root and the principles page no longer resolves.
**Not confirmed:** stated principles, WCAG target, typography, colour rules, component inventory —
none were on the page fetched. **TBD — needs validation** against the GitHub repo.
*Honest read:* GOLD is the weakest of the three as a citable source right now. GOV.UK is the one
with live, dated, specific guidance; it is also the system NSW and GOLD both descend from. For a
competition entry, citing GOV.UK patterns by name is defensible and checkable.

**6a.7 NT Government's own web style.** **Partially confirmed, weak.** Search (2026-09-14) surfaces
that the Territory's three official colours are **black, white and red ochre (PMS 159)**, and that
an NT Government branding style guide exists online. No primary NT design-system or web style
guide with typography and component specs was located. **TBD — needs validation.**
*For Fair Turn:* do not claim NTG brand compliance. A restrained neutral palette with one accent is
both safer and more honest than a half-matched ochre.

**6a.8 The accessibility bar — and a contradiction with the brief.**
The brief assumes **WCAG 2.1 AA**. Sources checked 2026-09-14 say otherwise:
the Australian Human Rights Commission **affirmed WCAG 2.2 Level AA as the minimum standard in
2025**, and the DTA's Digital Experience Policy standards apply to new sites from **2025-01-01**,
complementing the refreshed Digital Service Standard (10 criteria, including "Leave no one behind"
and "Do no harm"). Multiple secondary sources state all Australian Government websites and digital
services must comply with **WCAG 2.2 Level AA**.
**Contradiction reported, not resolved:** 2.1 AA (the brief) vs 2.2 AA (2025–2026 sources). The
primary DTA page `dataanddigital.gov.au/accessibility` **timed out** on fetch (2026-09-14) and was
not read, so the exact wording of the government's own commitment is **TBD — needs validation**.
Practically the gap is small for Fair Turn: 2.2 adds focus-appearance, target size (minimum),
dragging movements and consistent help. Note that Part 2 already accepts the design's Known Gap on
48 px touch targets — under 2.2 that maps to SC 2.5.8 Target Size (Minimum), 24×24 CSS px, which
Streamlit's own controls generally meet.
Underlying legal basis in both readings: the **Disability Discrimination Act 1992**.

### 6(b) What of that is reachable in Streamlit 1.63

**Reachable through `[theme]` alone — no CSS (all keys confirmed present, §1.15):**

| Want | Key |
|---|---|
| Sidebar as a distinct dark/neutral chrome | `[theme.sidebar] backgroundColor`, `textColor`, `primaryColor` |
| Sidebar hairline instead of shadow | `theme.showSidebarBorder` |
| One accent, everywhere | `theme.primaryColor` |
| Square corners (Carbon/GOV.UK-like) | `theme.baseRadius = 0`, `theme.buttonRadius = 0` |
| Restrained type scale | `theme.baseFontSize`, `theme.headingFontSizes`, `theme.headingFontWeights` |
| Quieter metric numerals | `theme.metricValueFontSize`, `theme.metricValueFontWeight` |
| Table header band + rules | `theme.dataframeHeaderBackgroundColor`, `theme.dataframeBorderColor` |
| Visible field outlines (form-like, not floaty) | `theme.showWidgetBorder`, `theme.borderColor` |
| Status colours that mean something | `theme.redColor`, `greenColor`, `orangeColor`, `blueColor`, `grayColor` (+ `*TextColor`, `*BackgroundColor`) — these are what `st.badge` renders |
| Chart palette | `theme.chartCategoricalColors`, `chartSequentialColors`, `chartDivergingColors` |
| Vendored IBM Plex | `theme.fontFaces`, `theme.font`, `theme.headingFont`, `theme.codeFont` |
| Link treatment | `theme.linkColor`, `theme.linkUnderline` |

That table covers sidebar background, heading weight/size, dataframe header, button shape,
container border and metric label size — **six of the seven properties the brief asked about,
without a single line of CSS.** The seventh, **tab underline colour**, has no dedicated theme key
and would need CSS.

**If CSS is used anyway — stable-ish selectors.** Streamlit ships `data-testid` attributes in the
production bundle (A, enumerated 2026-09-14). Relevant ones that exist today:
`stApp`, `stAppViewContainer`, `stMain`, `stMainBlockContainer`, `stHeader`, `stSidebar*`,
`stElementContainer`, `stVerticalBlock`/`stColumn`, `stDataFrame`, `stDataFrameGlideDataEditor`,
`stMetric`, `stMetricDelta`, `stMetricChart`, `stMarkdown`, `stMarkdownContainer`, `stHeading`,
`stHeadingDivider`, `stExpander`, `stExpanderDetails`, `stAlert`, `stAlertTitle`, `stButton`,
`stButtonGroup`, `stPopover`, `stHtml`, `stDeckGlJsonChart`, `stElementToolbar`.
**Warning, stated plainly:** these are **not a public API**. They are test hooks in a minified
bundle; they have been renamed before and Streamlit does not version them. Any CSS keyed to them is
a maintenance bet that survives exactly until the next upgrade, and it will fail *silently and
visually* — the gate will stay green while the page looks wrong. Given Part 2's rule that a silent
miss is what deserves a protocol, CSS keyed to `data-testid` should be the last resort, kept to a
handful of declarations in one file, and every declaration should degrade to "slightly less pretty",
never to "unreadable".

---

## Recommended changes for Fair Turn, ranked

1. **Fix the map markers: quote the literal string props.** `radius_units="'pixels'"` (note the
   inner quotes) plus `radius_min_pixels=6`, `radius_max_pixels=14`, `stroked=True`,
   `line_width_min_pixels=1` on the `ScatterplotLayer`. This is the 1–3 px / town-swallowing bug
   and it is a source-verified pydeck serialisation trap (§3.2).
2. **Give every pydeck layer an explicit `id=`.** pydeck generates a fresh UUID per run, and
   `st.pydeck_chart(on_select=...)` keys `selection.objects` by layer id (§3.7). Latent selection
   bug; check the existing code.
3. **Kill the horizontal scroll with `st.column_config`**, not by hiding columns: `pinned=True` on
   job id and the human-queue flag, `ProgressColumn` for the score, `NumberColumn(format=...)` for
   distance, `width="small"` elsewhere, `column_order=` to drop the rest, `hide_index=True`.
4. **Remove the empty details pane** with `st.dataframe(..., selection_mode="single-row-required")`,
   so the workspace opens on a selected job rather than on nothing.
5. **Set the government chrome with `[theme]` keys only:** `[theme.sidebar] backgroundColor`,
   `showSidebarBorder`, `baseRadius=0`, `buttonRadius=0`, `showWidgetBorder`, `borderColor`,
   `dataframeHeaderBackgroundColor`, `dataframeBorderColor`, `headingFontSizes`,
   `metricValueFontSize`. Zero CSS, one file, already the Part 2 token rule (§6b).
6. **A KPI row at the top of the Workspace and the Evidence lab:**
   `st.metric(label, value, delta=..., border=True, help=..., chart_data=...)` inside
   `st.container(horizontal=True)`. This is what turns the Evidence lab's wall of tables into a
   dashboard without a new chart grammar (§1.1, §4.1).
7. **Rebuild the selected-job pane as a GOV.UK summary list**: label/value rows in a
   `st.container(border=True)`, `st.badge` for "Set by coordinator" / "Needs a human", empty value
   where span verification failed. Matches Fair Turn's own constraint and a citable pattern (§6a.2).
8. **Make every refusal state show what it is refusing.** `st.container(border=True)` holding
   `st.info(body, title="Sign today's list first")`, a disabled preview of the plan table, and a
   `st.page_link` to the Workspace — not a bare sentence (§5.3).
9. **Replace filter selectboxes with `st.segmented_control` / `st.pills`** (`selection_mode`,
   `required=True`). One click, visible state, reads as a filter bar (§1.8).
10. **`st.set_page_config(layout="wide", initial_sidebar_state="locked")`**, plus `st.logo` and
    `st.navigation` with section headers. `"locked"` means the nav cannot be collapsed mid-demo;
    sidebar width is an int in the same argument, 200–600 px (§1.13, §1.12).
11. **Do not add `streamlit-extras`.** Everything it was wanted for is native since 1.44–1.51, and
    its CDN story is unverified against a socket-refusing gate (§4.4).
12. **If CSS is used at all, use `st.html` and never `st.markdown(unsafe_allow_html=True)`** — the
    former is invisible in the element tree (assert with `at.get("html")`, there is no `at.html`),
    the latter adds a phantom `markdown` node to every page (§1.9, §1.10). Keep it to the tab
    underline and nothing else; `data-testid` selectors are unofficial and fail silently (§6b).

**Two traps that will bite the test suite, whatever is decided:** `st.expander` emits a `status`
node (`at.expander` returns 0), and `st.badge` emits a `markdown` node (`at.badge` raises). Both
measured on this machine 2026-09-14 (§1.4, §1.11).

---

## Where this belongs

- **Part 2, stack table, "Why it is here" column — pydeck row.** The `@@=` string-accessor trap
  (§3.2) belongs beside the other CLI traps Part 2 already records. It is the same class of fact:
  something that silently produces wrong output and cost a debugging session. The explicit-layer-`id`
  requirement belongs with it.
- **Part 2, Fidelity & UI.** The `[theme]` key table in §6b is an extension of the existing "Tokens,
  defined once" rule, and the tab-underline exception is the one place that rule cannot reach.
  Whether limited `st.html` CSS is permitted at all is an **amendment to Key Constraints** and
  therefore the user's call, not an edit made in passing (Part 1 rule 8).
- **Part 2, Verification Rules, per-check detail.** The two AppTest node-type traps (§1.4, §1.11)
  and the `at.get("html")` access path change how assertions must be written. This is the kind of
  fact that belongs in the gate's documentation, not in a task file.
- **PRD open question.** The WCAG 2.1 vs 2.2 AA contradiction (§6a.8). Fair Turn is judged on trust;
  claiming the wrong conformance target in the report is worse than claiming none. Needs a decision
  and the DTA page needs a human read — it timed out here.
- **Nowhere (recorded and dropped).** Cluster layers (§3.5), Carto satellite (§3.6),
  `streamlit-extras` (§4.4), NSW/GOLD/NTG specifics beyond what is quoted (§6a.5–6a.7). Each is
  either unavailable, not needed, or not worth the dependency — noted so it is not re-proposed.

**Marked TBD, needs validation:** the DTA accessibility page's exact wording; Carto's attribution
terms for a non-commercial demo; whether pixel-radius or clamped-metre markers read better at NT
extent; whether TextLayer labels collide; `streamlit-extras` CDN behaviour; NSW/GOLD/NTG
typography and colour specifics.
