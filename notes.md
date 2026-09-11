# Notes — raw thinking, before any structure

Delete this file's instructions once you start writing real notes.

## What this is for

The first thing that happens in a project, before `create-prd` and before any
folder layout: dump what the thing has to do while you look at it.

If you are cloning or competing with something that exists, open it and walk
through it out loud — every panel, every screen, every data source. Write each
one down as you hit it, plus the call you are already making about it:

    - trading panel
    - chart -> use TradingView's library, not a custom one
    - market cap / liquidity / volume / ATH -> needs an indexer
    - holders + analytics -> they used a paid third party; we build our own
    - wallet -> Privy, not the one they used (social login)
    - search -> not in v1

Two minutes of this beats an hour of scaffolding. By the end you know what to
research, what the system revolves around, and which parts are out of scope —
and that is exactly what `create-prd` needs as input.

## Rules

- Decisions belong here too, not just features. "Not in v1" is a decision.
- Do not tidy it. This is a dump, not a document.
- When it stops growing, run `create-prd` and feed it this file.
- Nothing here is binding. Part 2 is binding; this is what leads to it.
