---
description: Deploy a parallel fleet of Codex delegates to execute a task.
argument-hint: "<the task to be swarmed>"
---

<!-- PLACEHOLDER — the real skill is not stored in this project.
     Canonical source : D:\TarikOS\.claude\skills\codex-swarm\SKILL.md
     Mounted globally : ~/.claude/skills/codex-swarm  (NOT ~/.codex/skills/ -- see note)
                        (directory junctions to the canonical source)
     Do not copy the skill back into this repo. One source of truth, edited
     in the vault, so a fix lands in every project at once. -->

Invoke the `codex-swarm` skill with the Skill tool and follow it exactly.
It is mounted globally, so it loads here without a local copy. If it does not
resolve, read `D:\TarikOS\.claude\skills\codex-swarm\SKILL.md` directly rather than
improvising a fleet.

Task (if empty, ask what to swarm — do not guess): $ARGUMENTS

<!-- NAMING: the `*-swarm` prefix names WHAT GETS SPAWNED. `codex-swarm` spawns Codex
     lanes and is driven from a Claude main loop; `claude-swarm` spawns Claude lanes
     from a Codex main loop. No CLI is mounted the swarm that carries its own name --
     mount_skills.py enforces this, because a Codex session reading `codex-swarm`
     would be reading 'respawn yourself'. Renamed 2026-09-04 from the old `swarm`,
     which no longer resolves. -->
