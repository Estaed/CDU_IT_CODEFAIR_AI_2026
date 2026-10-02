"""Tenant answers and coordinator lines: one headline per state, the reasons a remote job
waits, the counterfactual setting, sentences that stay true for the setting in force, and
plain wording (no deficit terms, grade 7 or lower) across every state."""

import ast
import re
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from fair_turn.core import constants, explain, weekly, wording
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

TODAY = date(2025, 6, 2)  # a Monday
OLD = TODAY - timedelta(weeks=20)  # urgency at its cap
BASE = "Katherine"
SIGNER = "R. Coordinator"
REASON = "Crews start Monday as planned."


def _place(cid: str, km: float, is_town: bool = False) -> weekly.Place:
    return weekly.Place(cid, BASE, is_town, km, -14.0, 132.0)


PLACES = {
    "K-TOWN": _place("K-TOWN", 0.0, is_town=True),
    "R-NEAR": _place("R-NEAR", 100.0),  # 0.5 driving days there and back
    "R-MID": _place("R-MID", 200.0),  # 1.0
    "R-FAR": _place("R-FAR", 450.0),  # 2.5
}


def job(
    jid: str,
    cid: str,
    reported: date = TODAY,
    cls: SafetyClass | None = SafetyClass.ROUTINE,
    fault: FaultType | None = FaultType.PLUMBING_WATER,
    health: frozenset[HealthRiskFactor] = frozenset(),
) -> Job:
    return Job(jid, cid, not PLACES[cid].is_town, reported, fault, cls, health)


def town_jobs(n: int) -> list[Job]:
    return [job(f"T{i:02d}", "K-TOWN") for i in range(n)]


def facts(
    target: Job,
    jobs: list[Job],
    setting_name: str = "Efficiency first",
    signed: bool = True,
    **plan_kw,
) -> explain.TenantFacts:
    """What the tenant page gathers for one job, the same way the app does."""

    def week(value: float, **kw) -> weekly.WeekPlan:
        return weekly.plan(jobs, PLACES, TODAY, value, {BASE: 1}, **kw)

    plan = week(constants.SETTINGS[setting_name], **plan_kw)
    trip = next((t for t in plan.trips if target.job_id in t.job_ids), None)
    start = None
    if trip is not None:
        start = next(s.start for c in plan.crews for s in c.stops if s.trip == trip)
    place = PLACES[target.community_id]
    closed = {"closed": plan_kw["closed"]} if "closed" in plan_kw else {}
    waiting = None if trip else plan.waiting_at(target.community_id)
    queue = None  # the tenant page's rule: place in line when only part of the repairs go
    if waiting is not None and waiting.reason == weekly.TRIP_FULL:
        queue = waiting.job_ids.index(target.job_id) + 1
    return explain.TenantFacts(
        job=target,
        today=TODAY,
        base=BASE,
        is_town=place.is_town,
        setting_name=setting_name,
        setting=constants.SETTINGS[setting_name],
        signed_by=SIGNER if signed else None,
        signed_reason=REASON if signed else None,
        trip=trip,
        start_day=start,
        waiting=waiting,
        travel_days=weekly.travel_days(place),
        queue_position=queue,
        in_plan_under=tuple(
            name
            for name, value in constants.SETTINGS.items()
            if target.job_id in week(value, **closed).planned_job_ids()
        ),
    )


def simple(target: Job, **kw) -> explain.TenantFacts:
    return explain.TenantFacts(
        job=target,
        today=TODAY,
        base=BASE,
        is_town=not target.is_remote,
        setting_name="Balanced",
        setting=constants.SETTINGS["Balanced"],
        signed_by=SIGNER,
        signed_reason=REASON,
        **kw,
    )


OVERDUE_FAR = job("F0", "R-FAR", OLD)  # planned only under "Most overdue first"
FRESH_FAR = job("F1", "R-FAR")  # planned under no setting
BUSY_TOWN = town_jobs(15)
# One crew, most overdue first: R-MID (priority 12, 4 days) and a town day (3) fill the
# week; R-FAR (priority 8, above the cut) needs 3 days in a row and finds none.
NO_ROOM_JOBS = [*(job(f"M{i}", "R-MID", OLD) for i in range(9)), OVERDUE_FAR, *town_jobs(3)]
# Ten at R-NEAR, the last reported latest: a trip carries nine.
FULL_NEAR = [job(f"N{i}", "R-NEAR", OLD + timedelta(i)) for i in range(10)]
# Twelve at R-NEAR, reported a day apart: nine go, the last three wait in report order.
LONG_LINE = [job(f"L{i:02d}", "R-NEAR", OLD + timedelta(i)) for i in range(12)]
# Twelve at R-FAR: a week's trip there carries only seven (2.5 driving + 2.5 work days).
BIG_FAR = [job(f"B{i:02d}", "R-FAR") for i in range(12)]


def all_states() -> dict[str, explain.TenantFacts]:
    """One set of facts per state the tenant page can show."""
    heat = frozenset(HealthRiskFactor)
    family = job("F2", "R-FAR", OLD, fault=FaultType.COOLING, health=heat)
    full = [job(f"N{i}", "R-NEAR", OLD) for i in range(9)] + [job("N9", "R-NEAR")]
    emergency = job("E0", "R-FAR", TODAY - timedelta(3), cls=SafetyClass.IMMEDIATE)
    return {
        "done": simple(job("D0", "K-TOWN", OLD), done_on=TODAY - timedelta(10)),
        "emergency_done": simple(emergency, done_on=TODAY - timedelta(3)),
        "after_today": simple(job("A0", "K-TOWN", TODAY + timedelta(2))),
        "needs_person": simple(
            job("H0", "K-TOWN", fault=None, cls=None),
            missing_fields=("fault_type", "safety_class"),
        ),
        "needs_person_one": simple(job("H1", "R-FAR", cls=None), missing_fields=("safety_class",)),
        "emergency": simple(job("E1", "R-FAR", cls=SafetyClass.IMMEDIATE)),
        "crew_town": facts(BUSY_TOWN[0], BUSY_TOWN),
        "crew_remote": facts(OVERDUE_FAR, [*BUSY_TOWN, OVERDUE_FAR], "Most overdue first"),
        "crew_remote_health": facts(family, [*BUSY_TOWN, family], "Most overdue first"),
        "outranked_counterfactual": facts(OVERDUE_FAR, [*BUSY_TOWN, OVERDUE_FAR]),
        "outranked_none": facts(FRESH_FAR, [*BUSY_TOWN, FRESH_FAR], "Balanced"),
        "outranked_big": facts(BIG_FAR[-1], [*BUSY_TOWN, *BIG_FAR]),
        "outranked_town": facts(job("T99", "K-TOWN"), [*BUSY_TOWN, job("T99", "K-TOWN")]),
        "no_room": facts(OVERDUE_FAR, NO_ROOM_JOBS, "Most overdue first"),
        "closed": facts(OVERDUE_FAR, [OVERDUE_FAR], closed={"R-FAR"}),
        "closed_until": replace(
            facts(OVERDUE_FAR, [OVERDUE_FAR], closed={"R-FAR"}), reopens_on=date(2025, 6, 9)
        ),
        "dropped": facts(OVERDUE_FAR, [OVERDUE_FAR], drop={"R-FAR"}),
        "trip_full": facts(full[-1], full, "Most overdue first"),
        "trip_full_efficiency": facts(FULL_NEAR[-1], FULL_NEAR),
        "trip_full_third": facts(LONG_LINE[-1], LONG_LINE),
        "unsigned": facts(OVERDUE_FAR, [*BUSY_TOWN, OVERDUE_FAR], signed=False),
    }


STATES = all_states()
ANSWERS = {name: explain.tenant_answer(f) for name, f in STATES.items()}


def test_the_states_are_the_ones_named() -> None:
    reasons = {
        "outranked_counterfactual": weekly.OUTRANKED,
        "outranked_none": weekly.OUTRANKED,
        "outranked_big": weekly.OUTRANKED,
        "outranked_town": weekly.OUTRANKED,
        "no_room": weekly.NO_ROOM,
        "closed": weekly.CLOSED,
        "dropped": weekly.DROPPED,
        "trip_full": weekly.TRIP_FULL,
        "trip_full_efficiency": weekly.TRIP_FULL,
        "trip_full_third": weekly.TRIP_FULL,
    }
    for name, reason in reasons.items():
        assert STATES[name].trip is None, name
        assert STATES[name].waiting.reason == reason, name
    assert STATES["crew_remote"].trip is not None


# --- headlines -----------------------------------------------------------------------------


def test_headline_done_before() -> None:
    assert ANSWERS["done"].headline == "This repair was done on 23 May 2025."


def test_headline_emergency_made_safe_before_the_planning_day() -> None:
    answer = ANSWERS["emergency_done"]
    assert answer.headline == "This emergency was made safe on 30 May 2025."
    assert "Any repair it still needs is a separate job." in answer.text
    assert "repair was done" not in answer.text


def test_headline_reported_after_today() -> None:
    answer = ANSWERS["after_today"]
    assert answer.headline == "Your report came in after this week's plan was made."
    assert "It joins the plan made next Monday." in answer.text


def test_needs_a_person_names_the_missing_fields() -> None:
    answer = ANSWERS["needs_person"]
    assert answer.headline == "A person is reading your report."
    assert "We could not read what is broken and how urgent it is" in answer.text
    one = ANSWERS["needs_person_one"].text
    assert "We could not read how urgent it is from your report." in one
    assert "what is broken" not in one


def test_headline_emergency() -> None:
    answer = ANSWERS["emergency"]
    assert answer.headline == "This is an emergency. It goes to the emergency make-safe team."
    assert f"within {constants.MAKE_SAFE_HOURS} hours" in answer.text
    assert "not part of the weekly crew plan" in answer.text


def test_headline_crew_coming_town_and_remote() -> None:
    assert ANSWERS["crew_town"].headline == (
        "Yes. A crew is planned in Katherine in the week of 02 June, from Monday."
    )
    assert ANSWERS["crew_remote"].headline == (
        "Yes. A crew is planned from Katherine to your community in the week of 02 June, "
        "from Monday."
    )
    assert "The crew will contact you before they come." in ANSWERS["crew_remote"].text


def test_start_day_names_the_weekday() -> None:
    f = facts(BUSY_TOWN[0], BUSY_TOWN)
    later = explain.tenant_answer(simple(BUSY_TOWN[0], trip=f.trip, start_day=3.5))
    assert later.headline.endswith("in the week of 02 June, from Thursday.")


def test_headline_not_this_week() -> None:
    for name in (
        "outranked_counterfactual",
        "outranked_none",
        "outranked_big",
        "no_room",
        "closed",
        "dropped",
        "trip_full",
    ):
        assert ANSWERS[name].headline == "Not in the week of 02 June.", name


def test_what_we_read_starts_with_the_repair_and_its_place() -> None:
    answer = ANSWERS["outranked_counterfactual"]
    read = next(b for b in answer.blocks if b.question == "What did we read in your report?")
    assert read.paragraphs[0] == "Repair F0, R-Far."
    named = Job(
        "JR-2025-00005", "BIG RIVERS R-01", True, TODAY, FaultType.OTHER, SafetyClass.URGENT
    )
    text = explain.tenant_answer(simple(named, waiting=None)).text
    assert "Repair JR-2025-00005, Big Rivers R-01." in text
    assert "Your report is about a repair outside our usual list." in text


@pytest.mark.parametrize(
    ("community_id", "name"),
    [("BIG RIVERS R-01", "Big Rivers R-01"), ("Katherine", "Katherine"), ("TOP END", "Top End")],
)
def test_place_name(community_id, name) -> None:
    assert explain.place_name(community_id) == name


def test_urgency_words_quote_the_nt_windows() -> None:
    days = constants.RESPONSE_BUSINESS_DAYS
    assert set(explain.URGENCY_WORDS) == set(constants.SAFETY_CLASSES)
    assert f"within {constants.MAKE_SAFE_HOURS} hours" in explain.URGENCY_WORDS["immediate"]
    for cls in ("urgent", "routine"):
        expected = (
            f"within {days[(cls, False)]} business days in town, "
            f"{days[(cls, True)]} in a remote community"
        )
        assert expected in explain.URGENCY_WORDS[cls]
    for cls, words in explain.URGENCY_WORDS.items():
        assert words.startswith(f"{cls}: ")
        # a coordinator-facing label, so only the deficit lexicon binds it, not grade 7
        assert [t for t in wording.check(words) if t != wording.READING_LEVEL] == []


def test_urgency_words_carry_no_literal_policy_numbers() -> None:
    tree = ast.parse(Path(explain.__file__).read_text("utf-8"))
    block = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "URGENCY_WORDS" for t in node.targets)
    )
    literals = [
        node.value
        for node in ast.walk(block)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert not [text for text in literals if re.search(r"\d", text)]


# --- why: true for the setting in force -----------------------------------------------------


def test_outranked_remote_answer_names_driving_days_and_setting() -> None:
    text = ANSWERS["outranked_counterfactual"].text
    assert "A trip to your community takes 2.5 days of driving, there and back" in text
    assert "to fix 1 repair." in text
    assert 'This week the setting is "Efficiency first"' in text
    assert explain.SETTING_MEANING["Efficiency first"] in text
    assert "The plan is made again every Monday." in text


def test_came_first_at_efficiency_first_is_about_repairs_not_need() -> None:
    text = ANSWERS["outranked_counterfactual"].text
    assert (
        "Trips that fixed the most repairs for each crew day came first. "
        "The days ran out before your trip." in text
    )
    assert "most need" not in text


def test_came_first_above_zero_is_about_need() -> None:
    text = ANSWERS["outranked_none"].text
    assert "Trips with the most need for each crew day came first" in text
    assert "fixed the most repairs" not in text


def test_never_claims_a_trip_larger_than_a_week_can_carry() -> None:
    waiting = STATES["outranked_big"].waiting
    assert len(waiting.job_ids) == 12 and waiting.trip_repairs == 7
    text = ANSWERS["outranked_big"].text
    assert "to fix 7 repairs." in text
    assert "12 repairs" not in text


def test_counterfactual_names_the_setting_that_would_plan_it() -> None:
    text = ANSWERS["outranked_counterfactual"].text
    assert 'Under "Most overdue first", a crew would come to you this week.' in text
    assert "None of the three" not in text


def test_no_setting_would_plan_it() -> None:
    text = ANSWERS["outranked_none"].text
    assert "None of the three named settings would plan your repair this week." in text
    assert "a crew would come to you" not in text


def test_town_answer_says_town_days_ran_out() -> None:
    text = ANSWERS["outranked_town"].text
    assert "The Katherine crews have more repairs than days this week, and others came first." in (
        text
    )
    assert 'This week the setting is "Efficiency first"' in text


def test_no_room_answer() -> None:
    text = ANSWERS["no_room"].text
    assert (
        "A trip to your community takes 3 days of a crew's week, with 2.5 days of driving "
        "there and back. By the time it came up, no Katherine crew had that many days left."
    ) in text
    assert "None of the three named settings would plan your repair this week." in text


def test_closed_answer_with_and_without_a_reopening_day() -> None:
    assert (
        "Access to your community is closed, for most of this week, so no trip was planned."
        in ANSWERS["closed"].text
    )
    assert (
        "Access to your community is closed until 09 June, for most of this week"
        in ANSWERS["closed_until"].text
    )


def test_dropped_answer() -> None:
    assert "The coordinator took your community's trip out" in ANSWERS["dropped"].text


def test_trip_full_names_the_carried_trip_and_the_order_under_the_setting() -> None:
    need = ANSWERS["trip_full"].text
    assert "A crew is going to your community this week, with time for 9 repairs." in need
    assert "Other repairs there had more need under this setting." in need
    first = ANSWERS["trip_full_efficiency"].text
    assert "with time for 9 repairs. Other repairs there were reported earlier." in first


def test_trip_full_says_the_place_in_line() -> None:
    assert STATES["trip_full_third"].waiting.job_ids == ("L09", "L10", "L11")
    assert STATES["trip_full_third"].queue_position == 3
    text = ANSWERS["trip_full_third"].text
    assert "Yours is number 3 in line there for the next trip." in text
    first = ANSWERS["trip_full_efficiency"].text
    assert "Yours is number 1 in line there for the next trip." in first
    # no place in line, no sentence about it
    no_queue = explain.tenant_answer(replace(STATES["trip_full_third"], queue_position=None))
    assert "in line there" not in no_queue.text


# --- what happens next ----------------------------------------------------------------------

COUNTS_FOR_MORE = "Each week your repair waits, it counts for more in the next plan."
ASK_FOR_A_TRIP = (
    "Your Community Housing Officer can ask the coordinator to add a trip for your community. "
    "The coordinator must give a reason, and it is written down."
)


def _next_block(name: str) -> tuple[str, ...]:
    return next(b for b in ANSWERS[name].blocks if b.question == "What happens next?").paragraphs


def test_next_at_efficiency_first() -> None:
    assert _next_block("outranked_counterfactual") == (
        "The plan is made again every Monday.",
        ASK_FOR_A_TRIP,
    )


def test_next_above_zero_and_below_the_cap_counts_for_more() -> None:
    assert _next_block("outranked_none") == (  # Balanced, reported today
        "The plan is made again every Monday.",
        COUNTS_FOR_MORE,
        ASK_FOR_A_TRIP,
    )


def test_next_at_the_urgency_cap() -> None:
    assert _next_block("no_room") == (  # most overdue first, far past its window
        "The plan is made again every Monday.",
        ASK_FOR_A_TRIP,
    )


def test_next_never_uses_the_old_waiting_sentences() -> None:
    for answer in ANSWERS.values():
        assert "does not move a repair up" not in answer.text
        assert "already counts as much as waiting" not in answer.text


def test_next_with_a_trip_says_the_crew_will_call() -> None:
    assert _next_block("crew_remote") == ("The crew will contact you before they come.",)


# --- who decided, wording ------------------------------------------------------------------


def test_health_risk_is_read_back() -> None:
    text = ANSWERS["crew_remote_health"].text
    assert "Your report is about cooling. We read it as routine." in text
    for words in explain.HEALTH_WORDS.values():
        assert f"We also read that {words}." in text


def test_who_decided_signed_and_unsigned() -> None:
    signed = ANSWERS["outranked_counterfactual"].text
    assert f"A person signed this week's plan: {SIGNER}. Their reason: {REASON}" in signed
    assert "This week's plan is not signed yet. It can still change." in ANSWERS["unsigned"].text


@pytest.mark.parametrize("name", sorted(ANSWERS))
def test_every_tenant_answer_passes_the_wording_check(name) -> None:
    assert wording.check(ANSWERS[name].text) == []


# --- sentences -----------------------------------------------------------------------------


def test_window_sentence_per_class() -> None:
    assert explain.window_sentence(job("A", "K-TOWN", cls=SafetyClass.URGENT)) == (
        "NT policy says urgent repairs in a town home are done within 2 business days."
    )
    assert explain.window_sentence(job("B", "R-FAR")) == (
        "NT policy says routine repairs in a remote home are done within 25 business days."
    )
    assert explain.window_sentence(job("C", "R-FAR", cls=SafetyClass.IMMEDIATE)) == (
        "NT policy says an emergency is made safe within 4 hours."
    )


@pytest.mark.parametrize(
    ("days_after", "sentence"),
    [
        (0, "The time limit started when you reported it."),
        (1, "It is 1 business day into that time limit."),
        (2, "It is 2 business days into that time limit."),
        (3, "It is 1 business day past that time limit."),
        (4, "It is 2 business days past that time limit."),
    ],
)
def test_wait_sentence(days_after, sentence) -> None:
    urgent = job("U", "K-TOWN", cls=SafetyClass.URGENT)  # 2 business days, reported Monday
    assert explain.wait_sentence(urgent, TODAY + timedelta(days_after)) == sentence


def test_wait_sentence_counts_business_days_only() -> None:
    friday = job("U", "K-TOWN", TODAY + timedelta(4))
    assert explain.wait_sentence(friday, TODAY + timedelta(6)) == (
        "The time limit started when you reported it."
    )
    assert explain.wait_sentence(friday, TODAY + timedelta(7)) == (
        "It is 1 business day into that time limit."
    )


def test_wait_sentence_for_an_emergency_does_not_count_business_days() -> None:
    friday = job("E", "K-TOWN", TODAY + timedelta(4), cls=SafetyClass.IMMEDIATE)
    assert explain.wait_sentence(friday, TODAY + timedelta(4)) == (
        "The time limit started when you reported it."
    )
    assert explain.wait_sentence(friday, TODAY + timedelta(7)) == (
        "It was reported before today, so it is past that time limit."
    )


def test_trip_line_remote_and_town() -> None:
    jobs = [*BUSY_TOWN, OVERDUE_FAR]
    by_id = {j.job_id: j for j in jobs}
    plan = weekly.plan(jobs, PLACES, TODAY, 1.0, {BASE: 1})
    far = plan.trip_to("R-FAR")
    assert explain.trip_line(far, by_id, TODAY) == (
        "1 repair, 1 past the NT time limit · 2.5 days driving + 0.5 days work"
    )
    town = plan.trip_to("K-TOWN")
    assert explain.trip_line(town, by_id, TODAY) == "3 repairs · 1 day in town"


def _line(jobs: list[Job], cid: str, setting: float, **kw) -> str:
    plan = weekly.plan(jobs, PLACES, TODAY, setting, {BASE: 1}, **kw)
    return explain.waiting_line(plan.waiting_at(cid), plan)


def test_waiting_line_per_reason() -> None:
    far = [*BUSY_TOWN, OVERDUE_FAR]
    assert _line(far, "R-FAR", 0.0) == (
        "Other trips came first (0.3 a crew-day; the last trip in was 3.0)"
    )
    assert _line(far, "R-FAR", 0.0, closed={"R-FAR"}) == "Access closed most of the week"
    assert _line(far, "R-FAR", 0.0, drop={"R-FAR"}) == "Taken out by you"
    full = [job(f"N{i}", "R-NEAR", OLD) for i in range(10)]
    assert _line(full, "R-NEAR", 1.0) == "Partly planned: the trip carries 9"
    assert _line(NO_ROOM_JOBS, "R-FAR", 1.0) == "Needs 3 days in a row; no crew had them left"


def test_waiting_line_after_an_added_trip() -> None:
    jobs = [*BUSY_TOWN, OVERDUE_FAR, job("N0", "R-NEAR")]
    assert _line(jobs, "R-FAR", 0.0, add={"R-NEAR"}) == (
        "Other trips came first, after your added trip (0.3 a crew-day; the last trip in was 3.0)"
    )


def test_waiting_line_tie_says_the_days_ran_out() -> None:
    # 18 town repairs, one crew: the last three are worth 3.0 a crew-day, as is the cut.
    assert _line(town_jobs(18), "K-TOWN", 0.0) == (
        "Other trips came first (a tie at 3.0 a crew-day; the days ran out)"
    )
    with_added = [*town_jobs(18), job("N0", "R-NEAR")]
    assert _line(with_added, "K-TOWN", 0.0, add={"R-NEAR"}) == (
        "Other trips came first, after your added trip (a tie at 3.0 a crew-day; the days ran out)"
    )


def _outranked(priority: float | None, cut: float | None) -> str:
    """The line for a hand-made plan: one waiting place and, if ``cut``, one trip."""
    trips = () if cut is None else (weekly.Trip("K-TOWN", BASE, True, ("T0",), 0.0, 1.0, cut),)
    waiting = weekly.Waiting("R-FAR", BASE, ("F0",), weekly.OUTRANKED, priority)
    plan = weekly.WeekPlan(TODAY, 0.0, trips, (), (waiting,))
    return explain.waiting_line(waiting, plan)


def test_waiting_line_tie_is_decided_at_one_decimal() -> None:
    assert (
        _outranked(2.96, 3.0)
        == "Other trips came first (a tie at 3.0 a crew-day; the days ran out)"
    )
    assert _outranked(2.94, 3.0) == (
        "Other trips came first (2.9 a crew-day; the last trip in was 3.0)"
    )


def test_waiting_line_without_a_priority_or_cut() -> None:
    assert _outranked(None, 3.0) == "Other trips came first"
    assert _outranked(1.0, None) == "Other trips came first"
