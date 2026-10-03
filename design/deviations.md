# Deviations from the reference

Reference: `reports/screens/ui-references/mock-6-gov-filepanel.png` (`design/DESIGN.md`). These
are intended differences in the Task-15 screen, from the builder's list and the orchestrator's
review (2026-10-03).

- **Service label:** the header band reads "NT priority housing · Demonstration service", not "NT
  Government, Territory Families, Housing & Communities". The app is not a government service.
- **Wait-time line:** it keeps the full honest wording from Task-13 ("historical, not
  priority-specific").
- **Opened counts:** no passage counts as opened when the screen first loads. Showing a page is not
  the same as the officer opening it, so the opening screen reads "0 of 2 opened" while page 8 is
  in view.
- **Order:** questions are ordered by their flags, from `view.json`, not in a fixed list. Clean
  questions fold into "1 question looks clean" (Blueprint), and "Other facts · no outcome needed"
  is a quiet row.
- **Tabs:** the required pages come first, then at most 2 more. Every other page that a claim
  cites or that is possibly missed sits under "More pages (N)", grouped "Cited by the AI's claims"
  and "Possibly missed". The mock showed only two tabs.
- **Full file:** "Open in full file" opens the whole file in a large dialog, with previous / next
  flag. This is the Task-11 reader.
- **Kept from before:** "How this works", "About these checks", "The policy question" and "AI
  claims · N" stay, as disclosures under the viewer.
- **Type and width:** no text is below 13 px. The question list is narrower at 1280.
