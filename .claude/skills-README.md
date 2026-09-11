# No local skills in this project — deliberate

Every skill comes from a single source: `D:\TarikOS\.claude\skills\`
It is junctioned into `~/.claude/skills/` and `~/.codex/skills/`, so Claude Code
and Codex both load the same version in every project.

**Do not copy skills back here.** Project scope shadows user scope: a local copy
silently overrides the current version in the vault. A fix made in the vault
lands in every project at once.

Command files (`.claude/commands/`) stay local — they do not shadow a skill,
they only invoke it.
