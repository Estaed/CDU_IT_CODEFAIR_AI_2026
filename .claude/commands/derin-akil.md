---
description: Hand a stuck problem to a non-agentic deep reasoning model, then verify every finding it returns against live code.
argument-hint: "<the problem, or 'report is back' when pasting the answer>"
---

<!-- PLACEHOLDER — the real skill is not stored in this project.
     Canonical source : D:\TarikOS\.claude\skills\derin-akil\SKILL.md
     Mounted globally : ~/.claude/skills/derin-akil  and  ~/.codex/skills/derin-akil
                        (directory junctions to the canonical source)
     Do not copy the skill back into this repo. One source of truth, edited
     in the vault, so a fix lands in every project at once. -->

Invoke the `derin-akil` skill with the Skill tool and follow it exactly. It is
mounted globally, so it loads here without a local copy. If it does not resolve,
read `D:\TarikOS\.claude\skills\derin-akil\SKILL.md` directly.

The skill runs in two halves and the second half is the point: when the report
comes back, every finding is checked against live code before anything is
applied. A report from a model that cannot run the code is a hypothesis, not a
result. Do not skip to implementation because the reasoning reads well.

$ARGUMENTS
