"""Map helpers shared by the workspace page and the clustered map (PRD 3.1).

The interactive map itself is ``cluster_map`` (MapLibre GL in a v2 component). What stays
here is plain Python: resolving a picked community to its jobs, and the inline Altair NT
outline drawn when the basemap cannot load.
"""

from fair_turn.app import state
from fair_turn.app.components.map import nt_map


def choice_for(community_id: str | None, by_community: dict[str, list]) -> tuple | None:
    """Resolve a map pick to ``(community id, sorted job ids)``.

    A pick naming a community the current filters no longer show is stale and yields no
    choice, rather than an error."""
    members = by_community.get(community_id) if community_id is not None else None
    if not members:
        return None
    return (community_id, sorted(job.job_id for job in members))


def _fallback_map(points: list[dict], crews: list[dict] | None = None):
    communities = {
        point["community_id"]: {
            "region": str(point["region"]),
            "lon": str(point["lon"]),
            "lat": str(point["lat"]),
        }
        for point in points
    }
    open_counts = {point["community_id"]: int(point["open_jobs"]) for point in points}
    return nt_map(communities, open_counts, state.ALL_REGIONS, crews)
