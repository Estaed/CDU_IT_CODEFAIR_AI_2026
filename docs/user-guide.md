# Fair Turn — User Guide

Five minutes, for a new coordinator, a teammate, or a judge. `docs/PRODUCT.md` has the
model behind each number.

## 1. What Fair Turn is

Fair Turn helps a housing maintenance coordinator in the Northern Territory decide where
the licensed trades go this week: the electricians, plumbers and cooling mechanics who
work out of the regional towns. The maintenance officer in a community fixes what needs
no licence; the rest waits for a trade from town.

A crew in its own town fixes three repairs a day. A trip to a remote community first
spends days on the road. So the plan with the most repairs keeps crews in town, and remote
households wait longest. That is the "efficiency" the brief warns about.

Fair Turn shows that trade-off as numbers, lets the coordinator choose it, and writes the
choice down. The AI only reads the tenants' reports. A plain formula proposes the plan. A
person decides and signs.

## 2. The four pages

- **This week's plan.** The coordinator's page: the setting, the trips, who is left
  waiting, and the signature.
- **Reports.** What the AI read from each report, next to the tenant's own words. Reports
  the AI could not read wait here for a person. New reports are added here.
- **Ask about a repair.** A tenant, or the housing officer helping them, types a repair
  number and gets a plain answer.
- **Evidence.** For judges: thirteen weeks planned under each setting, how well the AI
  reads, and the decision log.

## 3. A coordinator's Monday, step by step

1. Open This week's plan. Read the blue box. It says how many repairs wait, and how many
   are past the NT time limit.

2. If a yellow box says a report needs a person, open Reports. Read the report. Set what
   is missing. Say why you are sure. Save it. The repair joins the plan.

3. Choose what decides where crews go. Most repairs fixes the most this week. Most
   overdue first sends crews to the homes that have waited longest past the time limit.
   Balanced is in between.

4. Read the four numbers and the line under them. They show what your choice costs: fewer
   repairs this week, or more overdue homes reached.

5. Look at the map and the two lists. Green places get a crew. Red places wait, with
   repairs past the time limit. Each place says why it waits.

6. You know things the plan does not. Add a trip, or take one out. Give a reason each
   time.

7. Sign the plan with your name and a reason. Your reason is what a tenant is told.

8. Open the run sheet. It shows each crew, Monday to Friday.

If you change the plan after you sign, sign again. The old version stays in the log.

## 4. Adding a report

Open Reports, then Add a new report. Paste the tenant's words and pick the community.

To read it with a model, choose claude or ollama in "Who reads the report" (or set
`FAIR_TURN_PROVIDER` before starting the app; see the README). Press Read the report,
check what was found, then Save. A fact with no matching words in the report stays empty
and a person sets it.

With no model on the machine, the two buttons at the bottom add a report from the test set
with its committed reading: one the AI read in full, and one it could not.

## 5. Answering a tenant

Open Ask about a repair and type the number from the tenant's receipt, or press an
example. The answer says if a crew is coming this week. If not, it says why: the NT time
limit, how far past it the repair is, how long the trip is, the setting the coordinator
chose, and whether another setting would have sent a crew. It names who signed the plan
and their reason.

## 6. Where the numbers come from

- **The geography is real**: community locations, regions and road access from BushTel and
  ABS, under pseudonymous ids.
- **The reports and events are synthetic**: 1,452 tenant reports written by one model and
  read by another, over October to December 2025.
- **The time limits are NT policy**: fact sheet FS17, October 2025.
- **Crew numbers are our assumption**: 10 crews at 5 bases, 3 repairs a crew-day, 400 km of
  road a day. NT does not publish them. They live in `fair_turn/core/constants.py`.
- **The backlog on the planning day** is what 12 weeks of Most repairs planning left
  behind, simulated.

## 7. Glossary

- **Trip.** A crew going from its base to one community and back. It costs driving days
  plus work days.
- **Setting.** One number from 0 (Most repairs) to 1 (Most overdue first). It sets what a
  trip is worth.
- **Priority.** What a trip is worth per crew-day under the setting. Higher goes first.
- **Below the cut.** The base's crew-days ran out before this trip's priority.
- **NT time limit.** FS17: urgent repairs in 2 business days in town and 5 remote; routine
  in 10 and 25; emergencies made safe in 4 hours.
- **Overdue.** Past its NT time limit on the planning day.
- **Source phrase.** The tenant's own words that back a fact the AI read. No phrase, no fact.
- **Decision log.** Every signed plan, change and reason, with two clocks: the planning day
  and the real time.
