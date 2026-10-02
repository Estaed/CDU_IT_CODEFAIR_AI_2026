# Report brief — what the project report should say (rebuilt app, 3 October 2026)

For whoever writes the report PDF and the slides. The app was rebuilt on 2 October 2026
around a **weekly crew plan**; anything written about λ, "today's list", per-job accept or
reject, the visit plan or the clustered map describes the old version and must go. Section
headings follow `docs/report-requirements.md` (8 pages max, A4, Calibri or Arial,
"Discussion" is the ethics section, AI usage declaration in an appendix). Every number below
is in a committed file you can cite; regenerate with `scripts/export_report_tables.py`.

## Title page

Fair Turn: making the efficiency trade-off in remote NT housing repairs visible, owned and
explainable. AI Challenge 2026, brief 1 (housing maintenance triage). Team AIC014. Members
and roles. Date.

## Summary (150–250 words) — a draft to edit

> In the Northern Territory, the electricians, plumbers and refrigeration mechanics who repair
> remote public housing work out of five regional towns. A crew in town fixes about three
> repairs a day; a trip to a remote community first spends days on the road. Planning for the
> most repairs therefore keeps crews near town, and the households farthest away wait longest,
> while the NT's own evaluator reports that the wait cannot currently be measured. Fair Turn
> is a decision-support prototype for the coordinator who schedules those trades. An AI model
> reads tenants' free-text reports into typed facts, each tied to the tenant's own words; a
> transparent formula proposes the week's trips; one setting, from "Efficiency first" to
> "Most overdue first", decides what a trip is worth, and the screen shows the cost of each
> setting before anything is signed. The coordinator changes what they know better, signs with
> a reason, and every decision is logged. A tenant can ask why a crew is or is not coming and
> gets a plain answer that names the time limit, the trip, the setting and who signed. On a
> synthetic season over real NT geography, a balanced setting did more repairs than pure
> efficiency (1,084 against 1,074) and left 142 instead of 199 repairs more than 300 km from
> a base waiting after 13 weeks, at a cost of two points of remote on-time. We recommend a
> pilot that measures report-to-repair time and signs the weekly trade-off in the open.

## 1. Introduction

- The brief and its trust twist (`docs/task-briefs.md`, brief 1), in one paragraph.
- Background, all sourced (`docs/PRODUCT.md`, "Who uses it, and is the situation real?"):
  FS17 time limits (remote 2.5× town); trades in regional towns, plane/ferry/barge travel
  (Menzies 2023); WA Auditor General 2025 (21.9 vs 10.6 days to first work order); the
  Ombudsman's nine-month case (2012); Menzies §7.6.2 ("not possible to determine" the wait).
- Purpose and scope: one decision (where the trades go this week), one user (the trades
  scheduler), synthetic events on real geography; the AI reads, a person decides.

## 2. Methodology

- **Data.** 101 communities from BushTel and ABS under pseudonymous ids (real locations and
  road access; `data/raw/PROVENANCE.md`); 1,452 synthetic tenant reports, October to December
  2025, written by Claude Opus from seeded labels; 36 more by an OpenAI model as a
  cross-vendor check; 20 manipulation attempts; synthetic access closures.
- **Reading.** Claude Sonnet extracts fault type, urgency class, household health risk; each
  fact must be a literal phrase of the report or it is dropped and a person sets it;
  instruction-like reports always go to a person. Compared with a TF-IDF + logistic
  regression baseline; Wilson intervals.
- **Planning.** Need = time used of the NT limit (capped at three limits) + urgency class +
  household health risk. A trip's cost = driving days (400 road km a day) + work days (3
  repairs a day, at most 9 a trip). Priority per crew-day under the setting s:
  Σ((1−s) + s·need) / (work + (1−s)·driving). Each base fills its crews' week greedily.
- **Evaluation.** The planning week (29 Dec 2025) after 12 weeks of efficiency-first
  planning; and 13 weeks re-planned every Monday under each setting, measured by distance
  band; one extra crew at each base.
- **Assumptions, stated as such:** crew numbers (10 crews), productivity and speed; one
  community per trip; weekly cadence.

## 3. Findings (cite `data/build/report/`)

| This week (`this_week_by_setting.csv`) | Repairs | Overdue still waiting |
|---|---|---|
| Efficiency first | 88 | 130 (all remote) |
| 0.1 | 90 | 120 |
| Balanced | 77 | 108 |
| Most overdue first | 49 | 98 |

| 13 weeks (`season_by_setting.csv`) | Repairs | Town on time | Remote on time | Over 300 km still waiting |
|---|---|---|---|---|
| Efficiency first | 1,074 | 80 % | 51 % | 199 |
| Balanced | 1,084 | 90 % | 49 % | 142 |
| Most overdue first | 923 | 31 % | 36 % | 156 |

- The backlog after 12 weeks of efficiency first: 139 repairs past the NT limit, all remote.
- Efficiency first is not even the most efficient: 0.1 packs two more repairs and reaches
  ten more overdue households this week; over 13 weeks Balanced does more repairs.
- The cost is real: Balanced lowers remote on-time by two points (it serves the households
  already longest past the limit) and need-first collapses town service.
- One more crew at any base under Balanced: 127–137 far repairs waiting instead of 142
  (`one_more_crew.csv`). The setting decides who waits; capacity decides how long.
- Reading (`eval.json`): macro-F1 fault 0.979, urgency 0.969, health risk 0.983 against a
  baseline's 0.916 and 0.861; cross-vendor urgency 0.944 against 0.667; 100 % of facts tied
  to the report; 20 of 20 manipulation attempts changed the plan only by sending the report to
  a person. Upper bounds: synthetic text is cleaner than real reports.
- Figures: the plan page's trade-off line, the Evidence page's two bar charts, the tenant
  answer (`design/screenshots/readme/`).

## 4. Discussion (ethical, cultural and community impacts)

- **Who carries the cost of efficiency**, made explicit; the person who chooses signs it and
  the tenant is told. No setting is presented as "fair"; the tool shows the cost.
- **Human authority:** the plan is a proposal; adding or removing a trip needs a reason; a
  signature is versioned; facts the AI could not ground are set by a person, without the
  model's guess shown (anchoring).
- **Accountability:** the decision log with two clocks (planning day and real time).
- **Language:** no deficit language (the banned words are listed in
  `fair_turn/core/wording.py`; the factor is "household health risk"); tenant
  answers are tested at reading grade 7 or below.
- **Data:** synthetic events, pseudonymous community ids, no real names committed.
- **Cultural and community:** communities' own knowledge (a funeral, ceremony, a crew nearby)
  enters through the coordinator's changes; Housing Reference Groups advise on housing but
  not on repair order today (NT.GOV.AU) — a pilot could give them a view of the weekly plan.
- **Limits:** greedy planning, assumptions on crews, no multi-stop trips, synthetic closures,
  reading scores are upper bounds.

## 5. Recommendations

1. Pilot in one region with its real trade roster: replace the synthetic reports with the
   contractor's tasking export and measure report-to-repair time, which the NT cannot measure
   today (Menzies 2023 §7.6.2).
2. Publish the weekly setting and its reason to Housing Reference Groups.
3. Use the one-more-crew comparison when contracts are renewed (Healthy Homes contracts run
   15–22 months, Grealy et al. 2025).
4. Keep the AI to reading reports, with the phrase rule and a person for every ungrounded
   fact.

## References (from `reports/2026-09-12-research-*.md`)

- NT DHLGCD, fact sheet FS17 *Repairs and maintenance*, 10/2025.
- Menzies School of Health Research, *Healthy Homes Monitoring and Evaluation Project — Final
  Report*, September 2023.
- Grealy, Su & Thomas (2025), *Int. J. Environ. Res. Public Health* 22(6):836.
- WA Office of the Auditor General, *Management of Housing Maintenance Information*, 6 August 2025.
- Commonwealth Ombudsman, *Remote Housing Reforms in the Northern Territory*, June 2012.
- NT TFHC, *Tenancy Management Support Services Handbook*, v1.3, June 2021.
- BushTel community data (NT Government), ABS; Natural Earth.
(URLs are in the two research files.)

## Appendix: AI usage declaration (facts to state)

- Synthetic reports written by Claude Opus; the challenge set by an OpenAI model; reports read
  by Claude Sonnet (build time and live intake); local models benchmarked and not adopted
  (`MODELS.md`).
- Code written with AI coding assistants (Claude Code, Codex) under the team's direction;
  every change passed the project's test gate (`scripts/gate.py`).
- No model plans, ranks or writes to tenants; those are deterministic templates.
