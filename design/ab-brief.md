# A/B functional brief (one screen, desktop)

A and B are judged against this brief. B was drawn blind on 2026-10-03: no `tasarim` skill, no
DESIGN.md, no mock. A follows the `tasarim` skill (Tarik Base). Content and behaviour are identical;
only the visual design differs.

**Who and where:** an NT Government delegated officer in Darwin assessing an urban priority
social-housing application at a desk, on a 1280–1440 px screen. They are busy with a backlog. The
tool makes them faster without letting them trust an AI summary they haven't checked.

## What the screen does
1. **Case header:** "Applicant file A-0142" (synthetic file, 62 pages), checked against 5 NT public
   housing policies; a required-reading counter "0/4" that fills as required passages are opened.
2. **Evidence by policy clause (main view):** groups per decisive clause. Each row shows the
   **verbatim quote first**, then the AI's one-line claim, then a status. Three separate status
   lists, never mixed:
   - **claim check:** quote not found / checker disagrees / contradicted by another passage / supported;
   - **clause coverage:** possibly missed / no evidence in file;
   - **clause outcome**, set ONLY by the officer through a control on each group: met / not met /
     cannot decide yet (request information). The AI never pre-fills it.

   Colour is never the only signal.
3. **Source pane:** passages open one at a time. Each shows the document name, page or clause, a
   label ("Real NT policy" / "Synthetic file"), the text with the exact quote highlighted, and
   "opened hh:mm:ss · in view Ns".
4. **"Summary under audit" tab:** a plain one-paragraph summary produced elsewhere, each sentence
   marked with how it fared against the file.
5. **Sign-off:** "Sign decision" stays enabled. If required passages are unopened it names the
   missing ones. Once all are opened, a dialog asks for a decision (approve priority / decline /
   request more information) and a required reason. Then a decision record replaces the source
   pane: decision, reason, signed time, each passage opened with time and seconds in view, disputes.
6. **Disputes:** each AI claim can be disputed with a reason, and the dispute goes into the record.
7. **Empty state** of the source pane.

## Content (verbatim)
**Policy passages (real NT text):**
- Eligibility for Social Housing §3.4 Debts: "The provision of social housing will not be withheld
  based on a debt owed to the CEO (Housing). The CEO (Housing) will seek to recover outstanding debts
  in line with the Debt Management policy."
- Eligibility §3 (urban applicants): "If applying for urban social housing or private rental bond
  assistance, applicants must also qualify under additional income based criteria which are
  specified in the Income and Assets policy."
- Priority housing §3.1: "Applicants must prove their urgent need for priority housing and are
  required to provide documentation that supports their claim for priority."

**Case-file passages (synthetic):**
- p. 8, rent ledger (former public tenancy), statement 15 Jan 2026: "Former tenancy debt owed to the
  CEO (Housing). Arrears balance $2,400.00. Payment plan proposed at $100 per fortnight."
- p. 23, rent ledger, statement 4 Mar 2026: "Lump-sum payment received from a support agency on
  behalf of the former tenant. Arrears cleared in full. Balance $0.00."
- p. 30, previous tenancy record: "Tenancy at a Palmerston property ended by mutual agreement on
  12 June 2023. A rent debt remained outstanding at exit. No breach of the tenancy agreement recorded."
- p. 51, letter from a support agency: "Ms K. and her two children are fleeing family violence and
  cannot safely return to their current address. Police attended the property on 2 February 2026."

**Evidence groups:**
- **Debts (§3.4):**
  - "Rent arrears of $2,400 are outstanding" [p. 8] → contradicted by another passage (p. 23). Both
    pages are required.
  - "Debt to the CEO (Housing) does not stop social housing" [§3.4] → supported; §3.4 is required.
- **Urgent need documented (Priority §3.1):** coverage "possibly missed". p. 51 scored highly
  relevant, but the summary under audit never used it. p. 51 is required.
- **Previous tenancy (Eligibility §3.5):** "Previous tenancy ended by agreement in June 2023 with no
  breach" [p. 30] → supported.
- **Income evidence (Eligibility §3):** coverage "no evidence in file". The next step is to request it.

**Required reading** = §3.4, p. 8, p. 23, p. 51.

**Summary under audit** (a general-purpose AI given a one-line "summarise this file" prompt): "Ms K.
applied for priority housing for herself and two children. The rent ledger shows arrears of $2,400.
Because of the outstanding debt, the applicant does not meet the criteria for priority housing. A
previous tenancy ended in 2023. Recommendation: decline."
- arrears → contradicted by p. 23;
- debt makes her ineligible → contradicted by §3.4;
- the family violence letter → not mentioned (possibly missed);
- recommendation → the tool makes none; the officer decides.

**Footer:** "Synthetic case file. Policy text from NT public housing policies. Opening a passage is
recorded; it does not prove it was read."
