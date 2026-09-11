---
description: Run an unattended Codex wave over the tasks routed to codex, gate each lane, report back.
argument-hint: "<which tasks or wave to run while you are away>"
---

<!-- PLACEHOLDER — the real skill is not stored in this project.
     Canonical source : D:\TarikOS\.claude\skills\otopilot\SKILL.md
     Mounted globally : ~/.claude/skills/otopilot  and  ~/.codex/skills/otopilot
                        (directory junctions to the canonical source)
     Do not copy the skill back into this repo. One source of truth, edited
     in the vault, so a fix lands in every project at once. -->

Invoke the `otopilot` skill with the Skill tool and follow it exactly. It is
mounted globally, so it loads here without a local copy. If it does not resolve,
read `D:\TarikOS\.claude\skills\otopilot\SKILL.md` directly rather than
improvising an unattended run.

It only ever runs tasks whose `Execution` block routes to agent `codex` with plan
mode `no`, and it refuses to start on a dirty tree, a red baseline, a missing
`Lane` block, or an unanswered blocking question. Do not talk it past a refused
preflight — the preflight is the reason it is safe to walk away from.

$ARGUMENTS
