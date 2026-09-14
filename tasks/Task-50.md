# Task-50: User guide in English and an in-app "How to use" popover

Status: DONE

> **Execution:** agent `claude` · effort `medium` · plan mode **no**
> *Why:* Tarik (2026-09-14): nobody on the team could say what to do on the screen; the guide is the hand-off for teammates, judges and the report appendix.

**Lane**
- OWNS: `docs/user-guide.md` (new), `README.md` (one link), `fair_turn/app/components/intro.py`, `tests/test_user_guide.py` (new)
- MUST NOT TOUCH: `fair_turn/app/pages/`, `fair_turn/app/main.py`, `fair_turn/app/theme.py`, `.streamlit/`, `docs/PRD.md`, `CLAUDE.md`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 40

## Objective

A short guide a new coordinator or a judge can follow in ten minutes, in the repo and one
click away in the app.

## Execution Guide

- `docs/user-guide.md` (English, 120-180 lines, year-7 reading level for the walkthrough,
  no deficit language): (1) What Fair Turn is in three sentences and what it never does
  (PRD §2: the AI reads and suggests; a person decides and signs). (2) Who uses which page:
  coordinator (Workspace, Review queue, Visit plan), tenant or housing officer (Tenant
  answer), judges and governance (Evidence lab). (3) A coordinator's morning, step by step,
  built from `reports/research-ui-dispatch-products-2026-09-14.md` "Usage logic": read the
  KPI row, clear the review queue, choose the weighting and read the effect sentence, check
  the map, open a job and read why it sits there, move or send to review with a reason,
  review and sign, read the outcomes, open the visit plan. (4) How to test intake: set the
  extractor in the intake box, load an example, press Extract, see where it lands. (5) The
  keyboard path (Select job box, Tab order). (6) Glossary: efficiency-first, Balanced, Need
  first, window, human-set field, batch version, override rate, decide before reveal. (7)
  Where the numbers come from (Evidence lab, `data/build/`), one line each. Cite pages by
  their navigation names. Run the walkthrough paragraphs through `core.wording.check` in the
  test and keep them green.
- `README.md`: one line under the run instructions linking `docs/user-guide.md`.
- `intro.py`: `purpose(page)` additionally renders, once per page, `with st.sidebar:
  st.popover("How to use", icon=":material/help:")` (verify the `icon` parameter exists on
  1.63; drop it if not) containing the guide's sections 1 and 3 read from `docs/user-guide.md`
  with `pathlib` (`Path(__file__).resolve().parents[3] / "docs" / "user-guide.md"`; split on
  the H2 headings and show the two sections). AppTest sees `st.popover` as a `popover`-type
  block; assert through the markdown it contains.
- Tests: the guide file exists with the seven H2 sections in order; walkthrough paragraphs
  pass the wording check; every page renders the popover's markdown (smoke over the five
  pages, offline).

## Acceptance Criteria (DoD)

- [ ] `docs/user-guide.md` with the seven sections; README links it (test).
- [ ] Wording check green on the walkthrough (test).
- [ ] "How to use" popover in the sidebar on every page, content read from the guide (test).
- [ ] Gate green.
