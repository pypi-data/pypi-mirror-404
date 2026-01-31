"""Agnostic schema for rating engine inputs."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


InteractionMatrix = Dict[str, Dict[str, float]]


@dataclass
class Item:
    """A single candidate with issue and capability tags."""
    name: str
    issues: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    strength: Optional[float] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RatingConfig:
    """Top-level config for a rating run."""
    interaction_matrix: InteractionMatrix
    items: List[Item]
    portfolio: List[str] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    categories: Dict[str, List[str]] = field(default_factory=dict)


def _coerce_item(raw: Dict[str, Any]) -> Item:
    name = str(raw.get("name", "")).strip()
    issues = list(raw.get("issues") or [])
    capabilities = list(raw.get("capabilities") or [])
    strength = raw.get("strength")
    category = raw.get("category")
    metadata = dict(raw.get("metadata") or {})
    return Item(
        name=name,
        issues=issues,
        capabilities=capabilities,
        strength=strength,
        category=category,
        metadata=metadata,
    )


def validate_matrix(matrix: InteractionMatrix) -> None:
    if not isinstance(matrix, dict) or not matrix:
        raise ValueError("interaction_matrix must be a non-empty dict")
    for cap, issues in matrix.items():
        if not isinstance(issues, dict) or not issues:
            raise ValueError(f"interaction_matrix[{cap}] must be a non-empty dict")
        for issue, mult in issues.items():
            if not isinstance(mult, (int, float)):
                raise ValueError(f"interaction_matrix[{cap}][{issue}] must be a number")


def load_config(data: Dict[str, Any]) -> RatingConfig:
    if not isinstance(data, dict):
        raise ValueError("config must be a dict")
    matrix = data.get("interaction_matrix") or {}
    validate_matrix(matrix)
    items_raw = data.get("items") or []
    if not isinstance(items_raw, list) or not items_raw:
        raise ValueError("items must be a non-empty list")
    items = [_coerce_item(it) for it in items_raw]
    portfolio = list(data.get("portfolio") or [])
    weights = dict(data.get("weights") or {})
    categories = dict(data.get("categories") or {})
    return RatingConfig(
        interaction_matrix=matrix,
        items=items,
        portfolio=portfolio,
        weights=weights,
        categories=categories,
    )
