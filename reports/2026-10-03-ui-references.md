# UI references for the review screen: four directions (Readmark, 2026-10-03)

**Question.** Which real interface should Readmark's review screen look like? The handoff
(`reports/2026-10-03-handoff.md` → Session 2) asks for 3–4 directions, each with real screenshots,
a Readmark version, its source and date, and its cost. Tarık picks one. The `tasarim` skill and
Tarik Base are not used (Blueprint → Decisions, light default row).

**How it was made.** Candidates came from `reports/2026-10-03-ux-guided-review.md` and
`reports/2026-10-03-ui-patterns-and-logic-brief6.md`, plus Everlaw. The product screenshots are the
vendors' own help-page images, downloaded with Playwright. The government ones are the live
design-system examples, rendered and captured with Playwright. Each Readmark version is a static
HTML mock (`reports/screens/ui-references/mock-*.html`, 1440×900) built from the demo case A-0142:
the Debts question, pages 8 and 23, as `.tmp/explain/ekran-durumlari.html` shows them. The mocks
are pictures, not app code. Every mock keeps what the screen must show: 8 questions with a status,
both counters, the next step, the check label in words (never colour alone), the three outcomes
with no pre-fill, required passages, and sign-off.

All images are in `reports/screens/ui-references/`. Read dates are 2026-10-03.

---

## 1. Australian Government caseworker (AgDS, GOV.UK, MOJ)

**What it is.** The design systems that government staff tools are built from. A dark header, a
white page, one column of plain words, a task list where each row has a status, and one big
primary button.

| Real screenshot | Source |
|---|---|
| `1-agds-tasklist.png`: "Complete these tasks, 0 of 4 completed", status icons in words | https://design-system.agriculture.gov.au/components/task-list (live example) |
| `1-agds-applayout.png`: the app shell for signed-in staff tools (header, sidebar) | https://design-system.agriculture.gov.au/components/app-layout |
| `1-govuk-tasklist.png`: task list with "Completed / Incomplete" tags | https://design-system.service.gov.uk/components/task-list/ (live example) |
| `1-moj-identitybar.png`: identity bar with the case name and its actions | https://design-patterns.service.justice.gov.uk/components/identity-bar/ (live example) |

**Readmark in this style:** `mock-1-government.png`. Left: "Decide these questions" as a task list,
with Sign decision as the last row, "cannot start yet". Right: one question per page, with the
policy sentence as an inset, a warning box saying why it is flagged, the two cited pages side by
side, large radio buttons, and "Save and go to next question".

- **Strengths:** the most credible look for an NT officer (AgDS is an Australian Government
  system); accessibility and plain language come with the pattern; the next step is always one
  button.
- **Conflict with Blueprint (stop and decide):** the mock shows only the cited passages, not the
  file. The Blueprint says "the case file is the reading surface". Taking this direction either
  changes that decision or adds a "view in file" link that opens the page in the full file.
- **Cost:** high. It changes the layout, not just the colours. It means a new per-question page
  and a new task list in `web/app.js` (60 KB today) and a new `theme.css`. About 1.5–2 days with
  otopilot. AgDS is React, so we copy the look only; the GOV.UK crown and font are restricted to
  gov.uk and are not used.

## 2. Legal review workstation (Relativity, Everlaw)

**What it is.** The tools lawyers use to review thousands of documents: the document in the
centre, a list on the left, a "coding" panel on the right where the reviewer records a decision,
and "previous / next" paddles. Dense, small type, grey frames, a white page in the middle.

| Real screenshot | Source |
|---|---|
| `2-relativity-pdfviewer.png`: document list, viewer with hit highlights, "Coding Layout" panel | https://help.relativity.com/RelativityOne/Content/Relativity/Viewer/Viewer.htm (image dated Sept 2026) |
| `2-everlaw-review.png`: toolbar, context panel, hit highlighting, coding panel, navigation paddles | https://support.everlaw.com/hc/en-us/articles/204791759 (Classic Review Window) |
| Review Center queue: "Total Remaining", "Save and Next" (text only) | https://help.relativity.com/RelativityOne/Content/Relativity/Review_Center/Reviewing_documents_using_Review_Center.htm (modified 2026-09-16) |

**Readmark in this style:** `mock-2-workstation.png`. Left: a table of questions with "Check" and
"Outcome" columns, then the pages that have highlights. Centre: the file page on a grey
background, with the highlight labelled "Debts · Required" and "Prev flag / Next flag" paddles.
Right: the question, why it is flagged, the passages that must be opened, the outcome, disputes,
and "Save & next question". Counters at the top.

- **Strengths:** this is today's three-column layout (Blueprint layout B) in a known professional
  costume, so the Blueprint stays as it is; review tools are exactly "read a document, record a
  decision"; cheapest.
- **Weakness:** the most text per square centimetre. Tarık already found a dense screen hard to
  follow, and this direction does not fix that on its own.
- **Cost:** low. Mostly `web/theme.css`, plus a few small markup changes (the table on the left,
  the paddles). About half a day.

## 3. Answer key in the margin (Relativity annotations, Elicit quotes)

**What it is.** The document is the whole screen. Each highlight has a note in the margin, joined
to it by a line, the way a marked exam paper or a commented Word file looks. Relativity draws
"leader lines" from annotation cards to the highlighted text. Elicit steps through supporting
quotes with "1 of 6, Previous, Next".

| Real screenshot | Source |
|---|---|
| `3-relativity-annotations.png`: comment cards in the right margin, a leader line to the highlighted text | https://help.relativity.com/RelativityOne/Content/Relativity/Viewer/Viewer.htm (image dated May 2024, on the page read 2026-10-03) |
| `3-elicit-quotes.png`: "Supporting quotes from paper, 1 of 6, Previous / Next" | https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit ("updated over 2 weeks ago") |

**Readmark in this style:** `mock-3-margin.png`. Top: the 8 questions as numbered circles, then
Sign, the counters, and "Next highlight". Left: page thumbnails with a count of flags. Centre:
the page itself. Right margin: the question card beside its highlight, joined by a line. The card
says why it is flagged, "Open page 23 beside this", the three outcome buttons, and "highlight 1 of
2 for this question".

- **Strengths:** this is Tarık's answer-key idea (IELTS keys, Blueprint 2026-10-03), taken
  furthest. The officer looks in one place, beside the evidence. It has the least text on screen
  and is the most distinctive look for the pitch.
- **Weaknesses:** the whole-case overview shrinks to 8 circles, so a circle needs a hover or a
  tooltip with the question name. Cards must stay level with their highlight while the page
  scrolls, which is the one hard piece of code. At 1280 wide, the page and the margin compete for
  space.
- **Cost:** medium. A new layout in `web/app.js` and `theme.css`, plus the card-alignment code and
  its Playwright check at 1280 and 1440. About 1 day.

## 4. Case record with a stage bar (Dynamics 365, Salesforce Public Sector)

**What it is.** The enterprise case tools many agencies run on. A record header with key numbers,
a chevron "stage bar" across the top (each stage lists its required steps and gates "Next
stage"), tabs below, and cards of label/value fields.

| Real screenshot | Source |
|---|---|
| `4-dynamics-bpf.png`: stage bar, the steps in the active stage, "Next Stage" | https://learn.microsoft.com/en-us/power-automate/business-process-flows-overview (2026-08-15) |
| `4-salesforce-review.jpg`: caseworker "Review Application" with Check Eligibility and summary fields | https://trailhead.salesforce.com/content/learn/modules/benefit-management-with-public-sector-solutions/process-benefit-applications |

**Readmark in this style:** `mock-4-caserecord.png`. Header: A-0142, both counters, and the
Darwin wait-time line. Stage bar: Open flagged passages → Decide 8 questions → Reason & sign →
Decision record. The active stage lists its passages. Below: tabs (Questions, Case file, Policies,
Decision record), a question card with fields, and the file page beside it.

- **Strengths:** "where am I in the process" is answered by the bar. It looks like what an agency
  would actually buy.
- **Weaknesses:** it forces an order (read first, then decide), while the officer thinks question
  by question. The earlier research (`ux-guided-review` §2.2) shows users want to move between
  stages freely, and that whatever looks clickable must be. It also looks like a CRM, not a
  reading tool, and the file moves to a tab.
- **Cost:** medium to high. A stage model in `web/app.js`, tabs, and a new `theme.css`. About
  1–1.5 days.

---

## Comparison

| | 1 Government | 2 Workstation | 3 Margin answer key | 4 Case record |
|---|---|---|---|---|
| File as the reading surface (Blueprint) | no, unless changed | yes | yes, most | partly (a tab) |
| Text on screen | low | high | lowest | medium |
| NT/government credibility | highest | medium | medium | high |
| Distinctive for the pitch | low | low | highest | low |
| Cost | ~1.5–2 days | ~0.5 day | ~1 day | ~1–1.5 days |

**Recommendation: 3, the margin answer key.** It is the only direction that solves Tarık's
complaint (too much text, cannot follow) and his own idea at the same time, without touching the
Blueprint, and it fits before 8 Oct. Two things are borrowed from 1: the plain-word status under
each question name, and one primary "next" button. **Fallback: 2,** if time runs short: it is half a
day and keeps today's layout.

## After the pick
- `design/DESIGN.md`: "This project does not use Tarik Base. Reference: <direction>, with the
  screenshots in `reports/screens/ui-references/`."
- The interface rework becomes a task file (`plan-wave`). Its eye-check reference is the chosen
  mock and its real screenshots.

## Unknown
- The costs are estimates from the size of `web/app.js` and `theme.css`; they are not measured.
- No real officer has seen any of the four mocks. The 10-second "name the next step" check from
  the Blueprint has not been run on them.
