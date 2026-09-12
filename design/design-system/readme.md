# Fair Turn Design System

## Context

**Fair Turn** is a decision-support tool for a housing maintenance coordinator in the Northern Territory, Australia, plus a plain-language page for tenants. It ranks maintenance jobs for review using four factors (urgency, safety, household health risk, logistics), lets the coordinator adjust an equity weighting, records sign-off, simulates scenarios, and keeps an append-only audit table. The tool supports a decision; it never makes one.

Implementation: **Streamlit, standard components only** (dataframe, metric, slider, selectbox, warning/info boxes, columns, tabs, Altair charts). No custom components, no animation, no free-form layouts. Light theme only.

Surfaces: (1) coordinator app — triage board, job card, sign-off form, simulation page, audit table; (2) tenant answer page.

## Source

- `design/DESIGN_IBM.md` — a design.md extraction of IBM's public marketing site (Carbon Design System). Proprietary identity (IBM name, wordmark, logomark, IBM Blue as brand) was stripped; every other rule (type scale, spacing, radius, elevation, component patterns, responsive behaviour, do's and don'ts) is kept verbatim. No Figma, codebase or logo was provided.
- Streamlit theme key names confirmed against the config.toml reference (docs.streamlit.io).

## Index

All files live in `design/`.

- `DESIGN.md` — the full design template. Same section structure as the source, plus **Streamlit mapping**, chart palette (under Colors), screen rules and empty/unverified-field rules (under Components), wording rule (under Do's and Don'ts).
- `tokens.json` — Streamlit theme keys and values, exactly the 34 keys requested.
- `chart-palette.json` — palettes with no Streamlit theme key (regions by name, town/remote pair, factors, needs-a-human) for explicit Altair scales.
- `styles.css` → `tokens/fonts.css`, `tokens/colors.css`, `tokens/typography.css`, `tokens/spacing.css` — the same values as CSS custom properties for any HTML consumer. `tokens/fonts.css` declares `@font-face` against the woff2 files vendored in the app repo (`fair_turn/app/static/fonts`); the binaries are not in this project and the Streamlit app never loads `styles.css`, only `.streamlit/config.toml`.
- `SKILL.md` — agent skill wrapper.

No components, UI kits, specimen cards or screens were produced, per the brief ("Do not generate screens or HTML").

## Content fundamentals

- **Tone**: plain, direct, matter-of-fact. Government-grade: every sentence can be read aloud in a meeting without embarrassment.
- **Casing**: sentence case everywhere — headings, labels, buttons, tabs, eyebrows. No all-caps, no title case.
- **Person**: second person for instructions ("Choose a weighting"). Tenant page is second person, present tense ("Your repair is number 4 of 31 in your area this week").
- **Reading level**: coordinator screens assume a professional reader; tenant page is year 7 — sentences under 20 words, one idea per paragraph, no acronyms without the words first, numbers only inside sentences.
- **Emoji**: never. **Icons**: none. **Exclamation marks**: none.
- **Wording rule**: no deficit language ("vulnerable", "at-risk", "disadvantaged", "high-needs"). The factor is "household health risk", spelled out every time, never abbreviated. Describe conditions and actions, not categories of people.
- **Agency**: "ranked for review", "suggested order", "Record decision". Never "approved by the system".
- **Honesty**: an empty field reads "—" and "Not recorded"; an unverified value carries an "Unverified" badge; a partial computation says "Based on N of M fields". Nothing is faked.
- **Examples**: button "Record decision"; slider ends "Weight urgency more" / "Weight household health risk more"; caption "Ranking updated for weighting X"; tenant heading "When will someone come?"; empty date "We do not have a date yet."

## Visual foundations

- **Colour**: white canvas (#ffffff), light gray band (#f4f4f4), charcoal ink (#161616). One accent, terracotta #b4462a (5.45:1 with white), with hover #a33e25, link-hover #8f3720, pressed #6e2a17, and a faint tint #fbf1ec used only for the selected table row. Semantic hues are Carbon's public red/orange/yellow/green/gray plus cyan-60 for blue (so no blue reads as the removed brand blue) and purple-60 for violet (reserved, unused). Chart palettes are documented in DESIGN.md with contrast ratios; every value is ≥ 4.5:1 on canvas.
- **Type**: IBM Plex Sans 300/400/600 (SIL OFL, vendored in the app repo at `fair_turn/app/static/fonts`; no external font requests) and Streamlit's default code font, Source Code Pro, for mono. Display 42px+ at weight 300; body 16px/1.50 with 0.16px tracking; captions 12px with 0.32px tracking. Mono (Source Code Pro) for IDs, timestamps, hashes and aligned numbers. Floor: 14px running text, 12px anything.
- **Spacing**: 4px base; 4/8/12/16/24/32/48/96. Button padding 12×16, input 11×16, card 24.
- **Radius**: 0px on everything. Streamlit `baseRadius` and `buttonRadius` are `0px`.
- **Backgrounds**: flat solid only. No images, no patterns, no textures, no gradients (the source's soft-blue hero wash is removed with the brand).
- **Elevation**: none by shadow. Hierarchy via 1px #e0e0e0 hairlines and canvas → surface-1 change. Focus = 2px terracotta outline + 1px charcoal underline.
- **Animation**: none. Streamlit's built-in transitions are left at default; nothing is added.
- **Hover**: primary button darkens one step (#a33e25); links darken to #8f3720; tertiary buttons gain a surface-1 fill. **Press**: primary goes to #6e2a17. No shrink, no opacity change.
- **Borders**: 1px hairline on cards, inputs, dataframes; 2px bottom rule for focus, error, selected tab and source-phrase highlights.
- **Transparency / blur**: none. The single permitted alpha is a 10% factor-colour fill behind highlighted source phrases.
- **Imagery**: none. No photography, illustration, icons or depictions of country, community or people.
- **Cards**: white, 1px hairline, 0px radius, no shadow; `st.container(border=True)`.
- **Layout**: `wide` for coordinator screens (dense, 4-column metric rows, side-by-side rankings); `centered` ~720px for the tenant page. Sidebar on surface-1 carries navigation and scenario controls.
- **Charts**: 2px strokes, marks at data points, hairline gridlines, caption-size axis labels in ink-muted, direct labels preferred over legends, gaps for missing data, dashed strokes for projected values.

## Iconography

None. Fair Turn uses no icon system, icon font, SVG set, PNG icons or emoji. Where an icon would normally signal state, a word or a badge does: "Verified", "Unverified", "Needs a human". The only glyphs are typographic: the em dash "—" for an empty field and arrows "↑ ↓" for rank changes, set in the code font. Streamlit's own widget chrome (chevrons, close marks) is left at default.

No logo or mark exists. The product name "Fair Turn" is set in plain Plex Sans wherever a mark would go. Do not create one.

## Font binaries

Vendored in app repo: `fair_turn/app/static/fonts/IBMPlexSans-{Light,Regular,SemiBold}.woff2`. Not present in this project by design; the design-system font check reports them as missing and that is expected.

## Intentional additions

- `typography.mono` — the source excluded mono from marketing surfaces; Fair Turn is a product surface and needs it for IDs and audit values.
- `colors.terracotta-10` — a faint tint for the selected ranked-table row; the source had no equivalent because it had no tables.
- Slider, dataframe, metric, alert-box and badge rules — Streamlit widgets with no counterpart in the marketing extraction; each follows the nearest source rule (input, card, hairline).
