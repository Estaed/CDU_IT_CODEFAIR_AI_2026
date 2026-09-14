"""Minimum-cost assignment against brute force, plus edge cases and deterministic ties."""

from itertools import permutations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core.assignment import min_cost_assignment


def brute_force(costs: list[list[float]]) -> tuple[float, list[int]]:
    """Minimal total and the lexicographically smallest column sequence reaching it."""
    n, m = len(costs), len(costs[0])
    best: tuple[float, list[int]] | None = None
    for cols in permutations(range(m), n):  # lexicographic order
        total = sum(costs[r][c] for r, c in enumerate(cols))
        if best is None or total < best[0] - 1e-9:
            best = (total, list(cols))
    assert best is not None
    return best


@st.composite
def matrices(draw, value) -> list[list[float]]:
    n = draw(st.integers(1, 6))
    m = draw(st.integers(n, 7))
    return [[draw(value) for _ in range(m)] for _ in range(n)]


@settings(max_examples=200, deadline=None)
@given(matrices(st.floats(0, 1000, allow_nan=False)))
def test_total_matches_brute_force(costs: list[list[float]]) -> None:
    result = min_cost_assignment(costs)
    total, _ = brute_force(costs)
    assert len(result) == len(costs)
    assert len(set(result)) == len(result)
    assert sum(costs[r][c] for r, c in enumerate(result)) == pytest.approx(total, abs=1e-6)


@settings(max_examples=200, deadline=None)
@given(matrices(st.integers(0, 6).map(float)))
def test_ties_resolve_like_the_first_optimal_permutation(costs: list[list[float]]) -> None:
    # Small integer costs: many exact ties and no rounding, so the tie-break is checkable.
    assert min_cost_assignment(costs) == brute_force(costs)[1]


def test_empty_input() -> None:
    assert min_cost_assignment([]) == []


def test_square_matrix() -> None:
    costs = [[4.0, 1.0, 3.0], [2.0, 0.0, 5.0], [3.0, 2.0, 2.0]]
    result = min_cost_assignment(costs)
    assert sorted(result) == [0, 1, 2]
    assert sum(costs[r][c] for r, c in enumerate(result)) == 5.0


def test_ties_take_the_lowest_column_index() -> None:
    assert min_cost_assignment([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]) == [0, 1]
    assert min_cost_assignment([[0.0] * 4 for _ in range(3)]) == [0, 1, 2]


def test_more_rows_than_columns_is_an_error() -> None:
    with pytest.raises(ValueError, match="more rows"):
        min_cost_assignment([[1.0], [2.0]])
