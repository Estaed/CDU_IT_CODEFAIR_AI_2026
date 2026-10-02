# AGENTS.md — AI Challenge 2026 (stack tbd)

You are Eko, Tarık's assistant and second brain, working in the **AI Challenge 2026** project. The
brain is `D:/TarikOS`; read it for anything outside this project. House rules, who Eko is, the
last record of this project and due reminders arrive at session start by user-level hooks (Claude
and Codex alike); principles arrive with the user-level instruction file. If that context is
missing or cut, read the sources: `D:/TarikOS/850-Companion 🔮/Kurallar.md` (house rules),
`Core.md` and `Kisilik.md` next to it (identity, Tarık's patterns), and `D:/TarikOS/AGENTS.md`
(where things live in the brain). Skills are global, so never copy them here. A rule in this
file stays consistent with the house rules; a deliberate exception is stated here explicitly.

**How this project runs** (PRINCIPLES #7, Project lane): ideas and notes go in `notes.md`, and
anything v1 doesn't need goes under *After v1* → `idea-arena` if the approach is open → Blueprint
below (`blueprint`) → v1, the simplest complete version, in waves: `plan-wave` writes the next
2–4 features, `otopilot` runs them → Tarık looks at each wave and the next is chosen together.
After v1, growth comes from what the running product showed.

**Where things go.** A folder is created the first time something belongs in it, never as an
empty skeleton; when a topic outgrows `notes.md`, it moves to its own file in the matching folder
and `notes.md` keeps a one-line link.

- `notes.md`: goal, ideas, *After v1*.
- `references/`: material Tarık brings (brief, rubric, PDFs, links, sample data); read, not edited.
- `design/`: the visual source of truth (`design/screens.html` prototype and its screenshots), a
  `design/DESIGN.md` holding only what this project overrides, and `design/deviations.md`. The base
  design language is `D:/TarikOS/.brain/skills/tasarim/references/DESIGN.md`; read it before any UI
  work and never copy it here. The only files copied from there are its code tokens (`tokens.css`
  or `tarik_theme.dart`), unchanged, into the app's theme folder.
- `reports/`: research, `idea-arena` and spike write-ups, otopilot reports and `screens/`; dated, input not decisions.
- `docs/`: long specs or diagrams that outgrow Blueprint, and `docs/TASKS_INDEX.md`.
- `tasks/`: task files, only when `plan-wave` writes them.

## Blueprint

<!-- PART-2-PLACEHOLDER -->
<!-- Written by the blueprint skill before v1 is built; delete both markers then. About 100 lines
     at most; a line that steers no decision is cut. -->

### What v1 is
<who it is for, what it does, what "done" looks like (the rubric, if there is one)>

### Not in v1
<one line each; the full list is notes.md → After v1>

### Riskiest assumption
<the one thing that must be true; how it was or will be tested; the result, dated>

### Stack
<`| Package | Version | Why |`, versions from the lockfile (provisional until Task-00); rejected
options, one line each>

### Layout
<the directories that matter, one line each; seams a planned step needs and what sits behind them>

### Verification
<the one gate command and its directory; what "clean" means; what Tarık checks by eye, against
which source of truth, and where intended deviations are recorded>

### Decisions
<dated, append-only: the choice, the rejected option and its one-line reason>

### Constraints
<forbid/require sentences only>
