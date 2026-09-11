# AI Challenge — the six official task briefs

Transcribed verbatim on 11 September 2026 from
<https://itcodefair.cdu.edu.au/ai-challenge-task-details/>.

Teams pick **one**. Each brief has the same four parts: the "How Might We" question, the
**User** it serves, what to **Build**, and the **Trust twist** that makes it hard.

The framing sentence from the overview page applies to all six:

> "How Might We…" prompts for the Trusted AI decision-support challenge — pick one and run
> with it. Each is framed as an open "How Might We" question so you can shape your own
> solution, but comes with a real user, a decision to support, and the trust twist that makes
> it worth doing. Whatever you choose, scope it to one decision, one user, synthetic or
> public data — and remember the AI assists, a human decides.

---

## 1. Housing maintenance triage

**HMW:** How might we help a housing maintenance coordinator prioritise urgent repairs across
remote NT communities without "efficiency" quietly pushing remote tenants to the back of the
queue?

**User:** a coordinator drowning in repair requests, with too few trades and huge travel
distances.

**Build:** something that reads free-text fault reports, ranks jobs by urgency + safety +
logistics, and explains why each job sits where it does.

**Trust twist:** it's always "cheaper" to fix the town first — make the equity trade-off
visible and let the human own it. A tenant should be able to ask why their repair was
deprioritised and get a real answer.

---

## 2. Grant eligibility assessment

**HMW:** How might we help a grants officer assess applications consistently and produce
reasons a rejected applicant could actually understand and challenge?

**User:** an officer checking applications against published guidelines, under deadline
pressure.

**Build:** a tool that maps each application to each eligibility rule, cites both the rule and
the applicant's supporting text, and drafts reasons for a decision.

**Trust twist:** consistency is good, rubber-stamping is not. Require human sign-off, and
don't penalise applicants who write in plainer or second-language English instead of judging
the substance.

---

## 3. Information-access (FOI) request triage

**HMW:** How might we help an information officer find the records relevant to a request while
guaranteeing a human reviews anything sensitive before it's released?

**User:** an officer processing access requests over large, messy document sets.

**Build:** retrieval that surfaces relevant documents, flags likely personal/sensitive content
for human redaction review, and summarises the set.

**Trust twist:** nothing is released or redacted automatically. Reason about error costs — a
missed exemption is a privacy breach; over-flagging buries the officer.

---

## 4. Risk-based inspection prioritisation

**HMW:** How might we help a regulator decide where to send limited inspectors first, without
the model just re-checking wherever it looked last time?

**User:** an inspector choosing which premises to visit across a large area with few staff.

**Build:** a risk-ranking model that orders premises and shows the factors behind each score.

**Trust twist:** the feedback-loop trap — if you only inspect where you inspected before, the
data will "prove you right" forever. Watch for proxies that unfairly target certain areas or
business types.

---

## 5. Getting urgent messages to a human, fast

**HMW:** How might we make sure a vulnerable person's urgent message never gets buried in a
high-volume government inbox and reaches a human quickly?

**User:** a correspondence/complaints unit triaging a flood of public contact.

**Build:** classification + urgency detection that routes and prioritises items and drafts
acknowledgements, with an explanation for each call.

**Trust twist:** the whole design goal is the escalation path — anything flagged serious
should reach a human immediately, and the system should escalate, never try to respond itself.

---

## 6. Making sense of long documents without over-trusting the AI

**HMW:** How might we help a caseworker get through a backlog of long policy or case documents
faster, without nudging them into trusting a summary they haven't verified?

**User:** a caseworker who must read and interpret large volumes of policy or case material.

**Build:** a summariser that links every claim back to the exact source passage, and flags
where it's unsure.

**Trust twist:** speed can breed complacency. Design it so verification is easy and the human
stays accountable for what they act on.
