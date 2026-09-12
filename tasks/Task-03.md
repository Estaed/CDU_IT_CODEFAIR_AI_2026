# Task-03: Synthetic labels, personas, closures and climate table

> **Execution:** agent `claude` (main loop) · effort `high` · plan mode **yes**
> *Why:* the skew design (which mechanisms differ town/remote and by how much) is the trust twist's evidence base; the how is still open in places and the choices go in the report.

**Lane**
- OWNS: `fair_turn/data/synth.py`, `scripts/build_labels.py`, `data/build/labels.json`, `data/build/personas.json`, `data/build/closures.json`, `data/build/climate.csv`, `tests/test_synth.py`
- MUST NOT TOUCH: `fair_turn/core/` (Task-00, Task-02), `fair_turn/data/geography.py` (Task-01)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-01, Task-02

## Objective

Draw the ground truth in code before any model writes a word: about 1,500 label tuples
over the 90-day window with the three town/remote skew mechanisms built in on purpose,
plus the household personas the generator will be conditioned on.

## Execution Guide

- `synth.py`: `draw_labels(communities, seed) -> list[dict]`; each label: `job_id` (registration-number style, e.g. `JR-2025-00417`), `community_id`, `reported_on`, `fault_type`, `safety_class`, `health_risk` (list), `persona_id`, `is_holdout` (150 items flagged for eval), `is_adversarial` placeholder False. Report rate per community proportional to population band, remote base rate 0.8 × town (mechanism 3, static part); fault-type mix seasonal (cooling and hot water up in heat season); safety-class mix from FS17 proportions stated in `constants.md` as provisional.
- Personas (`personas.json`): about 40 household descriptions (composition, tenure length, register: terse / detailed / second-language English / phoned-in via CHO), no names, no community names.
- `closures.json`: for each `wet_season_closable` community, closure intervals drawn within Oct–Dec with total closed days rising through December; labelled synthetic.
- `climate.csv`: daily max temperature and a heat-warning flag per region for the window, drawn around BoM published monthly normals (cite in PROVENANCE.md), not fetched.
- `scripts/build_labels.py` writes the four files; idempotent for the same seed.
- Tests: same seed → identical files; remote share within 0.55–0.65; exactly 150 holdout items; every `community_id` exists in `communities.csv`; no persona contains a real name.

## Acceptance Criteria (DoD)

- [ ] Four artefacts committed; `build_labels.py` twice yields byte-identical output.
- [ ] `test_synth.py` passes, including the distribution assertions above.
- [ ] Every provisional proportion used is listed in `constants.md` with "provisional, PRD §6.2".
- [ ] `test_wording.py` and the real-name test still pass over the new artefacts.
- [ ] Gate green.
