# Fair Turn — User Guide

Ten minutes, for a new coordinator, a teammate, or a judge. This page is the walkthrough;
`docs/PRD.md` section 3 has the full rule behind each surface, and `design/` has the exact
layout. A short version of sections 1 and 3 is one click away in the app, in the
"How to use" popover under the page title, on every page.

If a screen ever disagrees with this guide, the screen and `docs/PRD.md` are right; this
guide is the fast path in, not the source of the rules.

## 1. What Fair Turn is

Fair Turn reads today's free-text repair reports and turns them into a suggested order.
A coordinator sets the weighting, checks each job, and signs the list that crews use.
Every step, from the reading to the sign-off, is written to a log that can be checked
later, with who did it and when.

Fair Turn never sends a job to a crew. It never approves a repair, and it never decides
who counts as a tenant. A person always makes the call, and a person always signs it. The
model only reads and suggests; nothing it produces reaches the screen unless a source
phrase in the report backs it up, or a person typed it in by hand.

## 2. Who uses which page

Fair Turn has five pages, reached from the sidebar.

- **Workspace.** The coordinator's main page. Today's ranked list, the map, the
  selected-job pane, the weighting control, and the sign-off form, all in one place.
- **Review queue.** The coordinator's second stop. One job at a time, for jobs where a
  needed field has no matching words in the report.
- **Visit plan.** The coordinator's run sheet, once today's list is signed. Each crew
  gets its stops in the shortest order, and the page shows the road kilometres of the day.
- **Tenant answer.** For a tenant, or the housing officer helping them. Look up one job
  by its registration number and read a plain-language answer.
- **Evidence lab.** For judges and governance, outside the coordinator's daily flow. How
  well the system reads reports, a 90-day simulation, and the full audit log.

## 3. A coordinator's morning, step by step

This step list follows how other dispatch tools already work. The same four day steps sit
in a strip at the top of the Workspace. Each tile says if it is done, and the next one
says what to do.

1. **Read the numbers at the top of the Workspace.** They say how many jobs are open,
   how many need a person's help, and how the list has moved since the last change.
2. **Jobs that need a person.** These are jobs with a field the system could not read.
   The Needs a human tab, next to today's list, names what is missing in each one.
   Press Review to open it. Fill each one in by hand, with a reason.
3. **Check today's jobs.** Open a job from today's list, the map, or the Select job box.
   Read the report and the words marked in it. If the fields are right, press
   Fields are right. If one is wrong, press Fix a field, pick the right value, and
   say why. The row then shows Checked or Corrected. There is no button that passes
   every job at once: each check is one job, read by you.
4. **Use the map when it helps.** Circles group nearby communities. Click one and it
   splits into one dot per community. A dot with several jobs lets you choose; it never
   picks one job. The region filter only narrows what you see.
5. **Move a job, or send it to the review queue, with a reason.** Every hand move is
   written down and shown to anyone who looks at that job later.
6. **Choose the weighting and sign.** Pick a setting in the sidebar: Efficiency first,
   Balanced, or Need first. The effect line under the numbers says how many remote and
   town jobs move in or out. Then press Review and sign, under the list. The summary
   says how many jobs you checked. Signing does not wait for checks. It freezes today's
   list as a numbered batch, and the signer and the reason go to the log.
7. **Read the outcomes.** Wait times and travel cost appear only after the first
   signature, so they cannot steer the order before it is set.
8. **Open the visit plan.** It turns the signed list into crew run sheets. Distance
   picks which crew goes, never which job is done.

Source: `reports/research-ui-dispatch-products-2026-09-14.md`, "Usage logic a coordinator
would recognise".

## 4. How to test intake

1. Open **New report** from the Workspace header.
2. Set the extractor in the intake box. If none is set, the box says why and offers the
   review queue as the way to add a report by hand instead.
3. Load an example report, or type one in. Reports are plain text: what broke, where,
   and who lives there.
4. Press **Extract** and watch the status line while the model reads the text.
5. See where the report lands: the ranked queue with a proposed rank, or the review
   queue if a required field has no matching words in the report. A failed or slow read
   is saved as "not extracted", with the reason, and can be tried again.
6. Sending the same report twice does not make two jobs. The box remembers the draft
   until it is saved, so a second press of Extract does not double-write the log.

## 5. The keyboard path

Every action on the Workspace has a real, focusable control, so a mouse is never
required to reach a decision.

- The **Select job** box in the sidebar is the keyboard way into the selected-job pane.
  Tab to it, then use the arrow keys or type to search by job id.
- Move, promote, and send-to-review are buttons with a reason field next to them; Tab
  reaches each one in turn.
- Sign-off is a form. Tab through weighting, reason, and signer, then press Enter or
  click Submit. A form only saves when submitted, never on a single keystroke.

## 6. Glossary

- **Source phrase.** The exact words in a report that support one field's value. A field
  with no source phrase is left empty, never guessed, and the job goes to the review
  queue.
- **Household health risk.** Our own factor, not an NT class: a household condition such
  as a young child, an elderly person, pregnancy, or no working water, that raises how
  soon a repair should happen.
- **Efficiency first, Balanced, Need first.** The three named weighting settings
  (λ = 1.0, 0.5, and 0.0). A slider value that does not match one is labelled "Custom".
- **Window.** The NT policy time a job's safety class allows before it should be fixed.
  Remote communities get a longer window than town, by policy (FS17).
- **Human-set field.** A fact a coordinator typed in by hand because the report did not
  say it clearly enough to read on its own. It carries a gray "Set by coordinator" tag
  and still counts in the ranking, the same as a field read from the report.
- **Batch version.** The number stamped on a signed list. Signing again after a change
  makes a new, higher version; the old one stays in the log and is never deleted.
- **Override rate.** How often a coordinator moves a job by hand, counted by day. Shown
  on the Workspace header and, over time, in the Evidence lab.
- **Decide before reveal.** Wait-time and travel numbers stay hidden until the first
  sign-off, so they cannot steer the order before a coordinator chooses it.

## 7. Where the numbers come from

- **How well the system reads reports:** Evidence lab, Extraction quality tab, scored
  against a labelled test set, with the provider and model named.
- **Wait times and travel cost:** Evidence lab, Feedback loop tab, from a 90-day
  simulation, not from real events; the report data in this demo is made up.
- **Every signed decision and its reason:** Evidence lab, Audit log tab, backed by the
  files under `data/build/` and `data/audit/`, which a judge can open directly.
- **The geography:** real (BushTel and ABS); this caption is fixed on every page.
- **The policy numbers:** window days, the make-safe hours, the crew counts, all in
  `constants.md` at the repo root, with a source row for each one.
