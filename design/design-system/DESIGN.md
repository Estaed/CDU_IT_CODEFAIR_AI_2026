---
version: alpha
name: fair-turn-design
description: "A calm, data-dense decision-support canvas for Fair Turn, derived from the Carbon Design System's public rules: white surfaces, charcoal type, a single warm terracotta accent (#b4462a) in place of a brand blue, and a flat-square aesthetic where corners stay at 0px. Type runs IBM Plex Sans at weight 300 for display sizes and 400/600 for body and emphasis; Streamlit's default code font (Source Code Pro) carries job IDs, timestamps and audit hashes. Cards are thin-bordered tiles with no shadow; sections separate via subtle gray bands. Light theme only, built for Streamlit standard components, government-grade readability."

colors:
  primary: "#b4462a"
  on-primary: "#ffffff"
  ink: "#161616"
  ink-muted: "#525252"
  ink-subtle: "#8c8c8c"
  canvas: "#ffffff"
  surface-1: "#f4f4f4"
  surface-2: "#e0e0e0"
  inverse-canvas: "#161616"
  inverse-surface-1: "#262626"
  inverse-ink: "#ffffff"
  inverse-ink-muted: "#c6c6c6"
  hairline: "#e0e0e0"
  hairline-strong: "#161616"
  terracotta-70: "#8f3720"
  terracotta-80: "#6e2a17"
  terracotta-hover: "#a33e25"
  terracotta-10: "#fbf1ec"
  semantic-success: "#24a148"
  semantic-warning: "#f1c21b"
  semantic-error: "#da1e28"
  semantic-info: "#0072c3"
  region-central-australia: "#8a6400"
  region-big-rivers: "#007d79"
  region-barkly: "#9f1853"
  region-top-end: "#198038"
  region-east-arnhem: "#2d5bbf"
  region-darwin: "#4d5358"
  locality-town: "#262626"
  locality-remote: "#8a3ffc"
  factor-urgency: "#da1e28"
  factor-safety: "#b35c00"
  factor-household-health-risk: "#6929c4"
  factor-logistics: "#0072c3"
  highlight-human: "#684e00"
  highlight-human-bg: "#fcf4d6"

typography:
  display-xl:
    fontFamily: IBM Plex Sans
    fontSize: 76px
    fontWeight: 300
    lineHeight: 1.17
    letterSpacing: -0.5px
  display-lg:
    fontFamily: IBM Plex Sans
    fontSize: 60px
    fontWeight: 300
    lineHeight: 1.17
    letterSpacing: -0.4px
  display-md:
    fontFamily: IBM Plex Sans
    fontSize: 42px
    fontWeight: 300
    lineHeight: 1.20
    letterSpacing: 0
  headline:
    fontFamily: IBM Plex Sans
    fontSize: 32px
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: 0
  card-title:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: 0
  subhead:
    fontFamily: IBM Plex Sans
    fontSize: 20px
    fontWeight: 400
    lineHeight: 1.40
    letterSpacing: 0
  body-lg:
    fontFamily: IBM Plex Sans
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0
  body:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0.16px
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.29
    letterSpacing: 0.16px
  body-emphasis:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.29
    letterSpacing: 0.16px
  caption:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: 0.32px
  button:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.29
    letterSpacing: 0.16px
  eyebrow:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.29
    letterSpacing: 0.16px
  mono:
    fontFamily: Source Code Pro
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.29
    letterSpacing: 0.32px

rounded:
  none: 0px
  xs: 2px
  sm: 4px
  md: 6px
  lg: 8px
  pill: 9999px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 96px

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: 12px 16px
  button-primary-hover:
    backgroundColor: "{colors.terracotta-hover}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
  button-primary-pressed:
    backgroundColor: "{colors.terracotta-80}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
  button-secondary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.inverse-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: 12px 16px
  button-tertiary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.primary}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: 12px 16px
  button-ghost:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.primary}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: 12px 16px
  button-danger:
    backgroundColor: "{colors.semantic-error}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: 12px 16px
  feature-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 24px
  feature-card-elevated:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 24px
  product-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 32px
  hero-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.display-md}"
    rounded: "{rounded.none}"
    padding: 48px
  cta-banner:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.headline}"
    rounded: "{rounded.none}"
    padding: 48px
  text-input:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 11px 16px
  text-input-focused:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 11px 16px
  text-input-error:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 11px 16px
  newsletter-input:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: 11px 16px
  product-tab:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    padding: 16px 20px
  product-tab-selected:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.none}"
    padding: 16px 20px
  resource-tile:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    padding: 16px
  customer-logo-tile:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    padding: 24px
  top-nav:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    height: 48px
  utility-bar:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    height: 32px
  footer:
    backgroundColor: "{colors.inverse-canvas}"
    textColor: "{colors.inverse-ink-muted}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    padding: 64px 32px
---

## Overview

Fair Turn's system is derived from the public, Apache-licensed rules of the **Carbon Design System**, with the brand identity removed. The dominant surface is `{colors.canvas}` pure white with `{colors.surface-1}` light gray for elevation, charcoal `{colors.ink}` (#161616) for text, and **terracotta** `{colors.primary}` (#b4462a) as the single accent. No wordmark or logomark exists; the product name is set in plain type.

The defining choice is **flat geometry**: every button, card, input, and container uses square corners (`{rounded.none}` 0px) with thin 1px borders. There are no rounded pills, no soft shadows, no atmospheric gradients. The system is engineered, not stylized.

**IBM Plex Sans** (SIL OFL) carries the type hierarchy. Display sizes (76 / 60 / 42px) run at weight **300**; body type sits at weight 400 with `letter-spacing: 0.16px` and line-height 1.50. Streamlit's default code font, **Source Code Pro**, carries job IDs, timestamps, hashes and audit values.

The system reaches for color rarely. Terracotta marks links, primary buttons, the slider fill, the selected tab underline and focus. Chart palettes are the only other chromatic content. Charcoal carries every other surface that isn't white.

**Key Characteristics:**
- **Carbon-derived chrome**: buttons are square, inputs are square-with-bottom-rule, corners stay at 0px.
- **Light-weight display type**: Plex Sans at weight 300 for 42–76px headings.
- **One accent color**: `{colors.primary}` terracotta carries every link, primary button, slider fill and focus state. There is no second brand color.
- White canvas + light gray (`{colors.surface-1}`) + charcoal (`{colors.ink}`) cover 95% of surfaces.
- Card hierarchy is carried by 1px hairlines and surface change, never by drop shadow.
- `letter-spacing: 0.16px` on body is a Carbon precision detail — the small positive tracking is part of the typographic voice.
- Light theme only. No dark mode.
- Implementation surface is **Streamlit standard components only** (dataframe, metric, slider, selectbox, warning/info boxes, columns, tabs, Altair charts). No custom components, no animation, no free-form layouts.

## Colors

> Source: Carbon Design System public palette (Apache 2.0), via the extracted DESIGN_IBM.md. IBM Blue (#0f62fe) and its derived states are removed and replaced with the terracotta family below. All other neutral and semantic values are unchanged.

### Brand & Accent
- **Terracotta** ({colors.primary}) #b4462a: The single accent. Links, primary buttons, slider fill, selected-tab underline, focus rings. White text on it measures **5.45:1** (AA); it measures 5.45:1 as text on canvas and 4.96:1 on `{colors.surface-1}`.
- **Terracotta Hover** ({colors.terracotta-hover}) #a33e25: Hover state for primary buttons (one shade darker, as Blue Hover was to IBM Blue). 6.4:1 with white.
- **Terracotta 70** ({colors.terracotta-70}) #8f3720: Hovered link state (the Blue 60 role). 7.7:1 on canvas.
- **Terracotta 80** ({colors.terracotta-80}) #6e2a17: Pressed primary button (the Blue 80 role). 10.4:1 with white.
- **Terracotta 10** ({colors.terracotta-10}) #fbf1ec: Faint tint. Only permitted use: selected row in a ranked table.

State derivation (unchanged from the source): hover = one step darker than primary; pressed = the 80 step; link hover = the 70 step; focus = 2px `{colors.primary}` outline + 1px `{colors.hairline-strong}` underline.

### Surface
- **Canvas** ({colors.canvas}): Default page background.
- **Surface 1** ({colors.surface-1}): Light gray (#f4f4f4) — input fields, alternate-row stripes, subtle section bands, dataframe headers.
- **Surface 2** ({colors.surface-2}): Slightly darker gray (#e0e0e0) — disabled fields, hairline-as-fill for separators.
- **Hairline** ({colors.hairline}): 1px borders on cards, inputs, dividers, dataframe cell borders.
- **Hairline Strong** ({colors.hairline-strong}): 1px charcoal underline on focused inputs.
- **Inverse Canvas** ({colors.inverse-canvas}): Charcoal #161616 — footer surface (rare in Streamlit; see Components).
- **Inverse Surface 1** ({colors.inverse-surface-1}): One step lighter than inverse canvas.

### Text
- **Ink** ({colors.ink}): All headings and body — charcoal #161616.
- **Ink Muted** ({colors.ink-muted}): Secondary type at #525252 — meta, captions, help text under widgets.
- **Ink Subtle** ({colors.ink-subtle}): Tertiary type at #8c8c8c — disabled labels and the "—" empty marker only. Never for running text (3.4:1).
- **Inverse Ink** / **Inverse Ink Muted**: White and light gray on charcoal.

### Semantic
Each semantic hue is a triplet: **colour** (icon, badge fill, chart marker), **background** (alert box fill), **text** (type on that background; AA against it and against canvas).

| Hue | Colour | Background | Text | Use in Fair Turn |
|---|---|---|---|---|
| Red | #da1e28 | #fff1f1 | #a2191f | Errors, failed validation, `st.error` |
| Orange | #ff832b | #fff2e8 | #8a3800 | `st.warning` when data is stale or incomplete |
| Yellow | #f1c21b | #fcf4d6 | #684e00 | "Needs a human" review highlight |
| Green | #24a148 | #defbe6 | #0e6027 | Signed off, verified, `st.success` |
| Blue | #0072c3 | #e5f6ff | #003a6d | `st.info`, neutral explanations on the tenant page |
| Violet | #8a3ffc | #f6f2ff | #491d8b | Reserved. Not used by any Fair Turn screen |
| Gray | #8d8d8d | #f4f4f4 | #525252 | "Unverified" and "Not recorded" badges |

Rules: orange and yellow **colour** values fail AA as text (2.9:1 and 1.7:1) and are only ever fills or icons; their **text** value carries any words. The semantic blue is Carbon cyan-60, chosen so no blue in the system reads as the removed brand blue.

### Chart palette

All values measure ≥ 4.5:1 against `{colors.canvas}` (#ffffff), so each can also label its own series in text. Three palettes exist because they appear on three different chart types; a colour may repeat across palettes but two palettes never share one chart.

**Regions (categorical, six)** — the order is fixed; it is the order of `chartCategoricalColors`.

| Region | Hex | Contrast on canvas |
|---|---|---|
| Central Australia | #8a6400 (dark ochre) | 5.4:1 |
| Big Rivers | #007d79 (teal) | 5.0:1 |
| Barkly | #9f1853 (magenta) | 7.7:1 |
| Top End | #198038 (green) | 5.0:1 |
| East Arnhem | #2d5bbf (indigo) | 6.3:1 |
| Darwin | #4d5358 (slate) | 7.8:1 |

**Town / remote pair (high contrast)** — Town #262626 (15.1:1), solid line / filled mark. Remote #8a3ffc (5.0:1), dashed line / hollow mark. Encode the pair in stroke as well as colour so it survives greyscale printing.

**Factors (four)** — used for factor-weight bars on the simulation page and for source-phrase highlights on the job card.

| Factor | Hex | Contrast on canvas |
|---|---|---|
| Urgency | #da1e28 | 5.0:1 |
| Safety | #b35c00 | 4.7:1 |
| Household health risk | #6929c4 | 7.7:1 |
| Logistics | #0072c3 | 5.0:1 |

**"Needs a human" highlight** — text/border #684e00 on fill #fcf4d6 (7.2:1 on the fill, 7.8:1 on canvas). This is the yellow semantic triplet under its own token name; it is the only yellow in the product, so yellow always means "a person must look at this".

**Sequential (10, light → dark)** — terracotta ramp, for single-measure heat cells and choropleth-style fills. The only place the accent appears inside a chart.
`#fbf1ec #f5dcd1 #edc2b0 #e3a68e #d6886b #c66a4c #b4462a #963920 #762c18 #561f10`

**Diverging (10, teal → neutral → terracotta)** — for before/after and equity-slider deltas, where zero is meaningful.
`#004144 #005d5d #007d79 #4fa8a3 #a6d5d2 #f0c6b5 #de9a80 #c86b4c #b4462a #6e2a17`

Chart rules: gridlines `{colors.hairline}`; axis labels `{typography.caption}` in `{colors.ink-muted}`; never rely on colour alone — add a text label, stroke style or direct annotation; missing data is a gap, never an interpolated line or a zero.

## Typography

### Font Family

- **IBM Plex Sans** — open source under the SIL Open Font License. Geometric, slightly humanist, designed for enterprise UI. Fallback: `Helvetica Neue, Arial, sans-serif`.
- **Source Code Pro** — Streamlit's default code font, left unchanged (`codeFont` is not overridden). Used for job IDs, timestamps, hashes, numeric columns where alignment matters, and code. Fallback: `Menlo, Consolas, monospace`.

Hierarchy is carried by **size + weight**, not by family change. Mono is a functional register, never decorative.

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xl}` | 76px | 300 | 1.17 | -0.5px | Not used in Streamlit surfaces; retained for completeness |
| `{typography.display-lg}` | 60px | 300 | 1.17 | -0.4px | Not used in Streamlit surfaces; retained |
| `{typography.display-md}` | 42px | 300 | 1.20 | 0 | Page title (`st.title`, h1) |
| `{typography.headline}` | 32px | 400 | 1.25 | 0 | Section heading (`st.header`, h2) |
| `{typography.card-title}` | 24px | 400 | 1.33 | 0 | Sub-section heading (`st.subheader`, h3); `st.metric` value |
| `{typography.subhead}` | 20px | 400 | 1.40 | 0 | Tenant page lead paragraph; h4 |
| `{typography.body-lg}` | 18px | 400 | 1.50 | 0 | Tenant page body; h5 |
| `{typography.body}` | 16px | 400 | 1.50 | 0.16px | Default body, widget labels |
| `{typography.body-sm}` | 14px | 400 | 1.29 | 0.16px | Dataframe cells, help text, tab labels |
| `{typography.body-emphasis}` | 14px | 600 | 1.29 | 0.16px | Selected tab, dataframe header, h6 |
| `{typography.caption}` | 12px | 400 | 1.33 | 0.32px | Chart axes, `st.caption`, metric labels |
| `{typography.button}` | 14px | 400 | 1.29 | 0.16px | All button labels |
| `{typography.eyebrow}` | 14px | 400 | 1.29 | 0.16px | Section eyebrows, sentence case |
| `{typography.mono}` | 14px | 400 | 1.29 | 0.32px | Job IDs, timestamps, hashes, `st.code` |

### Principles

- **Light-weight display is the voice.** Plex Sans at weight 300 for headings 42px and up reads as quietly authoritative.
- **`letter-spacing: 0.16px`** on body sizes is a precision detail. Don't remove it.
- **Mono is functional.** Use it wherever a value must be compared character by character (IDs, hashes, timestamps). Never for headings.
- **Eyebrow typography uses sentence case 14px** — no all-caps tracked labels.
- **Line-heights tighten on display, relax on body**: 1.17 at display-xl, 1.50 at body — proportional to size.
- **Readability floor**: no running text below 14px; nothing below 12px anywhere.

### Font files

IBM Plex Sans is vendored offline in the app repo at `fair_turn/app/static/fonts`: `IBMPlexSans-Light.woff2` (300), `IBMPlexSans-Regular.woff2` (400), `IBMPlexSans-SemiBold.woff2` (600). No font is fetched from any external host. Streamlit loads them through `[[theme.fontFaces]]` (see Streamlit mapping) with `enableStaticServing = true` under `[server]`. There is no Mono file; the code font is Streamlit's default. Do not substitute Inter, Helvetica or a system stack for Plex Sans.

## Layout

### Spacing System

- **Base unit**: 4px.
- **Tokens**: `{spacing.xxs}` 4px · `{spacing.xs}` 8px · `{spacing.sm}` 12px · `{spacing.md}` 16px · `{spacing.lg}` 24px · `{spacing.xl}` 32px · `{spacing.xxl}` 48px · `{spacing.section}` 96px.
- Card interior padding: `{spacing.lg}` 24px on feature cards; `{spacing.xl}` 32px on product cards; `{spacing.xxl}` 48px on hero cards and CTA banners.
- Button padding: 12px vertical · 16px horizontal.
- Form input padding: 11px vertical · 16px horizontal.
- In Streamlit, `st.container(border=True)` is the feature-card; its padding is fixed by the framework (≈16px). Do not compensate with empty elements.

### Grid & Container

- 16-column grid at desktop, scaling to 8 / 4 columns at tablet / mobile.
- Max content width around 1584px. Streamlit `layout="wide"` for coordinator screens; `layout="centered"` for the tenant page.
- Card grids are 4-up at desktop, 2-up at tablet, 1-up at mobile; in Streamlit, `st.columns(4)` / `(2)` / `(1)`.

### Whitespace Philosophy

Precise alignment to a 4-pixel grid is the whitespace system. Sections separate via thin gray rows (`{colors.surface-1}`) or a `st.divider()` hairline rather than large vertical gaps. Coordinator screens are dense by design. The tenant page is the exception: one idea per paragraph, generous air.

## Elevation & Depth

| Level | Treatment | Use |
|---|---|---|
| 0 (flat) | No shadow, no border | Default for body type, headings |
| 1 (hairline) | 1px `{colors.hairline}` border on canvas | Cards, inputs, list items, dataframe |
| 2 (surface lift) | `{colors.surface-1}` background on canvas | Alternate-row stripes, sidebar, section bands |
| 3 (focus ring) | 2px `{colors.primary}` outline + 1px `{colors.hairline-strong}` underline | Focused input, focused button |

Depth is carried by surface change and 1px hairlines. No drop shadows.

### Decorative Depth

- **None.** The source system's soft-blue hero wash is removed with the brand. No gradient backdrops, no spotlight cards, no pastel section blocks.

## Shapes

### Border Radius Scale

| Token | Value | Use |
|---|---|---|
| `{rounded.none}` | 0px | Default — every button, card, input, container, alert box, chart mark |
| `{rounded.xs}` | 2px | Small badges (rare exception) |
| `{rounded.sm}` | 4px | Dropdown menus |
| `{rounded.md}` | 6px | (Used rarely; documented for completeness) |
| `{rounded.lg}` | 8px | (Used rarely; documented for completeness) |
| `{rounded.pill}` | 9999px | Status pills (rare) |

The system commits to flat 0px corners. Streamlit `baseRadius` and `buttonRadius` are both `0px`.

### Photography & Illustration Geometry

- Fair Turn uses **no photography and no illustration**. Do not add stock imagery, icons of houses, or any depiction of country, community or people.
- Where the source used image frames, Fair Turn uses data: a table, a chart, or a plain-language paragraph.

## Components

The component entries in the front matter are retained verbatim from the source. In a Streamlit implementation they map to standard widgets; entries with no Streamlit counterpart are marked *retained, unused*.

### Buttons

**`button-primary`** — Terracotta solid. `st.button(type="primary")`. Background `{colors.primary}`, text `{colors.on-primary}`, type `{typography.button}`, padding 12px 16px, rounded `{rounded.none}`. Hover `button-primary-hover` (`{colors.terracotta-hover}`); pressed `button-primary-pressed` (`{colors.terracotta-80}`). One primary button per screen.

**`button-secondary`** — Charcoal solid. *Retained, unused* (Streamlit has no charcoal variant; use `type="secondary"`, which renders as `button-tertiary`).

**`button-tertiary`** — White with 1px `{colors.primary}` border + terracotta text. `st.button(type="secondary")`. Default for every non-primary action.

**`button-ghost`** — Plain text, no border. `st.button(type="tertiary")`. Cancel, back, "show more".

**`button-danger`** — `{colors.semantic-error}` background, white text. *Retained, unused*: Fair Turn has no destructive actions; records are appended, never deleted.

### Cards & Containers

**`feature-card`** — `st.container(border=True)`. Canvas background, 1px `{colors.hairline}`, 0px radius. Job card, sign-off panel, one card per ranking.

**`feature-card-elevated`** — Same shape on `{colors.surface-1}`. Only via sidebar or `st.expander`.

**`product-card`**, **`hero-card`**, **`cta-banner`**, **`resource-tile`**, **`customer-logo-tile`** — *Retained, unused*. Marketing patterns with no place in a decision-support tool.

### Inputs & Forms

**`text-input`** / **`text-input-focused`** / **`text-input-error`** — `st.text_input`, `st.text_area`, `st.selectbox`, `st.date_input`. Background `{colors.surface-1}`, 0px radius, focus = 2px `{colors.primary}` bottom rule, error = 2px `{colors.semantic-error}` bottom rule with the message in red **text** (#a2191f) below.

**`newsletter-input`** — *Retained, unused*.

**Slider** (Streamlit-specific, follows `text-input` rules) — `st.slider`. Track `{colors.surface-2}`, fill and thumb `{colors.primary}`, value label `{typography.body-sm}` in `{colors.ink}`. Always show min and max labels in words, not just numbers.

### Tabs

**`product-tab`** / **`product-tab-selected`** — `st.tabs`. Default `{colors.ink-muted}` text with 1px hairline; selected `{colors.ink}` at `{typography.body-emphasis}` with 2px `{colors.primary}` underline. Padding 16px 20px.

### Navigation

**`top-nav`** — Streamlit's native header; the product name in plain `{typography.body-emphasis}` type, no mark. **`utility-bar`** — *Retained, unused*. Streamlit's sidebar (`{colors.surface-1}`) carries page navigation.

### Footer

**`footer`** — *Retained, unused* in Streamlit. If a footer is needed, a `st.caption` line in `{colors.ink-muted}` on canvas.

### Data display (Streamlit-specific, follows card and hairline rules)

- **Dataframe** — header `{colors.surface-1}`, `{typography.body-emphasis}`; cells `{typography.body-sm}`, 1px `{colors.hairline}`; numeric and ID columns in `{typography.mono}`, right-aligned. No zebra stripes wider than one row; no colour fills in cells except the highlight rules below.
- **Metric** — label `{typography.caption}` in `{colors.ink-muted}`, value `{typography.card-title}` in `{colors.ink}`. Delta colour follows the green/red **text** values. Use `delta_color="off"` where a change has no good/bad direction.
- **Alert boxes** — `st.info` blue, `st.warning` orange, `st.error` red, `st.success` green, each with its triplet. 0px radius. Body `{typography.body}`. One alert per section maximum.
- **Badge** — `st.badge`. Gray for "Unverified" / "Not recorded"; green for "Verified"; yellow for "Needs a human". Never red or orange badges in tables — red and orange belong to alert boxes.

### Empty and unverified fields

A field is never faked. The rules are the same on every screen:

- **Empty (no value recorded)** — the cell or metric shows an em dash `—` in `{colors.ink-subtle}` and, where space allows, the words "Not recorded" in `{typography.caption}`. Never `0`, `N/A`, `TBD`, a placeholder date or a grey bar.
- **Unverified (value exists but is not confirmed)** — the value is shown in `{colors.ink}` followed by a gray `st.badge("Unverified")`. Charts render unverified points as hollow marks. Rankings that depend on an unverified value show the "Needs a human" highlight on that row.
- **Missing in a chart** — a gap in the line. No interpolation, no zero.
- **Computed from partial data** — the metric shows the value and a caption "Based on N of M fields". Never a value alone.
- **Whole section unavailable** — a `st.info` box stating what is missing and who can supply it. Never an empty table with placeholder rows.

### Screen rules

Six screens. Rules only; no mockups.

**1. Triage board**
- Layout `wide`. Page title `display-md`. One `st.slider` labelled in words at both ends (for example "Weight urgency more" ↔ "Weight household health risk more"), the current value stated in a sentence beneath it.
- Ranked table: `st.dataframe`, rank column first in `mono`, job ID in `mono`, region as text (not colour), score to one decimal. The selected row uses `{colors.terracotta-10}`; no other row fill.
- Two side-by-side rankings: `st.columns(2)`, each a `feature-card` with `card-title` heading naming its weighting. Rows whose rank changed between the two carry an arrow glyph and the change in `mono`; rows flagged for review carry the yellow badge. Both tables share identical column order and width.
- The equity slider never re-sorts silently; a `st.caption` states "Ranking updated for weighting X".

**2. Job card**
- `feature-card`. Header: job ID in `mono`, region and locality as plain text, report date in `mono`.
- Report text at `body` (16px / 1.50), verbatim, never paraphrased. Source phrases the model relied on are highlighted with a light fill and a 2px bottom rule in the factor colour: urgency #da1e28, safety #b35c00, household health risk #6929c4, logistics #0072c3. Fill is the factor colour at 10% on canvas; the text stays `{colors.ink}`. Each highlight has a plain-text legend beneath the report listing phrase → factor, so colour is never the only channel. In Streamlit, implement highlights with `st.markdown` inline HTML spans (colour + underline only).
- Factor summary: four `st.metric` in `st.columns(4)`, one per factor, each with a caption stating which phrases drove it. Any factor with no supporting phrase shows `—` and "No source phrase found".
- The "Needs a human" box (`st.warning`, yellow triplet) appears when any input is unverified or any factor has no source phrase.

**3. Sign-off form**
- `st.form`. Fields top to bottom: coordinator name (`text_input`), decision (`selectbox`: Approve / Defer / Request more information), reason (`text_area`, required), date (`date_input`, defaults to today and says so).
- Read-only summary of the job above the form in a `feature-card`: job ID, ranking position under the current weighting, factors with unverified badges intact. Nothing pre-filled that the coordinator did not enter.
- Submit is the single `button-primary` on the page, labelled "Record decision". After submit, `st.success` with the audit reference in `mono`. Validation errors use `text-input-error` and red text under the field; no modal.

**4. Tenant answer page**
- Layout `centered`, max width ~720px. Reading level year 7: sentences under 20 words, one idea per paragraph, common words, active voice, no acronyms without the words first.
- Type: lead in `subhead` 20px / 1.40; body in `body-lg` 18px / 1.50 (line height never below 1.50; if the page is its own Streamlit app, set `baseFontSize = 18`). Paragraphs of three sentences or fewer with `{spacing.lg}` between them.
- Structure: what was reported; where it sits in the queue and why, in words ("Your repair is number 4 of 31 in your area this week"); what happens next; who to contact. Each block is an `st.container(border=True)` with a `card-title` heading phrased as the tenant's question ("When will someone come?").
- No table, no chart, no score. Numbers appear only inside sentences. `st.info` (blue triplet) for neutral explanations; never orange or red on this page.
- Empty fields follow the global rule, in plain words: "We do not have a date yet."

**5. Simulation page**
- Three Altair line charts stacked or in `st.columns(3)` at wide widths. Each chart: title `card-title`, x axis time, y axis a single measure, gridlines `{colors.hairline}`, axes `caption` in `{colors.ink-muted}`, stroke width 2px, marks at data points.
- Series colour: regions use the six region colours in fixed order; town/remote uses the pair with solid/dashed strokes; factor weights use the four factor colours. Never mix palettes on one chart.
- Legend as direct labels at line ends where possible; otherwise a legend below the chart, never over it.
- Scenario controls (`st.slider`, `st.selectbox`) in the sidebar or a `feature-card` above the charts; every control states its current value in a sentence. A `st.caption` below each chart names the assumption set.
- Projected values are dashed and labelled "Projected"; observed values are solid. Missing observations are gaps.

**6. Audit table**
- `st.dataframe`, full width, `mono` for timestamp (ISO 8601, local time zone stated once in a caption), audit reference, job ID and hash; plain text for coordinator, decision, weighting used.
- Rows are append-only and ordered newest first. No row is editable; no delete action exists.
- Filters (`selectbox` for coordinator, region, decision; `date_input` range) above the table in `st.columns`. Active filters restated in a `st.caption` sentence.
- "Unverified at decision time" is its own boolean column shown as a gray badge, not a coloured cell.
- Export is a `button-tertiary` labelled "Download CSV"; the file contains exactly the filtered rows.

## Do's and Don'ts

### Do

- Use `{rounded.none}` 0px on every button, card, input, alert and container.
- Pair Plex Sans weight 300 for display sizes (42px+) with weight 400 for body. Resist the urge to bold the headline.
- Reserve `{colors.primary}` terracotta for primary buttons, links, slider fill, selected-tab underline and focus. Do not use it as a card background, chart series or badge.
- Apply `letter-spacing: 0.16px` to body sizes.
- Use surface change (`canvas` → `surface-1`) and 1px hairlines for hierarchy. Skip drop shadows.
- Stick to sentence case for eyebrows, headings, labels and buttons.
- Show an empty field as `—` and "Not recorded". Show an unverified value with its gray badge.
- Say "household health risk" for the factor.
- Pair every colour with a text label, stroke style or annotation.

### Don't

- Don't round corners on buttons, cards, or inputs. Even 4px rounded corners break the look.
- Don't bold display headlines.
- Don't add atmospheric depth (gradient backdrops, drop shadows, overlays).
- Don't introduce a second accent. Terracotta is the only chromatic UI accent; status semantics use the documented triplets; data uses the chart palettes.
- Don't replace IBM Plex Sans without preserving `letter-spacing: 0.16px` and the weight-300 display treatment.
- Don't use pill-shaped buttons.
- Don't write all-caps tracked eyebrows.
- Don't fake a value: no placeholder numbers, dates, names or bars.
- Don't invent, depict or name Aboriginal communities, country or people in copy, sample data or imagery.
- Don't add imagery, icons or illustration of any kind.
- Don't use red or orange fills inside tables; they belong to alert boxes.

### Wording rule

- **No deficit language.** Never "vulnerable", "at-risk", "disadvantaged", "high-needs", "priority household" as a label for people. The factor is **"household health risk"** — it describes a risk in the dwelling's effect on health, not a category of person.
- Describe conditions and actions, not people: "a household where someone uses a nebuliser" not "a vulnerable tenant".
- Name the factor consistently in every surface: table headers, legends, metric labels, tenant copy ("household health risk"). Never abbreviate to "HHR" or "health".
- Coordinator screens: plain, direct, sentence case, second person for instructions ("Choose a weighting"). Tenant page: second person, present tense, no jargon, no scores.
- The tool supports a decision; it does not make one. Write "ranked for review", "suggested order", never "approved by the system".

## Responsive Behavior

### Breakpoints

| Name | Width | Key Changes |
|---|---|---|
| Max | 1584px | Max grid; gutters expand |
| Desktop-XL | 1312px | Default desktop layout |
| Desktop | 1056px | Card grid 4-up maintained |
| Tablet | 672px | Card grid 4-up → 2-up; nav becomes hamburger |
| Mobile | 320px | Single-column; display-xl scales 76px → ~32px |

### Touch Targets

- 48px minimum tap target. Buttons and inputs hold 48px on touch viewports.
- Top-nav links grow from 36px to 48px tap height on touch.
- Tab strip rows hold 48px tap height.

### Collapsing Strategy

- **Top nav**: links collapse to a hamburger overlay below 672px.
- **Utility bar**: hides below 672px.
- **Card grid**: 4-up → 2-up at 1056px → 1-up below 672px. Streamlit columns stack automatically below its mobile breakpoint; order columns so the most important is first.
- **Display type**: 76px scales toward 42px on mobile while preserving weight 300.
- **Footer**: 6-column → 3-column → 1-column.
- **Tenant page**: single column at all widths; it is the screen most likely read on a phone.
- **Dataframes**: scroll horizontally inside their frame; pin the rank and job ID columns.

### Image Behavior

- Not applicable: Fair Turn has no imagery. Charts scale to container width and keep a minimum height of 240px.

## Streamlit mapping

Values live in `tokens.json` (exactly the keys below) and in `.streamlit/config.toml` under `[theme]`. Light theme only; do not define `[theme.dark]`.

| Streamlit key | Token | Value |
|---|---|---|
| `primaryColor` | `{colors.primary}` | #b4462a |
| `backgroundColor` | `{colors.canvas}` | #ffffff |
| `secondaryBackgroundColor` | `{colors.surface-1}` | #f4f4f4 |
| `textColor` | `{colors.ink}` | #161616 |
| `borderColor` | `{colors.hairline}` | #e0e0e0 |
| `baseRadius` | `{rounded.none}` | 0px |
| `buttonRadius` | `{rounded.none}` | 0px |
| `font` | `{typography.body}` family | IBM Plex Sans (vendored, weights 300/400/600) |
| `headingFont` | `{typography.display-md}` family | IBM Plex Sans |
| `codeFont` | `{typography.mono}` family | Source Code Pro (Streamlit default; key left at default) |
| `chartCategoricalColors` | regions, fixed order | #8a6400, #007d79, #9f1853, #198038, #2d5bbf, #4d5358 |
| `chartSequentialColors` | sequential ramp | #fbf1ec … #561f10 (10) |
| `chartDivergingColors` | diverging ramp | #004144 … #6e2a17 (10) |
| `redColor` / `redBackgroundColor` / `redTextColor` | semantic red | #da1e28 / #fff1f1 / #a2191f |
| `orangeColor` / `orangeBackgroundColor` / `orangeTextColor` | semantic orange | #ff832b / #fff2e8 / #8a3800 |
| `yellowColor` / `yellowBackgroundColor` / `yellowTextColor` | semantic yellow / needs-a-human | #f1c21b / #fcf4d6 / #684e00 |
| `greenColor` / `greenBackgroundColor` / `greenTextColor` | semantic green | #24a148 / #defbe6 / #0e6027 |
| `blueColor` / `blueBackgroundColor` / `blueTextColor` | semantic blue | #0072c3 / #e5f6ff / #003a6d |
| `violetColor` / `violetBackgroundColor` / `violetTextColor` | semantic violet (reserved) | #8a3ffc / #f6f2ff / #491d8b |
| `grayColor` / `grayBackgroundColor` / `grayTextColor` | semantic gray | #8d8d8d / #f4f4f4 / #525252 |

Streamlit derives hover and active states from `primaryColor` itself; the terracotta-hover / -70 / -80 values above document the intended result and are used verbatim in Altair specs and any inline markdown.

Font faces and optional keys that tighten the match to the type scale (not part of `tokens.json`):

```toml
[server]
enableStaticServing = true

[[theme.fontFaces]]
family = "IBM Plex Sans"
url = "app/static/fonts/IBMPlexSans-Light.woff2"
weight = 300

[[theme.fontFaces]]
family = "IBM Plex Sans"
url = "app/static/fonts/IBMPlexSans-Regular.woff2"
weight = 400

[[theme.fontFaces]]
family = "IBM Plex Sans"
url = "app/static/fonts/IBMPlexSans-SemiBold.woff2"
weight = 600

[theme]
baseFontSize = 16
headingFontSizes = ["42px", "32px", "24px", "20px", "18px", "16px"]
headingFontWeights = [300, 400, 400, 400, 400, 600]
linkColor = "#b4462a"
linkUnderline = true
showWidgetBorder = true
dataframeHeaderBackgroundColor = "#f4f4f4"
dataframeBorderColor = "#e0e0e0"
codeBackgroundColor = "#f4f4f4"
```

Palettes with no theme key (town/remote pair, factor colours, needs-a-human) are read from `chart-palette.json` and passed to Altair `alt.Scale(domain=…, range=…)` explicitly.

## Iteration Guide

1. Focus on ONE component at a time and reference it by its `components:` token name.
2. Default body to `{typography.body}` at weight 400 with `letter-spacing: 0.16px`.
3. When introducing a new section, decide whether it sits on `{colors.canvas}` (default) or on `{colors.surface-1}` (alternate band). The two-surface rhythm is the rhythm.
4. Run `npx @google/design.md lint DESIGN.md` after edits.
5. Add new variants as separate component entries (`button-primary-pressed`, `text-input-error`).
6. Treat terracotta as scarce: links, primary button, slider fill, tab underline, focus. Anything beyond that is drift.
7. Resist rounded corners. If a designer pushes for 4px rounding, the system is shifting away from its base.
8. Any new colour must be checked against canvas (≥ 4.5:1 for text, ≥ 3:1 for marks) and recorded here with its ratio.
9. Any new label about people is checked against the Wording rule before it ships.

## Known Gaps

- Streamlit fixes the internal padding of containers, alerts and dataframes; the 24/32/48px card paddings from the source cannot be applied exactly without custom CSS, which this product does not use.
- The 48px touch-target rule depends on Streamlit's widget heights (≈40px by default). Not adjustable without custom CSS; noted as a known deviation.
- Streamlit renders `st.dataframe` cell highlights through pandas Styler; the terracotta-10 selected-row fill and hollow-mark "unverified" convention require Styler or Altair support and may be approximated with badges in a plain column.
- Contrast ratios above are computed for the hex values on `{colors.canvas}` or the named background; anti-aliased thin strokes at 1px may read lighter in practice. Use 2px strokes for chart lines.
- No logo or mark exists and none should be created. The product name is set in type.
- Source rules for marketing components (hero, CTA banner, footer, logo marquee) are retained but have no Streamlit implementation.
