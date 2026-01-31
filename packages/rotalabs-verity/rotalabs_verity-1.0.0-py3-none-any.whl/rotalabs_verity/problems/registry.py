"""
Problem registry for Verity benchmark.
"""

from typing import Optional

from rotalabs_verity.core import ProblemSpec

_REGISTRY: dict[str, ProblemSpec] = {}


def register(spec: ProblemSpec) -> None:
    """Register a problem specification."""
    _REGISTRY[spec.problem_id] = spec


def get_problem(problem_id: str) -> Optional[ProblemSpec]:
    """Get problem by ID."""
    return _REGISTRY.get(problem_id)


def list_problems() -> list[str]:
    """List all registered problem IDs."""
    return sorted(_REGISTRY.keys())


def list_by_category(category: str) -> list[str]:
    """List problems in a category."""
    return [pid for pid, spec in _REGISTRY.items()
            if spec.category == category]


def list_by_difficulty(difficulty: str) -> list[str]:
    """List problems by difficulty."""
    return [pid for pid, spec in _REGISTRY.items()
            if spec.difficulty == difficulty]
