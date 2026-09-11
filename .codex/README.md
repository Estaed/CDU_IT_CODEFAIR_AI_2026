# `.codex/` in this project — what belongs here, and what deliberately does not

Codex reads three things. Only one of them is project-local:

| What | Where it comes from | Project-local? |
| --- | --- | --- |
| Project instructions | `AGENTS.md` at the repo root | **yes** — generated from `CLAUDE.md` |
| Skills | `~/.codex/skills/` (junctions to `D:\TarikOS\.claude\skills\`) | no — user scope, one source |
| Slash commands | `~/.codex/prompts/*.md` (generated stubs, one per skill) | no — user scope, one source |

So there is no `.codex/skills/` and no `.codex/commands/` here, and adding them
would be a regression: a project-local copy shadows the vault version silently,
and the shadow does not announce itself — it just serves a stale skill forever.
Same reason `.claude/skills-README.md` says the same thing on the Claude side.

`.claude/commands/*.md` **is** local, and that is not an inconsistency: those files
do not shadow a skill, they only invoke one. Codex has no project-level equivalent,
which is why the same shortcuts live in `~/.codex/prompts/`.

## Keeping both CLIs in sync

    python D:\TarikOS\.claude\scripts\mount_skills.py            # repair links + regenerate prompts
    python D:\TarikOS\.claude\scripts\mount_skills.py --check    # audit only, exit 1 if anything is missing

Run it after writing a new skill in the vault. A skill that exists but is not
mounted does not error — it simply never gets called, which is the hardest kind
of failure to notice.

## Hooks

Two different things share the name `hooks.json`, and only one of them belongs here.

**The Beyin *memory* hooks stay in the vault.** Those four hooks (`SessionStart`,
`UserPromptSubmit`, `PreCompact`, `SessionEnd`) *write* to `D:\TarikOS\daily\`. A
project does not write to the brain directly — the session summary is produced by
whichever session you ran, in the vault. Do not copy those here.

**The rule-injection hook does belong here**, because it only *reads*. `.codex/hooks.json`
in this project registers one `SessionStart` entry pointing at
`.claude/hooks/codex-brain-rules.cmd`, which runs the same `brain-rules.sh` that the
Claude side uses. Read-only, no second copy of the rules, no writes to the brain.

**It is not in this template.** It is generated per project, because the command path has
to be absolute — Codex defines neither `CODEX_PROJECT_DIR` nor `CLAUDE_PROJECT_DIR`, and a
file shipped here would hand every clone the template's own path. The generator refuses to
run while `CLAUDE.md` still has the `<PROJECT NAME>` placeholder, so it cannot reappear
here by accident. Run it **in the clone**, as a setup step:

    python D:/TarikOS/.claude/scripts/render_codex_hooks.py --project .
    python D:/TarikOS/.claude/scripts/render_codex_hooks.py --project . --check

Codex asks for trust once per clone. **An unapproved hook is skipped silently** and the
run still reports `Completed`, so absence of an error is not evidence that it worked.
