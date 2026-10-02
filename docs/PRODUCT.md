# Fair Turn — what it is and why it works this way

Written 2026-10-02, when the product was rebuilt around the weekly crew plan. It replaces
`docs/archive/PRD.md` as the description of what the app does; the archive still documents
how the synthetic data was made (its sections 5 to 7), which did not change.

## The brief, in one line

*How might we help a housing maintenance coordinator prioritise urgent repairs across
remote NT communities without "efficiency" quietly pushing remote tenants to the back of
the queue?* Trust twist: it is always cheaper to fix the town first; make the equity
trade-off visible, let a human own it, and give a tenant a real answer
(`docs/task-briefs.md`).

## Why the first version was rebuilt

The first version ranked single jobs with `score = need - λ × travel cost` and asked the
coordinator to accept or reject each of today's jobs. Two things were wrong with it:

1. **Efficiency was modelled in the wrong place.** Travel cost was charged to every job, as
   if a crew drove out separately for each. In practice the cost is the trip: a crew drives
   to a community once and fixes several repairs there. A per-job penalty punishes a remote
   household even when a crew is already going.
2. **The trade-off barely showed.** Each region had its own crew, so town and remote jobs
   never competed for the same crew, and moving λ changed little. On the default screen
   the effect line read "No job changes", the opposite of the story the brief asks for.

## Who uses it, and is the situation real?

**The user is the scheduler of the licensed trades**: the electricians, plumbers and
refrigeration mechanics who work out of the regional towns (Darwin, Katherine, Tennant Creek,
Alice Springs, Nhulunbuy). That is where the trade-off in the brief actually happens, and the
public record supports each part of it (sources in `reports/2026-09-12-research-*.md`):

- A tenant's report goes to the maintenance contractor's tasking system, through the 1800
  line or the Community Housing Officer (NT Remote Housing Handbook §3.2.1, June 2021).
- The Housing Maintenance Officer in a community fixes what needs no licence and makes
  things safe when a contractor is not available (FS17, 10/2025). Licensed work needs a
  trade from somewhere else.
- Where providers sit in regional towns, "significant travel costs are involved", and some
  communities need plane, ferry or barge travel (Menzies School of Health Research, Healthy
  Homes evaluation, 2023).
- NT policy already allows remote homes 2.5 times longer: urgent in 5 business days against
  2 in town, routine in 25 against 10 (FS17).
- Delays are real and measured nearby: in Western Australia the first work order took 21.9
  days in remote areas against 10.6 in the city, and urgent targets were met 74 % of the time
  (WA Auditor General, August 2025). A wet-season access case in the NT ran nine months
  (Commonwealth Ombudsman, 2012).
- And the NT cannot see the wait: its own evaluator found "it is not possible to determine"
  the time from a tenant's report to the finished repair (Menzies 2023 §7.6.2).

What is **our assumption**, not a source: that the trades batch their remote work as one
trip per community (the contracts' per-community work plans imply it), and the crew numbers,
repairs per day and driving speed. Since 2021 most Healthy Homes contracts cover one to three
communities and are often held by local Aboriginal Business Enterprises; Fair Turn is for the
part of the work those local teams cannot do without a licensed trade from town.

## The model

- **The decision:** where each base's licensed trade crews go this week. One decision, one
  user (the regional trades scheduler), signed.
- **A trip is the unit.** Ten crews at five bases (Darwin 3, Katherine 2, Alice Springs 2,
  Nhulunbuy 2, Tennant Creek 1), five crew-days each. A crew in its own town fixes 3
  repairs a day. A trip to a remote community costs the road days there and back (400 road
  km a day, in half days) plus the work days, and carries at most 9 repairs.
- **Need**, per repair: how far into or past its NT time limit (FS17), how serious, and the
  household health risk read from the report. Unchanged from the first version.
- **One setting, s from 0 to 1**, decides what a trip is worth per crew-day:
  `priority = Σ((1 − s) + s × need) / (work days + (1 − s) × driving days)`.
  At **Efficiency first** (0) every repair counts 1 and driving counts in full, so the most
  repairs per crew-day wins: the brief's efficiency, made exact. At **Most overdue first**
  (1) repairs count by need and driving is not held against a trip. **Balanced** is 0.5.
- **Each base fills its crews' week**, highest priority first, packing each trip onto the
  crew with the fewest days that still fit it. What is left waits, with its reason: below
  the cut, road closed, trip full, or taken out by the coordinator.
- **Emergencies** (Immediate) go to the make-safe contractor within 4 hours and are outside
  the plan. **Reports the AI could not read** wait for a person and are outside the plan
  until a person sets the missing fact.

## What the coordinator sees and does

1. The backlog in one sentence, with how many repairs are past the NT time limit and how
   many of those are remote.
2. The setting, and its cost in four numbers against Efficiency first: repairs this week,
   overdue repairs still waiting, remote communities visited, crew-days driving. A line
   chart shows every setting from 0 to 1, so the coordinator sees the whole trade-off,
   not one point.
3. The map and two lists: trips, and who is left waiting and why. The coordinator can add or
   take out a trip, each with a reason.
4. A signature with a name and a reason. Every change and the reason go to the decision
   log; signing again after a change makes a new version.

A tenant (or housing officer) types a repair number and is told whether a crew comes this
week; if not, the time limit, how far past it, the trip length, the setting and its
meaning, whether another setting would have sent a crew, and who signed with what reason.

## What the numbers show (synthetic data, our crew assumptions)

Planning day Monday 29 December 2025, after 12 weeks planned efficiency first: 336 repairs
wait for a crew, 139 are past the NT time limit, and all 139 are remote
(`data/build/report/this_week_by_setting.csv`):

| Setting | Repairs this week | Overdue repairs still waiting |
|---|---|---|
| Efficiency first | 88 | 130 (all remote) |
| 0.1 | 90 | 120 |
| Balanced | 77 | 108 |
| Most overdue first | 49 | 98 |

Efficiency first ranks trips by repairs per crew-day; it is a rule, not a guarantee of the
most repairs, because each base fills its week greedily. A little weight on need (0.1) packs
two more repairs **and** reaches ten more overdue households. Past that, every overdue
household reached costs repairs.

Thirteen weeks, every Monday planned under one setting
(`data/build/report/season_by_setting.csv`):

| Setting | Repairs | Town on time | Remote on time | Over 300 km, still waiting at the end |
|---|---|---|---|---|
| Efficiency first | 1074 | 80 % | 51 % | 199 |
| Balanced | 1084 | 90 % | 49 % | 142 |
| Most overdue first | 923 | 31 % | 36 % | 156 |

Pure efficiency is not even the most efficient over a season: it treats a fresh routine
repair like an urgent one. Balanced does more repairs and leaves 57 fewer far repairs
waiting, but remote on-time falls two points: it spends crew time on the households already
longest past the limit, which can no longer be on time. Pure need-first collapses town
service and leaves more far repairs waiting than Balanced. One more crew at any base, under
Balanced, leaves 127 to 137 far repairs waiting instead of 142 (`one_more_crew.csv`): the
setting decides who waits, and crews decide how long.

## What is deliberately not claimed

- Crew counts, repairs per crew-day and driving speed are assumptions; NT does not publish
  them. The pattern is what a pilot should test, not a forecast.
- A trip visits one community; multi-stop circuits are not modelled.
- Each base fills its crews' week greedily. It is fast and explainable line by line, not
  optimal: a slightly different setting sometimes packs a repair or two more.
- Access closures are synthetic; a community counts as cut off for the week when its access
  is closed on at least three weekdays.
- NT time limits skip the public holidays in the window (25 and 26 December, 1 January),
  but a crew's week is still counted as five days in the New Year week.
- Every report is treated as work for a licensed trade. In practice the community's
  maintenance officer does part of it (what needs no licence); which fault types fall on
  which side is not published, so we did not invent a split. A pilot would take it from the
  contractor's own job codes.
- Weekly planning: remote urgent jobs reported midweek wait for Monday. Real dispatch is
  more flexible; the town days in the model are flexible for that reason.
- The AI's reading scores (fault 98 %, urgency 97 % macro-F1) are on synthetic text written
  to the NT definitions, an upper bound.

## Rules that did not change

The AI only reads reports; the plan never reads model text. A fact is shown only with the
tenant's words it came from. Instruction-like reports go to a person. No model confidence
anywhere. No deficit language. No real community names outside `data/raw/`. Every policy
number and assumption is defined once in `fair_turn/core/constants.py` with a row in
`constants.md`. The app and the tests run with no network and no model.
