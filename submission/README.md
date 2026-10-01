# Submission folder

Put the two non-code deliverables here before packaging; `scripts/package_submission.py`
copies this whole folder into the zip and warns when no PDF is present.

- The project report PDF. The published rule names it `DataChallenge_Team xx(number)_Report.pdf`
  (copied from the Data Innovation Challenge page; see `docs/competition-notes.md`). Format:
  `docs/report-requirements.md`.
- The pitch slides (PDF export of the deck), if the team sends them.

Then, from the repo root on a clean, committed tree:

    venv/Scripts/python scripts/package_submission.py --team <N>

Open the zip and check it before emailing it to itcodefair@cdu.edu.au with the subject
`AI Challenge Submission – [Group] – IT Code Fair 2026`.
