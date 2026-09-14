# Research — visual examples: government internal tools, Streamlit chrome, ranked-row lists, logo craft

Checked 2026-09-14. Companion to `reports/research-ui-streamlit-2026-09-14.md` (§6 read first) and
`reports/research-ui-dispatch-products-2026-09-14.md`. Scope: what "more colour, stronger identity,
still a government tool" concretely looks like, with sources.

**Source classes.** (A) the installed `venv/Lib/site-packages/streamlit` 1.63.0, executed on this
machine 2026-09-14 — strongest evidence, it is the code the gate runs; (B) docs.streamlit.io,
fetched 2026-09-14; (C) design-system pages, fetched 2026-09-14; (D) live CSS downloaded and grepped
2026-09-14. Nothing here has been applied to the repo.

---

## 1. Government and public-sector operational UI — what they actually look like

**1.1 None of the four big public design systems ships a "dashboard" pattern.**
*What the sources show:* the GOV.UK Service Manual design section lists prototyping, patterns, forms,
inclusive design — "no links about dashboards, internal services, or data display" (C,
`gov.uk/service-manual/design`). The NHS design system lists 42 components in four groups
(form elements, content presentation, navigation) — Card, Table, Tag present, **no Dashboard** (C,
`service-manual.nhs.uk/design-system/components`). USWDS templates are 404, documentation page,
landing page, authentication, forms — "does not include a dedicated dashboard template" (C,
`designsystem.digital.gov/documentation/developers/`). MOJ has no dashboard component either (C).
*Implication for Fair Turn:* there is no canonical government dashboard to copy, so "looks
governmental" cannot be achieved by imitating one. It is achieved by restraint plus a small number
of named, citable components. Do not invent a dashboard idiom and claim it is a standard.

**1.2 MOJ — the internal-caseworking system — is where the operational patterns live, and it uses
a coloured left border as its main colour device.**
*What the source shows:* MOJ **Ticket panel**: "Use this component for dashboard level information
as a way of breaking up content or actions into visually distinct chunks, specifically for instances
where information does not fit comfortably in the table or summary list components." It has a left
border that "can be colour-coded to reinforce status", classes
`moj-ticket-panel__content--blue|red|yellow|green|purple|orange`, container
`<article class="moj-ticket-panel">`, up to 4 panels per row. Marked "To be reviewed", created
**July 2022**, with a noted screen-reader concern. MOJ **Card** (marked *Experimental*, added
**November 2025**): white background, **1px solid #d9dadb** border, clickable variant adds a **5px
bottom border**, hover darkens the border; structure is heading-link → description. Active
components include Sortable table, Filter, Badge, Alert, Pagination, Side navigation, Timeline,
Scrollable pane (C, `design-patterns.service.justice.gov.uk`).
*Implication:* a 4-6 px coloured left edge on an otherwise white bordered container is a citable,
government-native way to add colour that carries meaning. This is the cheapest big win available to
Fair Turn — one scoped CSS rule on `st.container(border=True)`, degrading to a plain card if it
fails.

**1.3 NSW is the "dark chrome + one hot accent" model, and it restricts status colour by rule.**
*What the source shows:* brand dark **#002664** (navy), brand accent **#D7153A** (red), accent light
#FFE6EA, supplementary #146CFD; greys #22272B / #495054 / #CDD3D6 / #EBEBEB, off-white #F2F2F2;
status Info #2E5299 on #EAEDF4, Success #008A07 on #E5F6E6, Warning #C95000 on #FBEEE5, Error
#B81237 on #F7E7EB. Guidance: "Red is a core element of the NSW Government visual identity and
should be prioritised for use" and "status colours are only to be used when providing contextual or
transactional feedback to the user" (C, `designsystem.nsw.gov.au/core/colour/`, system v3.27.0).
*Implication:* the identity colour and the status colours are **two separate systems** and the
status set is rationed. Fair Turn already has this split (terracotta #b4462a vs the Carbon status
set in `.streamlit/config.toml`) — the fix is to actually *use* the identity colour somewhere
structural, which NSW does via a dark navy chrome, not by tinting the body.

**1.4 GOV.UK / NHS both forbid colour-only status and both cap the status count.**
*What the sources show:* NHS Tag — "Use the tag component when it's possible for something to have
more than 1 status and it's useful for the user to know about that status"; "Do not rely on colour
alone to convey information because it's not accessible"; "Start with the smallest number of
statuses you think might work, then add more if your user research shows there's a need for them";
ten colour classes, contrasts stated to meet **WCAG 2.0 AAA** (C,
`service-manual.nhs.uk/design-system/components/tag`). GOV.UK Tag says the same, with nine
meaning-assigned colours and the "never make them links or buttons" rule (C, recorded in the
companion report §6a.1). Two independent systems, same two rules.
*Implication:* Fair Turn's badge set stays at three or four words — "Needs a human", "Set by
coordinator", "Signed" — each with a word, never a bare dot. More colour must arrive through
*structure* (left borders, tiles, chart fills), not through more status hues.

**1.5 The NT's own remote-communities tool, BushTel, is a light-body Bootstrap 3 app with an orange
accent and a coloured header bar.**
*What the source shows (D, `bushtel.nt.gov.au/public/dist/app.css?v=2.5.26`, 1.0 MB, downloaded and
grepped 2026-09-14):* stock Bootstrap 3 underneath (#337ab7 primary, #d9534f danger, #333 text, #ddd
borders, #fff 369 occurrences), overlaid with a custom orange: **`#f90`** used for button
backgrounds, headings, panel headers and 1px top rules, **`#c60`** for `.btn-general`,
**`#f58231`** for map/marker fills, plus `.btn-floating{background-color:#195587}` and
`.btn-general-altcolour{background-color:#8c4799}`. `.sitename{float:right;color:#fff}` — the site
name is white, i.e. it sits on a dark/coloured bar. Fonts are **Bree Serif** (display) + **Lato**
(body), loaded from `fonts.googleapis.com`; the map is ArcGIS 3.43.
*Implication:* NT's real operational tool is a **white body, coloured chrome, warm-orange accent**
app. Fair Turn's white canvas + terracotta is already in the right family; it is *less* coloured
than the real thing, which is exactly the operator's complaint. Note also BushTel would fail Fair
Turn's offline gate (Google Fonts + ArcGIS CDN) — a point worth one line in the report, not a model
to copy.

**1.6 The NT Government's official colours are black, white and red ochre PMS 159 — hex ≈ #C75B12.**
*What the sources show:* "The Northern Territory's official colours are black, white and red ochre
(PMS 159)"; CMYK 1/74/100/7, Pantone 159 C, RGB hex **#C75B12** (C, nt.gov.au flag colour pages +
flagcolorcodes.com, both 2026-09-14; `nt.gov.au` itself is behind Cloudflare and returned a
challenge page to direct fetch, so the CSS could not be read — the colour is corroborated by two
non-CSS sources instead).
*Implication:* Fair Turn's **#b4462a** is a deliberately cooler, darker neighbour of NT ochre
#C75B12. Keep it: it reads as Territory-adjacent without claiming NTG brand compliance — which §1.7
says you must not do.

**1.7 Two design systems explicitly forbid a non-official product from wearing the government mark.**
*What the sources show:* GOV.UK header — "If your service is not hosted on one of the gov.uk domains
outlined, you must not use the GOV.UK header component as it's not considered part of GOV.UK"; use
the **Generic header** with your own branding instead. Service names no longer belong in the GOV.UK
header at all (use Service navigation). Refreshed **June 2025**, GOV.UK Frontend v6.0.0+ (C).
NSW brand classification has four tiers, and the fourth is **"Independent: Text-based logo only; no
NSW Government logo used"** (C, `designsystem.nsw.gov.au/core/logo/`).
*Implication:* Fair Turn is "Independent". A **text-based wordmark, no crest, no NTG logo** is not a
compromise — it is the correct classification, and saying so in the report is a trust point rather
than an apology.

---

## 2. Streamlit chrome: dark sidebar, logo, offline icons — verified on 1.63.0

**2.1 `[theme.sidebar]` takes 45 keys including `textColor`, `primaryColor`, `backgroundColor`,
`secondaryBackgroundColor` and `borderColor`. `showSidebarBorder` is NOT among them.**
*What the sources show (two independent):* (A) enumeration of
`streamlit.config._config_options_template` on this machine, 2026-09-14 — 45 `theme.sidebar.*` keys:
backgroundColor, baseRadius, borderColor, buttonRadius, chartCategorical/Diverging/SequentialColors,
codeBackgroundColor, codeFont, codeFontSize, codeFontWeight, codeTextColor, dataframeBorderColor,
dataframeHeaderBackgroundColor, font, headingFont, headingFontSizes, headingFontWeights, linkColor,
linkUnderline, primaryColor, secondaryBackgroundColor, showWidgetBorder, textColor, and the full
`red|orange|yellow|green|blue|violet|gray × Color|TextColor|BackgroundColor` set.
`theme.sidebar.showSidebarBorder` → **False** (absent). (B) docs.streamlit.io "Customize colors and
borders" (2026-09-14) lists the same sidebar-settable set and names exactly two app-wide-only keys:
`theme.base` and `theme.showSidebarBorder` — "sets the visibility of the border between the sidebar
and the main body". The docs' own example is `[theme] base="light"` + `[theme.sidebar] base="dark"`.
*Implication:* a dark sidebar is **four lines of TOML, zero CSS**. Fair Turn's current
`[theme.sidebar] backgroundColor = "#f4f4f4"` is the single biggest reason it reads "plain": the
sidebar is 4 % different from the canvas. This is the highest-leverage change in this report.

**2.2 `st.logo` accepts an SVG *file path*, inlines it as a base64 data URI, and renders at 20 / 24 /
32 px max height.**
*What the sources show:* (A) `inspect.signature(st.logo)` on this machine:
`(image, *, size: Literal['small','medium','large'] = 'medium', link: str|None = None,
icon_image: AtomicImage|str|None = None)`. Docstring (A): "small": **20px max height**, "medium"
(default): **24px**, "large": **32px**; width is capped "to fit within the sidebar"; `image` also
accepts a single-character emoji or `":material/icon_name:"`; `icon_image` replaces `image` when the
sidebar is closed. (A) `streamlit/elements/lib/image_utils.py` line 284:
`if image.endswith(".svg") and os.path.isfile(image):` — the file is read and returned as
`data:image/svg+xml;base64,…`, so **no HTTP request and no static-serving dependency**.
*Implication:* ship `fair_turn/app/static/logo.svg` (wide wordmark) + `logo-mark.svg` (square mark)
and call `st.logo(logo, size="large", icon_image=mark)`. 32 px is the whole budget — the wordmark
must be legible at 32 px tall, which rules out a tagline and fine detail.

**2.3 Material Symbols are bundled locally; `:material/…:` page icons render with no network.**
*What the sources show (A, grep of `venv/Lib/site-packages/streamlit/static`, 2026-09-14):* the file
`static/media/MaterialSymbols-Rounded.Bc71WqoX.woff2` exists, and
`static/css/index.DZDjBcCO.css` contains
`@font-face{font-family:Material Symbols Rounded;font-style:normal;font-weight:400;font-display:block;src:url(../media/MaterialSymbols-Rounded.Bc71WqoX.woff2)format("woff2")}`
— a **relative** URL into Streamlit's own bundle. Referenced in `manifest.json`. (B) docs confirm the
`:material/home:` format for `st.Page(icon=…)`, `st.logo`, `st.badge`, `st.metric`, `st.button`.
*Implication:* every nav page icon, badge icon and metric icon is free and offline-safe. This is
pure identity gain at zero risk to the socket-refusing gate — unlike a Google Fonts import (§1.5).

**2.4 Dated third-party examples of the pattern.** The dark-sidebar + `st.logo` + material-icon-nav
combination is documented rather than showcased: the canonical example is the official
`st.navigation` / `st.logo` docs pair (B, 2026-09-14) — `st.logo()` plus pages carrying
`:material/home:`, `:material/monitoring:`, `:material/settings:`, grouped into sections via a
`Mapping[SectionHeader, Sequence[Page]]`; docs state "a common design practice is to use a wider
logo in the sidebar, and a smaller, icon-styled logo in your app's main body". Secondary, dated:
`streamlit/streamlit` issue **#12657 "Top navigation makes `st.logo` shrink"** (a real report that
`position="top"` reduces the rendered logo — relevant because Fair Turn uses sidebar nav, so it does
not bite), and issue **#9038 "fav icon in st.navigation pages"**. Community examples found
(`Paldom/streamlit-custom-style`, HuggingFace Spaces `mediNER`, `customer-predict`) are undated
or unversioned.
*Honest read:* **no well-known, dated, screenshot-backed Streamlit app** was found that demonstrates
a dark sidebar with a vendored wordmark. Marked **TBD, needs validation** — the mechanism is proven
on this machine (§2.1–2.3); the *look* has no exemplar and has to be judged on screen.

**2.5 `st.button(type="tertiary")` exists on 1.63.**
*What the source shows (A, live signature):* `type: Literal['primary','secondary','tertiary'] =
'secondary'`, alongside `icon`, `icon_position`, `shortcut`, `wrap`, `width`. Tertiary renders as a
borderless text-link-style button (introduced 1.51.0, 2025-10-29, per the companion report §5.2).
*Implication:* row-level and pane-level secondary actions ("Change", "Why this rank?") become quiet
text buttons instead of a wall of grey boxes — which is half of what makes a Streamlit page look
like a form rather than a tool.

---

## 3. Readable ranked rows, not a dataframe

**3.1 The canonical government list row is: name (+ hint) on the left, status tag on the right, whole
row clickable.**
*What the source shows:* GOV.UK **Task list** — left: task name as linked text with optional
single-sentence hint below; right: status, either plain black text ("Completed") or a tag
(`govuk-tag--blue` for "Incomplete"); the entire row is the link; statuses in sentence case; classes
`govuk-task-list`, `__item`, `__status`, `__hint`. "Do not use the task list … as a way of showing
users their answers" — that is the **Summary list** (C). Summary list is the key–value `<dl>`,
explicitly not for tabular data, with context-bearing actions ("Change name", not "Change") (C, via
companion report §6a.2).
*Implication:* two different components for two different Fair Turn surfaces — the ranked queue is a
task-list-shaped row list; the selected-job pane is a summary list. Do not use one grammar for both.

**3.2 Carbon: a single-selection list of many rows is a structured list, not a data table.**
*What the source shows:* structured list "displays a simple list with a considerable amount of items
in multiple rows", used "to browse information or select certain information within the group in the
simplest form"; **"Only one item can be selected from the list. If you need to select multiple items,
use a data table."** Use a data table for complex/nested content or multi-select (C,
`carbondesignsystem.com/components/structured-list/usage/`).
*Implication:* corroborates the companion report's recommendation of
`selection_mode="single-row-required"` — and says the deeper thing: at single-select, the table
*grammar itself* is wrong. Fair Turn's ranked queue wants rows, not a grid.

**3.3 Dispatch products put two independent colour channels on one card, with a legend on the page.**
*What the sources show:* Simpro (AU) — "Schedules are colour-coded by their status … with a legend
at the bottom of the page for quick colour code reference", and in Simpro Mobile "the coloured
status bar … matches the colour of the job status … and the coloured circle around matches the
colour of the current mobile status". ServiceM8 — Blue / Red / Yellow dots with three stated
meanings, plus queues that carry an **expiry date**. PagerDuty — **Priority** ("the order in which
incidents must be addressed") and **Urgency** ("determines how you are notified") are separate
columns, sort by "Urgency, Priority, or Recent", and every priority change ends in "Confirm"
(all via `reports/research-ui-dispatch-products-2026-09-14.md` §1.5, §3, undated vendor help pages).
*Implication:* Fair Turn legitimately has two axes — NT **policy class** (Immediate / Urgent /
Routine) and **today's rank**. Two channels on one row (left border = policy class, badge = needs a
human) has precedent, and a legend at the foot of the board is expected, not clutter.

**3.4 Streamlit 1.63 has exactly one non-checkbox row-click mechanism: `ButtonColumn`.**
*What the source shows (A, live introspection 2026-09-14):* `st.dataframe` selection modes are
`single-row`, `single-row-required`, `multi-row`, `single-column`, `multi-column`, `single-cell`,
`multi-cell`; row selection is the checkbox gutter, and `DataframeSelectionState.rows` returns
integer positions that "match the original dataframe, even if the user sorts the dataframe in their
browser". In `single-row-required` mode the source auto-selects the first row when none is selected
(`arrow.py` line ~349). The one alternative is
`st.column_config.ButtonColumn(label, *, width, help, pinned, alignment, type, on_click, args,
kwargs, key)` — "Button columns display clickable buttons in each cell, enabling row-level actions
with Python callbacks. The cell values determine the button labels." Widths: "small" 75 px, "medium"
200 px.
*Implication:* clicking a job id itself (rather than a checkbox) is possible via a pinned
`ButtonColumn` whose values are the job ids — but it is a button, and GOV.UK's tag rule (§1.4) says
a *status* must never be a button. Put the action on the identifier, never on the badge.

---

## 4. Logo craft for a text-based tool wordmark

**4.1 An "Independent" public-sector product uses a text-based logo — mark optional, crest never.**
Two sources, §1.7: NSW brand tier 4 ("Text-based logo only") and the GOV.UK header domain rule.
*Implication:* "Fair Turn" set in IBM Plex Sans SemiBold, one terracotta element, no crest. State in
the report that no NTG mark is used and why.

**4.2 Minimum sizes: ~20 px is the floor for a wordmark; NSW's own floors are 60 px primary /
38–60 px reduced / icon-only for favicons.**
*What the sources show:* NSW logo page (C, 2026-09-14) — 76 px height on ≥992 px screens, 48 px
below 991 px; primary logo minimum **60 px**; "NSW Only" reduced logo **38–60 px**; "Waratah Only"
for favicon and app icon only; clear space = "100% of the width of the 'N'", adjacent logos separated
by twice the 'N'. Secondary (weaker, commercial): SVG brand-guideline guidance giving ~20 px as a
digital wordmark floor and recommending one SVG master exported as full-colour / single-colour /
reversed / horizontal / stacked / icon-only variants.
*Implication:* Streamlit's `st.logo(size="large")` caps at **32 px** (§2.2) — below NSW's own
primary-logo minimum. So Fair Turn needs the **reduced lockup as the primary asset**: a square mark
plus a short wordmark, designed at 32 px, with the mark alone as `icon_image` and the favicon.

**4.3 Coloured-square-plus-text is the standard public-sector tool logo.** Concrete examples in the
sources above: the MOJ Card's 5 px coloured bottom border and the Ticket panel's coloured left edge
are the same device at component scale (§1.2); NSW's "Waratah Only" square-crop mark for app icons
(§4.2); GOV.UK's own crown-plus-wordmark lockup, which is a single mark followed by type in one
weight (§1.7). All three are: one shape, one colour, type in the system font, no gradient.
*Implication:* Fair Turn's mark should be a solid **#b4462a** square with one white geometric cut
(e.g. a queue notch or a turned arrow, reading as "turn"), followed by "Fair Turn" in IBM Plex Sans
SemiBold #161616. Nothing else.

---

## Recommended visual direction for Fair Turn

1. **Make the sidebar dark chrome, not off-white.** `[theme.sidebar] backgroundColor = "#161616"`
   (ink), `textColor = "#f4f4f4"`, `secondaryBackgroundColor = "#262626"`,
   `borderColor = "#393939"`, `primaryColor = "#b4462a"`. Zero CSS (§2.1). Keep
   `[theme] showSidebarBorder` at top level — it is not a sidebar key.
2. **Keep the canvas white (#ffffff) and the body tokens exactly as they are.** NSW, GOV.UK, NHS and
   BushTel all pair coloured chrome with a plain light working surface (§1.3, §1.5).
3. **Use terracotta #b4462a structurally, not decoratively:** the sidebar's active-page indicator,
   the logo mark, the KPI tile rule, and `linkColor`. One accent, appearing in three or four fixed
   places, reads as identity; sprinkled, it reads as decoration (§1.3).
4. **Add a 4 px coloured left edge to job cards and the selected-job pane** — MOJ Ticket panel's
   device (§1.2). Map it to **policy class only**: Immediate `#da1e28`, Urgent `#ff832b`, Routine
   `#8d8d8d`, all already in `.streamlit/config.toml`. One scoped CSS rule in the single `st.html`
   file, degrading to a plain bordered card.
5. **Cap the badge set at three words**, each with a Material icon and never colour alone (§1.4):
   "Needs a human" (`redColor #da1e28`), "Set by coordinator" (`blueColor #0072c3`), "Signed"
   (`greenColor #24a148`).
6. **Ship `logo.svg` + `logo-mark.svg` and call `st.logo(…, size="large", icon_image=mark, link=None)`.**
   SVG file paths are inlined as base64, no network (§2.2). Design at 32 px; the mark is a solid
   #b4462a square with one white cut, wordmark in IBM Plex Sans SemiBold #161616.
7. **Give every `st.Page` a `:material/…:` icon and group pages into two sections** ("Today's work",
   "Evidence"). The font is bundled locally — offline-safe (§2.3).
8. **Raise the grey contrast one step.** Use #525252 for secondary text (not #8d8d8d), #8d8d8d for
   disabled/meta only, #e0e0e0 for hairlines, #f4f4f4 only for the table header band and tile fills.
   The current look is flat because three near-identical light greys do three different jobs.
9. **Do not wear an NTG crest or claim brand compliance.** Fair Turn is NSW's "Independent" tier
   (§1.7); #b4462a is a neighbour of NT ochre #C75B12, not a match, and the report should say so
   (§1.6).
10. **Put a small colour legend at the foot of the board** naming what the left edge and each badge
    mean — precedent in Simpro and ServiceM8 (§3.3), and it is the accessible answer to §1.4.

## Row list spec — a ranked job row

Left to right, in one `st.container(border=True)` per job (or as pinned columns if the dataframe is
kept). Derived from GOV.UK Task list (§3.1), Carbon structured list (§3.2), MOJ Ticket panel (§1.2),
PagerDuty's two-axis rule and Simpro's two colour channels (§3.3).

| # | Field | Treatment | Source |
|---|---|---|---|
| 1 | Policy-class edge | 4 px left border, colour only (meaning repeated in col. 5) | MOJ Ticket panel |
| 2 | Rank | Today's rank, plain numeral, fixed width, #525252 | PagerDuty "Priority" column |
| 3 | Job id | **Primary identifier**, SemiBold #161616, the clickable element | GOV.UK Task list (name = link) |
| 4 | Community + fault, one line | Regular weight; the "hint" line, one short sentence, no full stop | GOV.UK Task list hint |
| 5 | Policy class | Word — "Immediate" / "Urgent" / "Routine" — never colour alone | GOV.UK + NHS Tag |
| 6 | Score | `ProgressColumn` bar or a short bar glyph, not six decimals | Carbon structured list |
| 7 | Status badge | At most one: "Needs a human" / "Set by coordinator" / "Signed"; non-interactive | GOV.UK Tag |
| 8 | Right-aligned meta | Days open or distance, `NumberColumn(format=…)`, #8d8d8d | GOV.UK Task list (status right) |

**Selection.** Single-select only, `selection_mode="single-row-required"` so the page never opens on
an empty pane; selected row marked by a filled #f4f4f4 background **plus** a thickened left edge —
two channels, not colour alone. Row actions live on the identifier (col. 3) via `ButtonColumn` or a
`type="tertiary"` button; **never** on the badge (§1.4, §3.4).

---

**Marked TBD, needs validation:** a dated, screenshot-backed Streamlit exemplar of dark-sidebar +
wordmark (none found, §2.4); `nt.gov.au`'s live CSS (Cloudflare challenge, §1.6); exact NHS/GOV.UK
tag hex values (class names only were published); whether a 4 px left edge survives Streamlit's
container padding without a `data-testid` selector — the companion report's warning that those
selectors fail silently applies in full.
