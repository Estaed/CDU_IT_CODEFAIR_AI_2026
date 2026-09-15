# Fair Turn First-Time User Test

Date: 2026-09-15  
Role: First-time maintenance coordinator with no housing-maintenance or AI background  
URL: `http://localhost:8501`  
Test method: Browser interaction through the visible UI. The Deploy button was not used.

## A. Problems

The test was blocked during Workspace step 3 by a runtime crash. Existing records were retained, so the starting state showed 1 accepted job and 13 jobs to decide.

| Severity | Page | Exact steps | Expected | Actual |
|---|---|---|---|---|
| blocker | Workspace | Open #1307, scroll to the decision controls, try Accept before acknowledgement, tick the read checkbox, then reload | Accept becomes usable and the decision workflow continues | Accept was correctly disabled before acknowledgement. After ticking the checkbox, the page crashed with `AttributeError: module 'fair_turn.core.audit' has no attribute 'make_safe_sent'`. Reload did not recover it. A later return showed `fair_turn.core.decisions` has no attribute `is_make_safe`. |
| major | Visit plan | Read the coordination and unplanned sections | Outstanding work is grouped and explained consistently | The page says “No manual coordination needed” while five Darwin jobs are listed as “signed, unplanned” because no crew has a free slot. |
| major | Evidence lab, Feedback loop | Read the explanation and default charts | The chart visibly supports the stated trade-off | The text says remote reporting falls under efficiency-only and holds under the chosen weighting, but the default remote report lines nearly overlap and both finish at 52. |
| minor | Visit plan | Read crew routes and kilometres | Travel figures are plausible or explained | Several Darwin and Alice Springs routes show 0 km without explaining why. |
| minor | Tenant answer | Select “#122 · needs a person first” | Status is consistent with the page introduction | The introduction says an officer checked and signed the list, while the answer says the coordinator has not signed today’s setting. |
| minor | Review queue | Review #106 and save a field | Action wording is familiar | The save action is “Mark rankable,” which does not clearly mean save and return. |
| minor | Workspace | Read the Today’s steps strip | Instructions are easy to scan | The supporting text is very faint grey on white. |

## B. Scenario results

### 1. First look

Fair Turn suggests which repair jobs should happen today, and I make the final decisions before signing. My first step is to open “Needs a human” and fill in missing information.

The “Today’s steps” strip was followed until the Workspace crash.

### 2. Needs a human

I opened the first item, job #106, whose fault type was missing. The report described a rangehood over a stove, so I selected `stove_cooking`, entered Tarik as the name, selected “Report names the appliance,” and pressed “Mark rankable.”

The green message said: `JR-2025-00106 is now rank 416, in the backlog`. Returning to Workspace changed “Needs a human” from 21 to 20. This part worked.

### 3. Deciding a job

I opened #1307 and scrolled to the bottom. “Accept for today” was disabled until “I have read the report and the reasons above” was checked. After checking it, the Workspace crashed before acceptance could be completed. Undo and reacceptance were not testable.

### 4–10. Rejection, correction, keyboard, map, weighting, DEV reports and signing

These scenarios were not testable because Workspace remained broken after reload. No new report or signature was created during this test.

### 11. Visit plan

The existing v6 plan showed Alice Springs with one stop, Katherine with two stops, and three Darwin crews with two stops each. Tennant Creek and Nhulunbuy had no signed road jobs. The plan reported 198 km total and five jobs with no crew within reach. It explains that an unreachable job needs a phone call, but also says “No manual coordination needed,” which is contradictory.

### 12. Tenant answer

I selected all three examples:

- #191: ninth on the signed list; no visit date yet.
- #4: position 516 in the queue; waiting for the next free crew day; no visit date.
- #122: a person is checking the report; no queue position yet.

The answers were mostly understandable, but “NT response window,” “weighted heavily,” and “lambda = 0” required interpretation. The #122 signing statement was inconsistent with the page introduction.

### 13. Evidence lab

- Extraction quality proves how often the extractor reads synthetic reports correctly. It clearly reports safety class at 56%, below the 85% target.
- Feedback loop presents a simulation of reporting decay and waiting time for remote versus town communities. Its default chart does not make the claimed difference obvious.
- Audit log proves that actions are recorded with signer, kind, job and timestamps. My #106 human-set correction and reason appeared under Tarik.

### 14. Persistence

I reloaded during step 3. The Workspace remained broken, so decision persistence could not be assessed. The earlier #106 field correction was still visible in the Audit log.

## C. Confusing words and labels

| Label | What I thought it meant |
|---|---|
| Mark rankable | Approve the job, rather than make it eligible for ordering |
| 8 of 2 d | A fraction, before understanding it meant eight days against a two-day target |
| Override rate | How often somebody rejected the AI; scope was unclear |
| No crew within reach | Too far away, although some jobs meant no crew had a free slot |
| NT response window | An appointment window, until the policy definition appeared |
| lambda, weighted heavily, logistics | Technical scoring terms rather than plain-language trade-offs |
| bag-of-words baseline, held-out, adversarial, schema | AI evaluation terms needing explanation |
| human_set, field_check, sign_off | Internal event names rather than readable actions |

## D. Three changes that would help most

1. Fix the Workspace runtime errors so the complete accept, reject and sign workflow is usable.
2. Clearly separate “selected today,” “signed,” “assigned to a crew,” and “needs coordination,” with one consistent warning for unplanned work.
3. Replace technical labels with everyday wording, increase instruction contrast, and make the charts visibly support their accompanying explanation.

## E. Competition judge assessment

### Efficiency versus remote communities

Partly. The screens expose the trade-off: the Workspace showed 1 remote household among 14 jobs, and tenant examples showed that removing travel cost moved #191 from position 9 to 291 and #4 from 516 to 244. The live weighting switch could not be tested because of the Workspace crash. The Evidence lab also provides a remote/town simulation, although its default chart is not visually persuasive.

### Human decision authority

Partly verified. The system required a human value and reason for missing information, reduced the review count from 21 to 20, and disabled acceptance until the report acknowledgement was checked. The full decision, undo and signing flow could not be verified because the Workspace crashed.

## Handoff note

Only the #106 field correction was saved during this test. No new signature was created. The report is ready to pass to Claude as a Markdown file.
