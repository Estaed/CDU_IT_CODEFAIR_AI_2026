"""Today's steps strip: four steps with live state, the first open one marked Next (PRD 3.1)."""

import re

from fair_turn.app.components import today_steps

JARGON = re.compile(r"λ|lambda|batch v|fingerprint|enum", re.IGNORECASE)


def test_a_fresh_morning_marks_the_first_step_next_and_counts_what_is_left() -> None:
    steps = today_steps.steps(review_left=21, to_decide=13, signed=False, plan_accepted=False)
    assert [s.title for s in steps] == [
        "Jobs that need a person",
        "Decide today's jobs",
        "Choose the weighting and sign",
        "Open the visit plan",
    ]
    assert [s.done for s in steps] == [False, False, False, False]
    assert [s.is_next for s in steps] == [True, False, False, False]
    assert steps[0].text == "21 left: open the Needs a human tab and fill in each one."
    assert steps[1].text == (
        "13 left: open each job, read it to the bottom, then Accept or Reject."
    )
    assert "Review and sign" in steps[2].text
    assert "visit plan" in steps[3].text


def test_next_moves_to_the_first_step_not_done() -> None:
    steps = today_steps.steps(review_left=0, to_decide=0, signed=False, plan_accepted=False)
    assert [s.done for s in steps] == [True, True, False, False]
    assert [s.is_next for s in steps] == [False, False, True, False]


def test_every_step_done_leaves_no_next() -> None:
    steps = today_steps.steps(review_left=0, to_decide=0, signed=True, plan_accepted=True)
    assert all(s.done for s in steps)
    assert not any(s.is_next for s in steps)


def test_nothing_to_decide_counts_as_done_and_texts_are_plain_words() -> None:
    for signed in (False, True):
        steps = today_steps.steps(review_left=0, to_decide=0, signed=signed, plan_accepted=False)
        assert steps[1].done
        assert not any(JARGON.search(s.title + s.text) for s in steps)
