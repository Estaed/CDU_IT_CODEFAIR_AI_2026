# Task-03: Design A/B, Tarik Base against a blind direction
> **Execution:** agent `main-loop` · effort `high`
> *Why:* Tarık wants to see whether the `tasarim` skill produces a better screen than an unguided
> model before the look is built (2026-10-03). Design is eye work, which `Proje-Baslatma.md` §3.5
> gives to the main loop.

**Lane**
- OWNS: `design/direction-A.html`, `design/ab.html`, `design/shots/**`
- MUST NOT TOUCH: `design/direction-B.html` (written blind before this wave), `design/ab-brief.md`, `design/mock-v0.html`, and everything outside `design/`
- GATE: `python -c "import pathlib,sys; sys.exit(0 if all(pathlib.Path(p).exists() for p in ['design/direction-A.html','design/direction-B.html','design/ab.html']) else 1)"` (from repo root)
- DEPENDS ON: none

## Goal
**A** (`design/direction-A.html`) is the same screen as B, built from exactly the same functional
brief and content in `design/ab-brief.md`.
- Load the `tasarim` skill first. It is Tarik Base, both modes.
- Start from `design/mock-v0.html` and fix its known issues (listed in `notes.md` → Framing → "Mock
  v0 known issues").

**Compare page** (`design/ab.html`): A and B side by side as screenshots, the same five states for
both, dark and light where a design has them. Playwright at 1280×900, files in `design/shots/`.
- Under each pair, one line on what differs.
- At the top, a neutral note: which one followed the skill, and that Tarık picks.

## Why
Tarık's choice sets `web/theme.css` and the eye-check source of truth (`design/screens.html`) for
the look wave.

## Acceptance
- [ ] The gate exists check passes.
- [ ] A covers every item in `design/ab-brief.md`, with the same content as B; quotes are verbatim.
- [ ] A has no console errors, and its screenshots exist in both modes.
- [ ] (eye) Tarık opens `design/ab.html` and picks A or B in one sentence. That pick becomes
  `design/screens.html` in the next wave.

## Out of scope
- Changing B, and any app code (`web/` belongs to Task-00).
