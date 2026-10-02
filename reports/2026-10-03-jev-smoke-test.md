# Jev smoke test for brief 6 (2026-10-03)

Input for decisions, not a decision. The data was synthetic (an invented case file) plus quoted NT
policy text, so no personal data was sent. Tarık's existing TypeSafe key from `D:/TarikOS/.env` was
used; the key is not stored in this repo. Scripts: `.tmp/jev_smoke.py` and `.tmp/jev_scan.py` (git-ignored).

**Endpoint:** `POST https://api.typesafe.ai/v1/systemone` with body
`{"model": "jev-latest", "state": {...}, "questions": {...}}`. The response model was `jev-1.13.0`.

## 1. Claim support (one call per claim–passage pair, two questions per call)
Questions:
- `noul`: "Does the passage, read on its own, support every part of the claim?"
- `choice`: supports / contradicts / not_enough_information.

| Case | Passage | Claim | noul | choice (confidence) | Latency |
|---|---|---|---|---|---|
| Supported | p.23 March ledger, "Arrears cleared in full" | "Arrears were cleared in March 2026" | 0.85 | supports (0.97) | 0.42 s |
| Stale value | p.23 March ledger | "Currently owes $2,400" | 0.01 | contradicts (1.00) | 0.35 s |
| Policy misread | Eligibility §3.4 | "Not eligible because of rent debt" | 0.02 | contradicts (0.97) | 0.36 s |

**Result:** 3 of 3 correct, about 410 input tokens per call.

## 2. Relevance scan (one `score` question per passage, 0–4)
- **Clause:** Priority §3.1, urgent need must be documented.
- **Passages:** six synthetic ones, scored in parallel with 6 threads. Wall time 0.6 s.

| Passage | Score |
|---|---|
| p.51 support letter (family violence, police attended) | **2.92** |
| p.44 GP note (anxiety, poor sleep) | 0.91 |
| p.12 application form (household) | 0.25 |
| p.30 previous tenancy | 0.17 |
| p.8 January ledger | 0.05 |
| p.57 vehicle registration | 0.00 |

**Result:** the decisive passage ranked first by a wide margin, and the plausible secondary one
ranked second.

## Limits
- n=3 and n=6: a smoke test, not an evaluation.
- The scores are not calibrated probabilities, so calibration has to be measured on the gold set.
- Jev is not deterministic.
- Cost at the published price ("$42 per billion input tokens", see the landscape survey §4): a full
  scan of about 300 passages × 5 clauses ≈ 1,500 calls ≈ 0.6 M tokens ≈ US$0.03.
- Rate limits for this key are unknown. The demo should run on precomputed results, so it needs no
  network at the Fair.
