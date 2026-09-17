# WORKFLOW.md — skill sequence for a full-template project

Read this when a phase starts (new project, new task wave, leaving the desk), not every
session. The operating principles are Part 1, injected from the brain; the architecture is
Blueprint in `CLAUDE.md`. This file only says which skill runs when.

**Core Workflow (Skill Routing).** Grouped by *when they run*, not numbered — only the
first group is a sequence. Nothing here is a ladder to climb once and leave behind.

**Once per project, in this order**
- **Scaffolding files**, created with the folder and grown from there: `notes.md` (raw
  dump), `reports/` (unattended research output), `BACKLOG.md` (what was deferred and
  why), `constants.md` (values that must not be retyped), `MODELS.md` (which model runs
  which lane here). Each carries its own instructions; delete the instructions, not the
  file. `constants.md` and `MODELS.md` may be deleted outright if this project genuinely
  has no such values or lanes — say so in Blueprint rather than leaving them empty.
- `notes.md` — before any skill runs, dump what the thing has to do while looking at it.
  Features, data sources, and the calls already being made ("not in v1", "their third
  party, our own build"). Two minutes of this is what `create-prd` needs as input; see
  the file's own instructions.
- `create-prd` — the spec, from `notes.md`, the user's inputs, or designs.
- `create-architecture` — turns the PRD into Blueprint below: the stack, the layer rule, the
  seams, the verification rules. Blueprint ships as a placeholder in this template, so this
  step is **required** before any task is written. Once Blueprint exists, amending it stays a
  decision to raise with the user rather than an edit made in passing.
- `generate-tasks` — breaks the PRD into atomic `tasks/Task-XX.md`. Refuses to run before
  Blueprint exists.

**Per task, in a loop**
- **Read the task file's `Execution` and `Lane` blocks first.** `Execution` names the agent
  and the effort; `Lane` carries the delegation contract (OWNS,
  MUST NOT TOUCH, GATE, DEPENDS ON). Both were written by `generate-tasks` with the PRD and
  Blueprint in view — a session reading the task cold does not have that context and must not
  re-litigate it. One thing overrides it: `Kurallar.md`'s top-tier ban. If an `Execution`
  block names Fable or Astra as a lane, the block is wrong — say so and route to the
  lower tier; never open the top tier as a lane.
- **No Plan mode on tasks.** A task runs directly from its file. The task file is the
  contract — `Lane` (OWNS / GATE), the Acceptance Criteria and Blueprint are binding; the
  Execution Guide is the recommended route, not a script. Deviate from the guide when you
  have a concrete reason, stay inside OWNS, and say what you changed and why in the report.
  An open "how" is a ⛔ question to the operator, closed before the task runs — never a
  planning session at run time.
- `verify-task` — the goal-oriented fix loop, and **the gate**: nothing else marks a task
  DONE. **Run from the main loop, never by the lane that wrote the code** — the agent that
  produced the work must not be the one that relaxes its test.

**Unattended, when you want to leave the desk**
- `otopilot` — runs the tasks routed to `codex` that carry no ⛔ stop marker, in parallel worktree
  lanes, and runs each lane's `GATE` command itself. You approve one wave plan; everything
  after that is unattended, and you come back to a report. It refuses to start on a dirty
  tree, a red baseline, a missing `Lane` block, or any unanswered blocking question — clear
  those before you walk away, not after.

**Per group of tasks, once they are green — not per task**
- `/code-review` over the accumulated diff — **not** a persona subagent: it is built to
  review a diff and takes an effort level, where a cold subagent reports every provisional
  value and deliberate omission Blueprint records as a defect. Feed it the task file and
  Blueprint, and treat its findings as candidates, not verdicts.
- `review-visual` — only when the task produced something anyone looks at. Compares the
  built output against the source of truth Blueprint names, because `verify-task` cannot see a
  screen and reading the code to describe what it *would* render is the same guess that
  wrote it. Advisory like `/code-review` — never a gate.

**Any time, on their own — these are not stages and carry no place in the order**
- `idea-arena` — when the approach is genuinely open and more than one mechanism fits.
  Expensive; skip it whenever the approach is already decided or the call is cheap to
  reverse. Before the PRD its verdict is what the PRD describes; later it answers a question
  the PRD left open, and nothing about running it again means starting over.
- `research` — for a claim that can be checked: is this package maintained, does this API
  still exist, what is the current version, what is the known trap. It reports dated sources
  and hands the decision back; it never edits `docs/PRD.md`, Blueprint or a task file.
- `derin-akil` — for a problem that is stuck rather than open: a bug that survives the
  obvious fixes, a performance cliff, an architecture that will not close. It packages the
  relevant code, asks one non-agentic deep model, and then **verifies every finding against
  live code** before anything is applied. That verification half is the skill; a report from
  a model that cannot run the code is a hypothesis.
- `claude-chef` — the delegation policy itself: which tier of the stack a piece of work
  goes to. Read it before spawning subagents or Codex lanes, not after. Its mirror
  `codex-chef` applies when Codex is the main loop instead.
- `codex-swarm` — runs `codex exec` lanes directly, and generates image assets. Unlike
  `otopilot` it is not gated and not unattended: you are still at the desk. Its mirror
  `claude-swarm` spawns `claude -p` lanes from a Codex main loop.

  The prefix names **what gets spawned**, not who reads the file, and no CLI is shown the
  swarm that spawns its own kind — a Codex session reading `codex-swarm` would be reading
  "respawn yourself".

**Where the project currently stands** — which tasks are DONE, which is next — is
`docs/TASKS_INDEX.md`, never this file. Status written here goes stale within a week and
is then loaded into every session as a fact.
