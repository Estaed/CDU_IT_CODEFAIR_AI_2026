"""Today's steps (PRD 3.1): the day's four steps as a strip of tiles at the top of the
workspace, each with its live state and one line on what to do next, so a first-time user
needs no document. ``steps`` is pure; ``render`` only draws what it returns."""

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class Step:
    title: str
    done: bool
    text: str
    is_next: bool = False


def steps(review_left: int, to_decide: int, signed: bool, plan_accepted: bool) -> list[Step]:
    """``to_decide`` is the number of jobs left in To decide; ``signed`` means today's list is
    signed and not changed since; ``plan_accepted`` that a visit plan for that signed batch
    was accepted."""
    drafts = [
        Step(
            "Jobs that need a person",
            review_left == 0,
            "No job needs a person."
            if review_left == 0
            else f"{review_left} left: open the Needs a human tab and fill in each one.",
        ),
        Step(
            "Decide today's jobs",
            to_decide == 0,
            "Every job on today's list is decided."
            if to_decide == 0
            else f"{to_decide} left: open each job, read it to the bottom, then Accept or Reject.",
        ),
        Step(
            "Choose the weighting and sign",
            signed,
            "Today's list is signed."
            if signed
            else (
                "Pick a weighting in the sidebar, read the effect line, then Review and sign below."
            ),
        ),
        Step(
            "Open the visit plan",
            plan_accepted,
            "The visit plan is accepted."
            if plan_accepted
            else "After signing, the visit plan turns the list into crew run sheets.",
        ),
    ]
    first_open = next((i for i, step in enumerate(drafts) if not step.done), None)
    return [
        Step(step.title, step.done, step.text, is_next=i == first_open)
        for i, step in enumerate(drafts)
    ]


def render(day_steps: list[Step]) -> None:
    columns = st.columns(len(day_steps))
    for number, (column, step) in enumerate(zip(columns, day_steps, strict=True), 1):
        with column, st.container(border=True):
            st.markdown(f"**{number}. {step.title}**")
            if step.done:
                st.badge("Done", icon=":material/check:", color="green")
            elif step.is_next:
                st.badge("Next", color="orange")
            st.markdown(step.text)
