# Pre-Blueprint review of the brief 6 design (2026-10-03)

**Sources:**
- An independent read-only reviewer (Opus) read `notes.md`, `design/mock-v0.html` and the reports.
- The main loop added its own checks: the real Priority housing and Eligibility policy text read via
  r.jina.ai, a Jev load test, and Gmail.

This is input, not a decision. Items marked **Tarık** need his call; items marked **fixed in notes**
were consistency errors in Eko's drafts.

## Checks by the main loop
- **Real decision flow** ([Priority housing v2.04](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf), approved 2024-03-26, read 2026-10-03):
  1. Meet eligibility (with "some discretion for extreme situations").
  2. Fall into one of four urgent-need categories: a young person transitioning from care, at risk of
     homelessness, serious medical or social problems, or domestic or family violence.
  3. "Prove their urgent need … provide documentation that supports their claim".
  4. An interview if more information is needed.
  5. A written determination, then appeal.

  Decisions are made by **delegated officers** (§4). Priority applies only to "urban social housing
  applicants" (§2).
- **Eligibility** ([Eligibility v7.1](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf), approved 2024-06-27, read 2026-10-03):
  - **Urban applicants:** "must also qualify under additional income based criteria which are
    specified in the Income and Assets policy".
  - **Other criteria:** property ownership (§3.1, with an exemption on the delegate's approval for
    people fleeing DFV), residency (§3.2), age (§3.3), debt (§3.4), and unsatisfactory former
    tenancies (§3.5).
- **Jev load test** (2026-10-03):
  - 120 single calls with 16 threads: all HTTP 200, 3.4 s wall, p50 0.34 s, p95 0.98 s.
  - One call holding 20 passages and 20 `score` questions: 0.35 s and about 2,170 input tokens. The
    DFV passage scored top at 2.65; the 19 fillers scored ≤ 0.03.
  - A full scan therefore needs a few dozen calls and takes seconds.
- **Registration:** the AI Challenge confirmation (2026-09-03) gives team ID **AIC014** and names no
  brief. It links a "submit details" form whose contents are unknown.

## Findings, most severe first
1. **BLOCKER — Tarık. The errors the demo catches are not produced by v1.**
   - All planted errors sit in a hand-written "plain AI" summary that v1 never generates.
   - A good writer with a goal prompt will probably cite §3.4, notice the March ledger and cite
     p.51, so little turns red.
   - The mock's red claim "not eligible because of arrears" is an eligibility conclusion, which our
     own writer is not allowed to make.

   **Fix:** a v1 input called *summary under audit*. Freeze one summary produced by a named plain
   setup (a one-line "summarise this file" prompt on a weaker or Copilot-style model), split it into
   claims and run the same checks. The mutation set uses the same path. Never present a hand-written
   summary as "plain AI".
2. **BLOCKER — fixed in notes. The stale-ledger trap needs the cross-passage check, which was marked
   "if time allows".**
   - A claim checked only against its own cited passage (p.8) comes back supported.
   - The smoke test's stale row paired the claim with p.23, which the per-claim check would never do.

   **Fix:** contradiction pairs are core v1 (top 3–5 passages per clause, a pairwise `choice`), and
   the contract allows 1..n citations per fact.
3. **BLOCKER — Tarık. The "flip to accept" ignores eligibility.**
   - §3.4 removes only the debt barrier.
   - Urban eligibility still needs the income and assets criteria.
   - The mock itself says "no income statement found", and by our own rule "not in file" means a
     request, not an accept.

   **Fix:** the moment becomes "the reason to reject collapses on screen". The correct demo outcome is
   either "request income evidence" or an accept made defensible by putting an income statement in
   the file.
4. **MAJOR — fixed in notes. Whose debt is the $2,400?**
   - §3.4 covers only a debt owed to the CEO (Housing).
   - **Fix:** in the facts table, p.8 is a former public-tenancy debt from the tenancy that ended in
     2023 by agreement with a balance outstanding, and p.30 says the same.
5. **MAJOR — Tarık. Three checker names, and Jev chosen on n=3.**
   - The checker is named three ways: System says Claude, Decisions say Jev, and the mock says
     MiniCheck.
   - **Fix:** use the single name Jev, with Claude as the fallback. Measure Jev against Claude as
     checker on about 50 external SummEdits pairs (CC BY) at the start of the build. That one task
     also supplies the external number for #10.
6. **MAJOR — fixed in notes. Reproducibility.**
   - Jev is waitlisted, Claude is paid, and the PDFs are versioned and behind Cloudflare.
   - A cache of a full scan would contain policy text, which undoes the no-bundling decision.
   - **Fix:**
     - Make a replay cache of every model response the README default.
     - Pin each PDF by version and SHA-256 and fail loudly on a mismatch.
     - Store offsets or hashes in the cache, never policy text.
     - Report the variance across two Jev runs.
7. **MAJOR — fixed in notes. The status words collide.** Three separate lists replace them:
   - **Claim checks:** quote not found / checker disagrees / contradicted by another passage / supported.
   - **Coverage:** possibly missed / no evidence in file.
   - **Clause outcome, set by the officer only:** met / not met / cannot decide yet, which means
     request information.
8. **MAJOR — fixed in notes. The "possibly missed" scan was underspecified.**
   - Scan only the approved decisive clauses.
   - Set the threshold on one gold file before the evaluation, dedupe by fact, and cap required items
     at ≤ 8; the rest are "suggested".
9. **MAJOR — fixed in notes. "Opened" was presented as "read".**
   - The Goal wording now says "opened".
   - Passages open one at a time, and time-in-view is logged.
   - The tag says "Opened".
10. **MAJOR — Tarık. The evaluation is circular.**
    - **Fix:** a held-out file written by a teammate before the first pipeline run, plus about 50
      SummEdits pairs for an external checker number, both inside v1.
    - Freeze the checklist before writing any file, and print n beside every number.
11. **MAJOR — Tarık. The timing test cannot answer the riskiest assumption.** Its flaws: reading the
    same file twice, contaminated subjects, traps already flagged, a wrong baseline, and n ≈ 3.
    - **Fix:**
      - Two different files, in counterbalanced order.
      - Baseline: the full file plus a plain summary.
      - Measure correct decision and minutes.
      - Leave one trap unflagged.
      - Report it as a pilot, with n stated.
12. **MAJOR — Tarık. The scope does not fit 4.5 days.**
    - **Fix:**
      - One full 60-page demo file.
      - Short (10–15 page) evaluation files made from the same facts table.
      - Freeze the numbers for the teammate by 7 Oct.
      - Dispute becomes a text field on the record.
13. **MAJOR — Tarık, outward. The report writer may still be working from Fair Turn.**
    - `archive/v2-weekly-plan:docs/report-brief.md` (3 Oct 00:54) describes Fair Turn, brief 1,
      team AIC014.
    - **Fix:**
      - Tell the teammate today.
      - Write a one-page brief 6 report brief.
      - Ask Thi (who registered) whether the "submit details" form named a brief; if it did, send
        the organisers one line.
14. **MINOR — fixed in notes.** `verify_spans.py` (78 lines) only matches substrings with whitespace
    normalised. The number and date checks are new code; negation counting is dropped because it is
    brittle.
15. **MINOR — fixed in notes.** Smaller contradictions:
    - "one policy" vs five;
    - "ask the organisers" vs "not asked";
    - the omission source (writer list vs Jev scan);
    - the plain tab's role;
    - "show the passage, not an AI explanation" vs the mock's "why" lines;
    - the unused wait-time CSV;
    - "15 files" vs one demo file;
    - the token estimate (text vs PDF input).

## Independent quality assessment (if v1 as scoped is built and works)

| Criterion | Rating | Reason |
|---|---|---|
| Datasets | medium | Real NT clauses land well; but the file, traps, labels and checklist are all ours, with no independent ground truth yet |
| Creativity | good | The reading gate, omission map and receipt go beyond NotebookLM; each piece exists in research |
| Technical | medium | The second key is an unbenchmarked API, the cross-passage check was optional, calibration rests on 3–5 files, and the errors shown are not the pipeline's own |
| Context and practicality | good | Context is strong; practicality is weaker: case text goes to two US cloud APIs, one waitlisted, and the time saving is unproven |
| Ethics | good, near strong | The officer decides and not-in-file leads to a request; but DFV text goes to an early-access vendor with no known DPA, "read" was overclaimed, and the log is still monitoring |
| Presentation | strong if #1 and #3 are fixed, medium if not | A real clause flipping the answer is memorable, but one NTG question can undo a staged summary |

- **Real-world readiness:** a research prototype, about 6–12 months from a pilot. The three biggest
  gaps:
  - data handling: two cloud services, one in early access;
  - real documents: scans, emails and forms, plus integration with case systems and maintaining the
    checklist;
  - no evidence yet that it saves time or improves decisions on real-shaped files.
- **The single change that would most raise the result:** audit a real summary from an NT-plausible
  tool and report "caught X of Y errors in a summary we did not write, missed Z".
- **The single thing most likely to lose it:** being caught staging in Q&A (a hand-written summary,
  a premature "accept"). Close behind: scope overrun that leaves the teammate's report without numbers.
