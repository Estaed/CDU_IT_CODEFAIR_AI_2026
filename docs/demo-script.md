# Demo script — three minutes, one story

For the Challenge Day pitch (10 minutes plus Q&A; this is the live part). **Restart the app
right before the demo** (its season results are cached per process). Start it with
no model and an empty local log (`data/audit/audit.jsonl` absent), on "This week's plan".
Numbers below are what the committed data shows; if a number on screen differs, read the
screen.

## 0:00 — The problem, on one screen

"This is Monday for the coordinator who schedules the licensed trades out of the
regional towns. The maintenance officer in a community can fix what needs no licence; an
electrician or a plumber has to come from town. 295 repairs wait for a crew. 116 are
past the NT time limit, 113 of them in remote communities. That is what ten
weeks of planning efficiency first left behind. A crew in Darwin fixes three repairs a
day; a trip to Top End R-01 spends three days driving there and back first. So the efficient
plan stays near town. That is the brief's trust twist, and here it is as numbers."

Point at the four numbers: **88 repairs this week, 105 overdue repairs still waiting.**

## 0:40 — The coordinator owns the trade-off

Click **Balanced**. "79 repairs, 9 fewer, and 23 more overdue households reached." Point at
the line chart: "Every setting is on this line. The top dot is Efficiency first. Notice the first
steps down are free: the same 88 repairs and twelve more overdue households reached.
After that, every
household costs repairs. The tool does not pick the point. The coordinator does."

Scroll to the map: green trips, red places still waiting with overdue repairs. In **Left
waiting**, read the top row: Top End R-01, 17 repairs, 11 overdue, waiting 52 days, "Other
trips came first". Then open **Every repair, in the order the plan takes them**: the brief's
"ranks jobs and explains why each sits where it does", one row per repair.

## 1:30 — A human decides, and it is written down

Open **Add or take out a trip**. Add Top End R-01 with the reason "Longest wait in the
region; go now". The box beside the map says what moved: which trip came in, which went out,
and the two numbers before and after. Sign: name and reason. "Every change and the reason are in the log,
with the planning day and the real time. If I change the plan now, I must sign again; the old
version stays."

## 2:00 — The tenant gets a real answer

Open **Ask about a repair**; the example "Remote, still waiting" is selected. Read the
headline and a few lines aloud: "Not in the week of 15 December. Repair JR-2025-00005, Big
Rivers R-03. NT policy says routine repairs in a remote home are done within 25 business
days; it is 28 business days past. A trip to your community takes 3.5 days of driving, there
and back, to fix 4 repairs. Under 'Most overdue first', a crew would come to you this week.
Your Community Housing Officer can ask the coordinator to add a trip." Then: "and once the
plan is signed, it names who signed and why."

## 2:30 — The AI only reads, and we checked it

Open **Reports**: one report the AI could not read fully; the urgency is empty and the
model's guess is not shown, so a person sets it. Then **Evidence**: "Over thirteen weeks,
Efficiency first leaves 199 repairs more than 300 km out still waiting; Balanced leaves 142 and
does more repairs in total. One more crew at Darwin cuts that to 127. The AI reads what
is broken and how urgent at 98 % and 97 %, every fact tied to the tenant's words, and all 20
manipulation attempts changed nothing but sending the report to a person."

## Likely questions

- **Is this real? Who is the user?** The trades sit in the regional towns and remote
  communities need road, plane or barge travel (Menzies 2023); NT policy already gives
  remote homes 2.5 times longer (FS17); in WA the first work order took 21.9 days remote
  against 10.6 in the city (WA Auditor General 2025); and the NT's own evaluator says the
  wait cannot currently be measured (Menzies 2023). Batching one trip per community and
  the crew numbers are our assumptions, and we say so.

- **Where do crew numbers come from?** Our assumption; NT does not publish them. They sit in
  one file, and the Evidence page shows how the result moves with one more crew.
- **Why not let the AI plan?** The plan is a formula a person can read and argue with; the AI
  is only used where language is the problem, reading the reports.
- **Is it fair?** It does not decide fairness. It shows the cost of each choice and makes the
  person who chooses sign it, and tells the tenant.
- **Could we pilot it?** Swap the report reader's input for the agency's intake and the crew
  table for the real roster; the log already has the two clocks an auditor needs.
