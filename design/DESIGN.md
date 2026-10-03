# DESIGN.md — Readmark overrides

**This project does not use Tarik Base.** The look follows Australian Government caseworker tools
(AgDS, GOV.UK, MOJ), with the case file shown inside the question page. Tarık picked it on
2026-10-03, from `reports/2026-10-03-ui-references.md` → Round 2, hybrid 6.

## Reference
- **The screen:** `reports/screens/ui-references/mock-6-gov-filepanel.png` (its HTML is next to it).
  This is the eye-check reference until Tarık approves the built screen. From then on, that
  screen's screenshots in `design/screens/` are the reference.
- **The real interfaces behind it:** `1-agds-tasklist.png`, `1-agds-applayout.png`,
  `1-govuk-tasklist.png` and `1-moj-identitybar.png` in the same folder. Sources and dates are in
  the report.
- **What it keeps from direction 3:** the original page with the verified quote highlighted in
  place and labelled with its question (the answer-key idea).

## Look
- **Light only.** There is no dark mode (Tarık, 2026-10-03).
- **Type:** Arial / Helvetica, sans-serif for the interface, and a serif (Georgia) for the case
  file's own text, so the document reads as paper. Question title 30 px; body 16 px; never below
  13 px.
- **Palette** (mock 6's own, in the AgDS manner; not AgDS's exact tokens):

  | Role | Value |
  |---|---|
  | Header band | `#1a2b4a`, with a 6 px `#e66a50` rule under it |
  | Text | `#313131`; secondary text `#555` |
  | Primary button and links | `#00698f` (button shadow `#003c52`) |
  | Flag (needs a look) | `#b54800`, on a `#fdf1e9` warning box |
  | Highlight on the page | `#fff3b0` fill, with a `#b58a00` underline; the question tag is `#1a2b4a` with white text |
  | Lines and borders | `#bbb`; viewer background `#f3f4f6` |

- **Shape:** square-ish (radius 4 px on buttons and none on panels), 1 px borders, and no shadows
  except the button's bottom edge.

## Components
- **Header band:** the service name ("Readmark · Priority housing review · Darwin urban").
- **Identity bar:** "Applicant file A-0142", the case facts and the wait-time line, then the one
  primary button "Next: …" and the secondary "Sign decision".
- **Question list (task list):** "Decide these questions", the two counters, one row per question
  with a status in words, and "Sign decision" as the last row.
- **Question page:** the title, the policy sentence as an inset, a warning box saying why it is
  flagged, the file viewer, the outcome radios and "Save and next question".
- **File viewer:** one tab per cited page, "Open in full file (N pages)", and the page text with
  the labelled highlight.

## Rules kept from the Blueprint
- Colour is never the only signal. Every status has words and an icon.
- Text contrast is at least 4.5:1.
- No outcome is ever pre-selected.
