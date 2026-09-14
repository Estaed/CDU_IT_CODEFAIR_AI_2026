# Review workflow, accept/reject, rubber-stamping, novice onboarding, keyboard — for Fair Turn

All sources accessed **2026-09-14**. "Source says" is what the page states; "Inference" is mine.
Builds on `reports/research-ui-hitl-guidance-2026-09-14.md` (HAX, PAIR, NN/g empty states and
tutorials, Buçinca cognitive forcing, Skitka/Mosier accountability, Ben Green); not repeated.

**Conflict to raise first.** The brief says the app "can now host one or two small JavaScript
components". CLAUDE.md Part 2 (Fidelity & UI, Key Constraints) still says "JavaScript, custom
bidirectional components and npm builds stay forbidden: `AppTest` cannot see them." Any tour or
hotkey component below needs a Part 2 amendment first. That decision belongs to Tarik.

---

## 1. How review tools work

**Labelbox.**
- Source says: a project has four default workflow tasks: Initial labeling, Initial review,
  Rework, Done (<https://docs.labelbox.com/docs/workflows>).
- Approve "will move the data row to the next task in the Workflow", or to Done at the last
  step. Reject "will move the data row to the Rework task", and the reviewer "can mark the issue
  and leave a comment as to why the label was rejected"
  (<https://labelbox.com/guides/how-to-customize-your-annotation-review-process/>).
- In Rework "any labeler or reviewer can modify all labels" (same guide).
- Issues are pinned to the asset. The labeler finds them in an Issues tab, then fixes and
  resolves the issue or replies to it (<https://docs.labelbox.com/docs/issues-comments>).
- Bulk "Move to task → Rework" works for up to 10,000 rows. The review queue can be filtered by
  "time spent", consensus score and "sample probability" (workflows doc).
- Pre-labels (model-assisted labeling) load as editable suggestions. "A pre-label is only
  converted into a finalized, ground truth annotation after a human labeler has reviewed and
  submitted" (<https://docs.labelbox.com/docs/model-assisted-labeling>).
- Benchmarks score labels against a gold-standard row; consensus scores agreement between
  labelers (<https://docs.labelbox.com/docs/quality-analysis>).
- The performance dashboard shows average review time. Review time is "the time a different
  user … spends looking at a label". It also shows Approval % and Rework %
  (<https://docs.labelbox.com/docs/performance-dashboard>).
- Documented hotkeys: `E` submit, `Q` skip, `X` create issue, `Tab`/`Shift+Tab` next/previous
  list item. **No approve or reject hotkey is documented**
  (<https://docs.labelbox.com/docs/keyboard-shortcuts>).

**Label Studio Enterprise.**
- Source says: the review stream offers Accept, **Fix & Accept** (correct the annotation, then
  accept) and Reject. "Rejecting an annotation does not return it to annotators to re-label"
  unless configured. Members metrics include acceptance score and time spent
  (<https://docs.humansignal.com/guide/quality>).
- The keymap binds submit `Ctrl+Enter` and skip `Ctrl+Space`. It has three reject variants:
  `Ctrl+Shift+1` no rework, `…+2` return to annotator, `…+3` pass to another annotator
  (<https://raw.githubusercontent.com/HumanSignal/label-studio/develop/web/libs/editor/src/core/settings/keymap.json>).

**Prodigy.**
- Source says: `a` accept, `x` reject, `space` ignore, `backspace` undo, `f` flag, `h` help.
  The decision is stored as an `"answer"` key. "The ten most recent decisions are shown in the
  sidebar and remain editable" (<https://prodi.gy/docs/api-web-app>).
- One keypress records the answer and moves to the next item.

**Human-in-the-loop document products.**
- Source says: Amazon A2I with Textract starts a human review on these activation conditions:
  a key's confidence falls in a range, "specific form keys are missing", or "randomly send a
  sample of forms to humans for review". The worker corrects the key-value pairs. A2I "is no
  longer open to new customers"
  (<https://docs.aws.amazon.com/sagemaker/latest/dg/a2i-textract-task-type.html>).
- Google Document AI Human-in-the-Loop (compare extracted values with the document, correct,
  add missing values) is deprecated. The forum post gives a shutdown date of 16 January 2025
  (<https://discuss.google.dev/t/document-ai-human-in-the-loop-deprecation/146583>). Google's
  deprecations page says 16 January 2024 (fetched via
  <https://docs.cloud.google.com/document-ai/docs/hitl/concepts>). **Dates contradict.**
- Inference: the pattern that survives in both is to route on a *missing* field and add a
  *random sample*. Fair Turn already routes on a missing verified phrase. It has no random
  sample, and it cannot use confidence (Part 2 forbids it).

**Inference: what these tools share.**
- The reviewer sees one item at a time, with the source and the proposed labels overlaid.
- One key or click records the decision and moves to the next item.
- Reject carries a reason (issue or comment) and sends the item to a *named queue*. It is never
  deleted.
- The system logs who decided and how long they looked.

All of these tools review *labels to train models*. Nobody downstream is waiting on each item.
Fair Turn reviews *facts that decide a tenant's place in the list*, so its reject cannot be a
bare thumbs-down.

---

## 2. Mapping to Fair Turn

### (a) Accept or correct the AI-extracted fields of one job

PRD constraints: verified fields already show their source phrase (§3.1). Unverified fields are
empty and go to the review queue, where "the rejected model value is never shown" (§3.2).

**Recommendation: yes, but as "Fields confirmed" / "Correct a field", not a green tick and red
cross.**
- **Accept (one click):** records `fields_confirmed` for the job, with actor, recorded-at,
  decision day and the batch version. It does not change the ranking. Enable it only after the
  selected-job pane has shown the report with its highlighted phrases (see §3).
- **Correct:** opens the existing human-set path. The coordinator picks the enum value and must
  give a reason. The field becomes human-set with the "Set by coordinator" badge. The job
  re-ranks, and if a batch is open, the batch is invalidated (existing Part 2 rule).
- A reject must capture: which field, the new value (or "cannot tell → request clarification"),
  and a reason. That is Label Studio's "Fix & Accept", and Labelbox's issue-plus-comment.
- **Not** "reject → discard". A tenant's report must not disappear. Rejected jobs go to the
  review queue, the equivalent of Labelbox's Rework.
- Inference on batch interaction: confirmations are optional evidence, not a gate on signing.
  The sign-off summary reports "k of n jobs in today's list had fields confirmed". Making them
  a gate turns them into n rubber-stamps before one signature.

### (b) Accept a job onto today's list, or defer it to the backlog

The PRD already has hand moves, promote-from-backlog and send-to-queue, each with a reason (§3.1).

**Recommendation: add only a per-row "Defer" (move to backlog), with a required reason. Do not
add a per-row accept tick.**
- **Defer (one click, then a reason):** removes the job from today's proposed list. The next
  backlog job is promoted, and the pane names it (mirrors the existing "names the job it
  displaces"). The move is logged as a hand move and invalidates an open batch.
- A defer must capture: the reason (suggested: access not possible today, tenant unavailable,
  trade not available, other with text), actor, time and batch version.
- **Accept stays the daily signature.** A per-job accept on 30 rows plus a batch signature would
  be two approval layers. Source says the ICO counts a decision as automated if a human merely
  "rubber-stamped" it
  (<https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-individual-rights-in-our-ai-systems/>).
  Inference: 30 unexamined ticks are the textbook shape of that.

---

## 3. Rubber-stamping and automation bias

**What the sources say**
- **Parasuraman & Manzey 2010**, *Human Factors* 52(3):381–410
  (<https://journals.sagepub.com/doi/10.1177/0018720810376055>): complacency appears under
  multiple-task load. It is found in naive and expert users alike and "cannot be overcome with
  simple practice".
- **Skitka, Mosier & Burdick 1999**, *IJHCS* 51(5):991–1006
  (<https://dl.acm.org/doi/abs/10.1006/ijhc.1999.0252>): with a highly but not perfectly
  reliable aid, participants made omission and commission errors that the non-automated group
  avoided. Training reduced commission errors but not omission errors.
- **Goddard, Roudsari & Wyatt 2012**, *JAMIA* 19(1):121–127
  (<https://academic.oup.com/jamia/article-abstract/19/1/121/732254>), 74 studies. Mediators:
  workload, task complexity, time constraint. Mitigators: training, "emphasizing user
  accountability", "the position of advice on the screen", and "information versus
  recommendation".
- **Lyell & Coiera 2017**, *JAMIA* 24(2):423–431
  (<https://academic.oup.com/jamia/article-abstract/24/2/423/2631492>): automation bias tracks
  cognitive load and verification complexity, not multitasking alone.
- **Bahner, Hüper & Manzey 2008**, *IJHCS* 66:688–699
  (<https://dl.acm.org/doi/abs/10.1016/j.ijhcs.2008.06.001>): *experiencing* automation misses
  during training reduced complacency and omission errors. Being told about misses did less. It
  did not reduce commission errors.
- **Park et al. 2019**, PACM HCI 3(CSCW) art. 102 (<https://dl.acm.org/doi/10.1145/3359204>):
  added waiting time improved users' assessment of algorithm accuracy (title claim; I could not
  read the full text).
- **Government guidance.**
  - EU AI Act Art. 14(4)(b) requires overseers to "remain aware of the possible tendency of
    automatically relying or over-relying" (<https://artificialintelligenceact.eu/article/14/>).
  - The NSW Ombudsman says human involvement must exist "in practice, not just on paper" and
    warns of "technology complacency". Reviewers need time, access to source data and the
    ability to override
    (<https://www.ombo.nsw.gov.au/guidance-for-organisations/improving-public-administration/automated-decision-making-systems/implementing-automated-decision-making>).
  - The Commonwealth Ombudsman's better practice guide is the federal equivalent
    (<https://www.ombudsman.gov.au/__data/assets/pdf_file/0030/109596/OMB1188-Automated-Decision-Making-Report_Final-A1898885.pdf>;
    only the search summary was read).
  - The ICO (above) says the same about rubber-stamping.

**Mitigations, graded**

| Mitigation | Grade | Basis |
|---|---|---|
| Emphasise accountability (named signer, reason, audit) | **Evidence** | Skitka/Mosier; Goddard 2012 |
| Show source evidence in place, next to the value | **Evidence (design factor)** | Goddard "position of advice"; NSW "access to source data" |
| Reduce verification load (highlighted phrases, one job at a time) | **Evidence (indirect)** | Lyell & Coiera 2017 |
| Commit before seeing the AI's view | **Evidence**, disliked | Buçinca 2021 (prior report) |
| No "accept all" | **Inference** from the above; no study isolates it | — |
| Accept enabled only after the evidence is shown | **Folklore / plausible**; forced viewing does not prove reading | Park 2019 is the nearest evidence |
| Show the reviewer's own review time and override rate | **Industry practice** (Labelbox), not tested as a mitigator | Labelbox dashboard; EU Art. 14(4)(b) |
| Spot-check sampling | **Industry practice** (A2I random sample); no bias study | A2I doc |
| Seeded known-wrong items ("catch trials") | **Evidence**, limited to omission errors | Bahner 2008; Labelbox benchmarks as practice |
| Reason required on accept-with-change | **Evidence** via accountability | Skitka/Mosier |
| "Calibrated disagreement" prompts | **Folklore**; no source found | — |

---

## 4. Novice onboarding without documents

**What the sources say**
- NN/g's controlled test (Kendrick, 2020; 70 users, 4 apps) found task success of 91% with the
  tutorial and 94% after skipping it, not significant. Tutorial readers rated tasks harder
  (<https://www.nngroup.com/articles/mobile-tutorials/>).
- NN/g prefers contextual help (<https://www.nngroup.com/articles/onboarding-tutorials/>).
- Tooltips "shouldn't be essential"; actionable instructions do not belong in a tooltip
  (<https://www.nngroup.com/articles/tooltip-guidelines/>).
- The empty-state guidance is in the prior report.
- Checklist progress: Nunes & Drèze 2006 showed that pre-granted progress raised completion from
  19% to 34%, on car-wash loyalty cards
  (<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=991962>). Its transfer to onboarding
  checklists is **practitioner inference** (<https://uxdesign.cc/endowed-progress-effect-give-your-users-a-head-start-97d52d8b0396>).
- Tours: a "Streamlit Guided Tour" component wrapping Driver.js was posted on 3 April 2026
  (<https://discuss.streamlit.io/t/new-component-streamlit-guided-tour/121206>; repo
  mp-mech-ai/streamlit_tour). I did not verify its maintenance or AppTest behaviour.

**Inference, smallest set for Fair Turn**
1. **A day stepper** in the workspace header. It shows the day's actual steps with their state
   (review queue cleared → list checked → signed → visit plan), not a tutorial. It is native
   Streamlit, reuses the existing decision states, and is testable.
2. **Teaching empty and locked states** (already specified).
3. **Inline definitions** with `help=` on column headers and controls, for domain terms
   (safety class, NT window, λ). The definition must stay non-essential, so the label itself
   stays plain.
4. **Optional presenter tour**, only if Part 2 is amended. Keep it to five steps or fewer and
   never auto-open it. It is the lowest-evidence item; drop it first.

---

## 5. Keyboard review

**What the sources say**
- Prodigy: `a` / `x` / `space` / `backspace`.
- Labelbox: `E` submit, `Q` skip, `X` issue, `Tab` next.
- Label Studio: `Ctrl+Enter` submit, `Ctrl+Shift+1..3` reject variants.
- Gmail: `j` / `k` next/previous, `e` archive, `u` back to list
  (<https://zapier.com/blog/gmail-shortcuts/>).
- **Trap:** Streamlit reserves bare `r` (rerun) and `c` (clear cache) outside text inputs
  (<https://github.com/streamlit/streamlit/issues/4048>).
- Custom keys need a JS component, for example streamlit-hotkeys
  (<https://github.com/viktor-shcherb/streamlit-hotkeys>). That is blocked by Part 2 today.

**Inference, proposed map** (only if a component is allowed; the selectbox path stays the
accessible equivalent):

| Key | Action |
|---|---|
| `j` / `k` | next / previous job |
| `a` | confirm fields (disabled until evidence shown) |
| `x` | correct a field (opens the field and the reason box; never submits) |
| `d` | defer to backlog (opens the reason box) |
| `q` | send to review queue (with reason) |
| `?` | show key map |

Deliberately excluded:
- No key signs the batch; signing stays a form with a typed reason.
- No bare `r` or `c`.
- No key submits a reason without focus in the text box.

---

## Recommendation for Fair Turn

1. **Do not add a green tick / red cross per row on today's list.** The daily signature is the
   accept. A second per-job approval layer is the rubber-stamp shape the ICO and NSW Ombudsman
   warn against. *(Evidence-backed: ICO, NSW Ombudsman, Skitka 1999.)*
2. **Add "Fields confirmed" / "Correct a field" in the selected-job pane.** Confirm logs actor,
   both clocks and the batch version. Correct uses the existing human-set path with a required
   reason. Rejected fields go to the review queue, never deleted, and confirmation does not gate
   signing. *(Pattern from Labelbox and Label Studio; accountability evidence from
   Skitka/Mosier and Goddard 2012.)*
3. **Add a per-row "Defer to backlog" with a required reason.** Name the job it promotes, and
   invalidate an open batch. *(Inference from the PRD's existing override rules.)*
4. **No "accept all" anywhere, and confirm is enabled only after the report and its
   highlighted phrases are shown.** *(Inference; forced viewing is plausible but unproven.)*
5. **Show the coordinator's own confirm/override counts and median time per job on the sign-off
   summary.** *(Industry practice (Labelbox); supports EU AI Act Art. 14(4)(b); not tested as a
   mitigator.)*
6. **Add a random spot-check: one confirmed job per signed batch is re-shown with its fields
   hidden, for the coordinator to set blind.** *(A2I random sampling as practice; Bahner 2008
   evidence for experienced misses, omission errors only.)*
7. **Onboard with a day stepper, teaching empty states and `help=` definitions. No auto-opened
   tour.** *(Evidence-backed: NN/g tutorial test (Kendrick 2020), NN/g contextual help and
   tooltip guidance.)*
8. **Treat any JS tour or hotkey component as a Part 2 amendment, decided before building.** If
   approved: `j`/`k`/`a`/`x`/`d`/`q`/`?`, never `r`/`c`, and no key that signs. *(Key
   conventions from Prodigy and Gmail; the Streamlit reserved keys are verified.)*
