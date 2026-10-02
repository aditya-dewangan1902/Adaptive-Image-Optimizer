"""Budget policy definitions and configurations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchBudget:
    """Explicit computational and candidate search budgets."""
    max_total_encodes: int = 50
    max_parallel_encodes_per_job: int = 4
    max_coarse_candidates: int = 24
    max_quality_searches: int = 24
    max_finalists: int = 4
    max_resolution_trials: int = 5
    max_wall_clock_ms: int = 90_000
    max_memory_mb_per_worker: int = 4096


def get_profile_budget(profile_name: str = "balanced") -> SearchBudget:
    """Return budget corresponding to requested profile."""
    p_lower = (profile_name or "").lower()
    if p_lower == "fast":
        return SearchBudget(
            max_total_encodes=30,
            max_coarse_candidates=14,
            max_quality_searches=14,
            max_finalists=3,
            max_wall_clock_ms=30_000,
        )
    elif p_lower in ("max_quality", "maximum"):
        return SearchBudget(
            max_total_encodes=70,
            max_coarse_candidates=28,
            max_quality_searches=32,
            max_finalists=6,
            max_wall_clock_ms=120_000,
        )
    # Default balanced
    return SearchBudget()
