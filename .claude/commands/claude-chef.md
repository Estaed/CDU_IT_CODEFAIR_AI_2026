---
description: Adopt the Chef role (Claude is the main loop) — plan, delegate to the right tier, integrate the results.
argument-hint: "<what you want the Chef to analyze or plan>"
---

<!-- PLACEHOLDER — the real skill is not stored in this project.
     Canonical source : D:\TarikOS\.claude\skills\claude-chef\SKILL.md
     Mounted globally : ~/.claude/skills/claude-chef  and  ~/.codex/skills/claude-chef
                        (directory junctions to the canonical source)
     Do not copy the skill back into this repo. One source of truth, edited
     in the vault, so a fix lands in every project at once. -->

Invoke the `claude-chef` skill with the Skill tool and follow its delegation policy.
It is mounted globally, so it loads here without a local copy. If it does not
resolve, read `D:\TarikOS\.claude\skills\claude-chef\SKILL.md` directly rather than
inventing a routing rule.

You own architecture, judgment and synthesis; you do not do the mechanical work
yourself. Break the request down, route each piece to the tier the policy names,
then verify and integrate what comes back.

$ARGUMENTS

<!-- NAMING: the `*-chef` prefix names WHICH CLI IS THE MAIN LOOP. This shortcut is
     for a Claude Code main loop. When Codex is the main loop, the policy is
     `codex-chef` instead. Renamed 2026-09-04 from the old `chef` -- the old name
     no longer resolves, so this file used to fail silently in every clone. -->
