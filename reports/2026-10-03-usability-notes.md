# Usability notes on the review screen (2026-10-03, after Task-16)

The orchestrator's own pass over the wave 6 and 6b screenshots (A-0142, E-02 at 1280 and 1440),
asked for by Tarık. These are input for the next screen task, not decisions. U6 needs Tarık's call.

| # | What the officer sees | Why it hurts | Suggested fix |
|---|---|---|---|
| U1 | "Sign decision" is a grey button at all times. When everything is ready, "Next: sign decision" and "Sign decision" sit side by side | Grey reads as disabled (Tarık). Two buttons do one job | Not ready: an outlined button, "Sign decision · 3 questions left". Ready: one green primary button. Signed: a green "Signed ✓" badge |
| U2 | Every decided question shows the same blue tick, including "Cannot decide yet" | "Cannot decide yet" looks finished, and Met looks the same as Not met | One icon per outcome, with the word kept: Met ✓ green, Not met ✗ red, Cannot decide yet ⏸ amber |
| U3 | After signing, the "Sign decision" row still has a dashed circle | It does not look done | A green lock or tick, with "Signed · record locked" |
| U4 | "Opened · in view 0 s" under every passage on the page | Noise on the reading surface; "0 s" reads like an error | Remove it from the page. The record keeps the times |
| U5 | The same tag ("Urgent-need category · Possibly missed") repeats on each paragraph of one page | Heavy. Tags look like the main content | Tag the first paragraph of a run in full. Later paragraphs get a small marker |
| U6 | Page 8 is on screen when the case opens, yet the list says "0 of 2 opened" | The officer is looking at it and the app says they have not opened it | **Tarık decides:** a page counts as opened after N seconds in view (for example 3 s), still recorded with its time. Today a 0.1 s glance also counts once it is clicked |
| U7 | "Open before you sign" says "Page 1, paragraph 1"; the tab says "Page 1" | Two names for one thing | Use the same label in both places |
| U8 | "Other facts · no outcome needed" | Unclear what it is for | "Background facts (no decision needed)" |
| U9 | The check page and the exported record say "Clause outcomes"; the HTML export also uses "clause" (in `readmark/record`, outside Task-16's lane) | Same word problem Task-16 fixed on the screen | "Your answers to the questions" |
| U10 | "AI claims · N" opens to the AI's sentences with technical labels | Tarık could not follow it | Task-17: "What the AI noted (N)", one plain card per note (note, quote and page, check result in words, "This note is wrong") |
