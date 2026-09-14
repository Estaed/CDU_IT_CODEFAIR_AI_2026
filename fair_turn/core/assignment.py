"""Minimum-cost assignment (Hungarian / Kuhn-Munkres), pure Python.

Used where distance decides which crew goes to a job that the ranking has already chosen;
it never chooses which jobs are served.
"""

from collections.abc import Sequence

_TIE_EPS = 1e-9


def _hungarian(costs: Sequence[Sequence[float]], rows: list[int], cols: list[int]) -> list[int]:
    """Optimal assignment of ``rows`` to distinct ``cols`` (indices into ``costs``); returns the
    column for each row in order. Shortest augmenting paths with potentials, O(n^2 m)."""
    n, m = len(rows), len(cols)
    inf = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    owner = [0] * (m + 1)  # owner[j]: 1-based row matched to column j, 0 when free
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        owner[0] = i
        j0 = 0
        minv = [inf] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = owner[j0]
            row = costs[rows[i0 - 1]]
            delta, j1 = inf, 0
            for j in range(1, m + 1):
                if used[j]:
                    continue
                cur = row[cols[j - 1]] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j], way[j] = cur, j0
                if minv[j] < delta:
                    delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[owner[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if owner[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            owner[j0] = owner[j1]
            j0 = j1
    result = [0] * n
    for j in range(1, m + 1):
        if owner[j]:
            result[owner[j] - 1] = cols[j - 1]
    return result


def _total(costs: Sequence[Sequence[float]], rows: list[int], chosen: list[int]) -> float:
    return sum(costs[r][c] for r, c in zip(rows, chosen, strict=True))


def min_cost_assignment(costs: Sequence[Sequence[float]]) -> list[int]:
    """For each row, the column assigned to it: every row a distinct column, total cost minimal.

    Rows must not outnumber columns. Among equal-cost optima the result is the
    lexicographically smallest column sequence (row 0 takes the lowest column it can while
    staying optimal, then row 1, and so on), so ties resolve the same way every time.
    """
    n = len(costs)
    if n == 0:
        return []
    m = len(costs[0])
    if any(len(row) != m for row in costs):
        raise ValueError("every row needs the same number of columns")
    if n > m:
        raise ValueError("more rows than columns")

    rows = list(range(n))
    free_cols = list(range(m))
    best = _hungarian(costs, rows, free_cols)
    target = _total(costs, rows, best)
    fixed: list[int] = []
    for position in range(n):
        rest = rows[position + 1 :]
        current = best[position]
        for col in (c for c in free_cols if c < current):
            others = [c for c in free_cols if c != col]
            tail = _hungarian(costs, rest, others) if rest else []
            total = sum(costs[r][c] for r, c in zip(rows[:position], fixed, strict=True))
            total += costs[position][col] + _total(costs, rest, tail)
            if total <= target + _TIE_EPS * max(1.0, abs(target)):
                current = col
                best = [*fixed, col, *tail]
                break
        fixed.append(current)
        free_cols.remove(current)
    return fixed
