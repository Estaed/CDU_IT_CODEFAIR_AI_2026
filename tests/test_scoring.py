"""Need score: NT windows, business days over weekends, the overdue boundary, the urgency cap,
heat escalation and the health-risk part."""

from datetime import date, timedelta

import pytest

from fair_turn.core import constants, scoring
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

MONDAY = date(2025, 6, 2)  # June: outside the heat season
FRIDAY = date(2025, 6, 6)
DECEMBER = date(2025, 12, 1)  # inside the heat season


def job(
    reported: date = MONDAY,
    cls: SafetyClass | None = SafetyClass.ROUTINE,
    fault: FaultType | None = FaultType.PLUMBING_WATER,
    remote: bool = False,
    health: frozenset[HealthRiskFactor] = frozenset(),
) -> Job:
    return Job("J1", "C1", remote, reported, fault, cls, health)


@pytest.mark.parametrize("remote", [False, True])
@pytest.mark.parametrize("cls", [SafetyClass.URGENT, SafetyClass.ROUTINE])
def test_window_per_class_and_remoteness_comes_from_constants(cls, remote) -> None:
    expected = constants.RESPONSE_BUSINESS_DAYS[(cls.value, remote)]
    assert scoring.window_days(job(cls=cls, remote=remote)) == expected


def test_window_values_town_and_remote() -> None:
    assert scoring.window_days(job(cls=SafetyClass.URGENT)) == 2
    assert scoring.window_days(job(cls=SafetyClass.URGENT, remote=True)) == 5
    assert scoring.window_days(job(cls=SafetyClass.ROUTINE)) == 10
    assert scoring.window_days(job(cls=SafetyClass.ROUTINE, remote=True)) == 25


def test_immediate_window_is_four_hours_town_and_remote() -> None:
    for remote in (False, True):
        window = scoring.window_days(job(cls=SafetyClass.IMMEDIATE, remote=remote))
        assert window == constants.MAKE_SAFE_HOURS / 24


def test_window_without_class_raises() -> None:
    with pytest.raises(ValueError):
        scoring.window_days(job(cls=None))


def test_business_days_skip_the_weekend() -> None:
    saturday, sunday, monday = FRIDAY + timedelta(1), FRIDAY + timedelta(2), FRIDAY + timedelta(3)
    assert scoring.business_days_between(FRIDAY, saturday) == 0
    assert scoring.business_days_between(FRIDAY, sunday) == 0
    assert scoring.business_days_between(FRIDAY, monday) == 1
    assert scoring.business_days_between(MONDAY, FRIDAY) == 4
    assert scoring.business_days_between(FRIDAY, FRIDAY + timedelta(7)) == 5
    assert scoring.business_days_between(MONDAY, MONDAY + timedelta(14)) == 10
    assert scoring.business_days_between(saturday, monday) == 1


def test_business_days_zero_when_end_not_later() -> None:
    assert scoring.business_days_between(MONDAY, MONDAY) == 0
    assert scoring.business_days_between(FRIDAY, MONDAY) == 0


def test_business_days_match_a_day_by_day_count() -> None:
    start = date(2025, 5, 28)
    for n in range(40):
        end = start + timedelta(n)
        by_hand = sum((start + timedelta(k)).weekday() < 5 for k in range(1, n + 1))
        assert scoring.business_days_between(start, end) == by_hand


def test_public_holidays_are_not_business_days() -> None:
    christmas_eve = date(2025, 12, 24)  # Wednesday; 25 and 26 December are holidays
    assert scoring.business_days_between(christmas_eve, date(2025, 12, 26)) == 0
    assert scoring.business_days_between(christmas_eve, date(2025, 12, 29)) == 1
    assert scoring.business_days_between(date(2025, 12, 25), date(2025, 12, 29)) == 1
    assert scoring.business_days_between(date(2025, 12, 31), date(2026, 1, 2)) == 1
    for holiday in constants.PUBLIC_HOLIDAYS:
        assert scoring.business_days_between(holiday - timedelta(1), holiday) == 0


def test_business_days_match_a_day_by_day_count_over_the_holidays() -> None:
    start = date(2025, 12, 10)
    for n in range(40):
        end = start + timedelta(n)
        by_hand = sum(
            (day := start + timedelta(k)).weekday() < 5 and day not in constants.PUBLIC_HOLIDAYS
            for k in range(1, n + 1)
        )
        assert scoring.business_days_between(start, end) == by_hand


def test_overdue_boundary_moves_past_the_holidays() -> None:
    urgent = job(reported=date(2025, 12, 23), cls=SafetyClass.URGENT)  # 2 business days
    assert not scoring.is_overdue(urgent, date(2025, 12, 29))  # 24 Dec and 29 Dec used
    assert scoring.is_overdue(urgent, date(2025, 12, 30))


def test_is_overdue_boundary_urgent_town() -> None:
    urgent = job(cls=SafetyClass.URGENT)  # 2 business days, reported Monday
    assert not scoring.is_overdue(urgent, MONDAY + timedelta(2))  # Wednesday: 2 used
    assert scoring.is_overdue(urgent, MONDAY + timedelta(3))  # Thursday: 3 used


def test_is_overdue_boundary_routine_remote_over_weekends() -> None:
    routine = job(remote=True)  # 25 business days = five weeks of weekdays
    assert not scoring.is_overdue(routine, MONDAY + timedelta(weeks=5))
    assert scoring.is_overdue(routine, MONDAY + timedelta(weeks=5, days=1))


def test_immediate_uses_calendar_days() -> None:
    immediate = job(cls=SafetyClass.IMMEDIATE, reported=FRIDAY)
    assert not scoring.is_overdue(immediate, FRIDAY)
    assert scoring.is_overdue(immediate, FRIDAY + timedelta(1))  # Saturday counts


def test_urgency_is_window_share_and_capped() -> None:
    routine = job()  # town routine, 10 business days
    assert scoring.urgency(routine, MONDAY) == 0.0
    assert scoring.urgency(routine, MONDAY + timedelta(7)) == 0.5
    assert scoring.urgency(routine, MONDAY + timedelta(14)) == 1.0
    assert scoring.urgency(routine, MONDAY + timedelta(weeks=6)) == scoring.URGENCY_CAP
    assert scoring.urgency(routine, MONDAY + timedelta(weeks=50)) == scoring.URGENCY_CAP


def test_urgency_before_report_is_zero() -> None:
    assert scoring.urgency(job(), MONDAY - timedelta(5)) == 0.0


def test_safety_weights() -> None:
    assert scoring.safety(job(cls=SafetyClass.ROUTINE), MONDAY) == 1.0
    assert scoring.safety(job(cls=SafetyClass.URGENT), MONDAY) == 2.0
    assert scoring.safety(job(cls=SafetyClass.IMMEDIATE), MONDAY) == 3.0


@pytest.mark.parametrize(
    ("fault", "remote", "today", "escalated"),
    [
        (FaultType.COOLING, True, DECEMBER, True),
        (FaultType.HOT_WATER, True, date(2026, 1, 15), True),
        (FaultType.COOLING, False, DECEMBER, False),  # town
        (FaultType.PLUMBING_WATER, True, DECEMBER, False),  # not heat sensitive
        (FaultType.COOLING, True, MONDAY, False),  # June, outside the heat season
        (FaultType.HOT_WATER, True, date(2025, 4, 1), False),  # April: wet, not heat
    ],
)
def test_heat_escalation_only_remote_cooling_or_hot_water_in_heat_month(
    fault, remote, today, escalated
) -> None:
    j = job(fault=fault, remote=remote, reported=today)
    expected = 1.0 + (scoring.HEAT_ESCALATION if escalated else 0.0)
    assert scoring.safety(j, today) == expected


def test_health_risk_counts_factors() -> None:
    assert scoring.health_risk(job()) == 0.0
    two = frozenset({HealthRiskFactor.ELDERLY, HealthRiskFactor.OVERCROWDING})
    assert scoring.health_risk(job(health=two)) == 2 * scoring.HEALTH_RISK_PER_FACTOR


def test_need_is_the_sum_of_its_factors() -> None:
    j = job(
        cls=SafetyClass.URGENT,
        fault=FaultType.COOLING,
        remote=True,
        reported=DECEMBER,
        health=frozenset({HealthRiskFactor.ELDERLY}),
    )
    today = DECEMBER + timedelta(2)  # Wednesday: 2 of 5 business days
    factors = scoring.need_factors(j, today)
    assert factors == {"urgency": 0.4, "safety": 3.0, "health_risk": 0.5}
    assert scoring.need(j, today) == pytest.approx(3.9)


@pytest.mark.parametrize(
    ("fault", "cls"),
    [(None, SafetyClass.URGENT), (FaultType.OTHER, None), (None, None)],
)
def test_need_raises_for_a_needs_human_job(fault, cls) -> None:
    j = job(fault=fault, cls=cls)
    assert j.needs_human
    with pytest.raises(ValueError):
        scoring.need(j, MONDAY)
