"""Agnostic scoring and projection helpers."""
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple, Any

from .schema import InteractionMatrix, Item


def _item_name(item: Any) -> str:
    if isinstance(item, Item):
        return item.name
    return str(item.get("name", ""))


def _item_issues(item: Any) -> List[str]:
    if isinstance(item, Item):
        return list(item.issues or [])
    return list(item.get("issues") or item.get("types") or [])


def _item_capabilities(item: Any) -> List[str]:
    if isinstance(item, Item):
        return list(item.capabilities or [])
    return list(item.get("capabilities") or [])


def _item_strength(item: Any) -> Optional[float]:
    if isinstance(item, Item):
        return item.strength
    return item.get("strength")


def _item_category(item: Any) -> Optional[str]:
    if isinstance(item, Item):
        return item.category
    return item.get("category")


def _issue_list(matrix: InteractionMatrix, issues: Optional[Iterable[str]]) -> List[str]:
    if issues:
        return list(issues)
    seen = set()
    for row in matrix.values():
        for issue in row.keys():
            seen.add(issue)
    return sorted(seen)


def _weight(weights: Optional[Dict[str, float]], key: str, default: float) -> float:
    if not weights:
        return default
    val = weights.get(key)
    return default if val is None else float(val)


def interaction_multiplier(issue: str, item_issues: Iterable[str], matrix: InteractionMatrix) -> float:
    base = matrix.get(issue, {})
    mult = 1.0
    for tag in item_issues:
        mult *= base.get(tag, 1.0)
    return mult


def compute_coverage(items: List[Any], matrix: InteractionMatrix, issues: Optional[Iterable[str]] = None):
    issue_list = _issue_list(matrix, issues)
    coverage = []
    for issue in issue_list:
        weak = resist = immune = neutral = 0.0
        for item in items:
            item_tags = _item_issues(item)
            if not item_tags:
                continue
            mult = interaction_multiplier(issue, item_tags, matrix)
            if mult == 0:
                immune += 1.0
            elif mult > 1:
                weak += 1.0
            elif mult < 1:
                resist += 1.0
            else:
                neutral += 1.0
        size = sum(1 for it in items if _item_issues(it))
        coverage.append(
            {
                "issue": issue,
                "weak": weak,
                "resist": resist,
                "immune": immune,
                "neutral": neutral,
                "size": size,
            }
        )
    return coverage


def resilience_score(coverage, weights: Optional[Dict[str, float]] = None) -> int:
    overlap_w = _weight(weights, "overlap", 8.0)
    gap_w = _weight(weights, "exposure_gap", 8.0)
    overlap = sum(
        max(0, c["weak"] - 1) for c in coverage if c["weak"] > (c["resist"] + c["immune"])
    )
    exposure_gap = sum(
        max(0, c["weak"] - (c["resist"] + c["immune"])) for c in coverage
    )
    score = 100 - (gap_w * exposure_gap) - (overlap_w * overlap)
    return max(0, min(100, int(score)))


def resilience_delta(
    base_coverage,
    sim_coverage,
    weights: Optional[Dict[str, float]] = None,
    bonus_weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, int, int]:
    base_score = resilience_score(base_coverage, weights=weights)
    sim_score = resilience_score(sim_coverage, weights=weights)
    base_cov_map = {c["issue"]: c for c in base_coverage}
    immune_gain = 0
    resist_gain = 0
    for sc in sim_coverage:
        bc = base_cov_map.get(sc["issue"], {"weak": 0, "resist": 0, "immune": 0})
        was_exposed = bc["weak"] > (bc["resist"] + bc["immune"])
        if not was_exposed:
            continue
        if sc["immune"] > bc["immune"]:
            immune_gain += 1
        if sc["resist"] > bc["resist"]:
            resist_gain += 1
    immune_bonus = _weight(bonus_weights, "immune_gain", 6.0)
    resist_bonus = _weight(bonus_weights, "resist_gain", 3.0)
    bonus = (immune_gain * immune_bonus) + (resist_gain * resist_bonus)
    return (sim_score - base_score) + bonus, sim_score, base_score


def concentration_score(coverage, weights: Optional[Dict[str, float]] = None) -> int:
    if not coverage:
        return 100
    overlap_w = _weight(weights, "concentration_overlap", 10.0)
    exposed_w = _weight(weights, "concentration_exposed", 5.0)
    max_weak = max(c["weak"] for c in coverage)
    overlap = max(0, max_weak - 1)
    exposed = sum(1 for c in coverage if c["weak"] > (c["resist"] + c["immune"]))
    score = 100 - (overlap * overlap_w) - (exposed * exposed_w)
    return max(0, min(100, int(score)))


def coverage_effectiveness(
    items: List[Any],
    coverage,
    matrix: InteractionMatrix,
    issues: Optional[Iterable[str]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> int:
    issue_list = _issue_list(matrix, issues)
    capabilities = set()
    for item in items:
        for cap in _item_capabilities(item):
            capabilities.add(cap)
    if not capabilities:
        return 0
    exposed_issues = [c["issue"] for c in coverage if c["weak"] > (c["resist"] + c["immune"])]
    penalties = 0.0
    neutral_pen = _weight(weights, "neutral_penalty", 6.0)
    immune_pen = _weight(weights, "immune_penalty", 14.0)
    for issue in exposed_issues:
        best = 1.0
        for cap in capabilities:
            best = max(best, matrix.get(cap, {}).get(issue, 1.0))
        if best >= 2.0:
            continue
        if best >= 1.0:
            penalties += neutral_pen
        else:
            penalties += immune_pen
    min_breadth = _weight(weights, "breadth_min", 2.0)
    breadth_pen = _weight(weights, "breadth_penalty", 3.0)
    breadth_penalty = max(0, min_breadth - len(capabilities)) * breadth_pen
    base = max(0, min(100, 100 - penalties - breadth_penalty))
    if penalties == 0:
        neutral, strong = coverage_projection(capabilities, matrix, issue_list)
        neutral_ratio = neutral / max(1, len(issue_list))
        strong_ratio = len(strong) / max(1, len(issue_list))
        bonus_cap = _weight(weights, "breadth_bonus_cap", 10.0)
        bonus_neutral = _weight(weights, "breadth_bonus_neutral", 5.0)
        bonus_strong = _weight(weights, "breadth_bonus_strong", 6.0)
        bonus = min(bonus_cap, (bonus_neutral * neutral_ratio) + (bonus_strong * strong_ratio))
        base = min(100, base + bonus)
    return int(base)


def coverage_projection(capabilities: Iterable[str], matrix: InteractionMatrix, issues: Iterable[str]):
    if not capabilities:
        return 0, []
    strong_issues = []
    neutral_or_better = 0
    for issue in issues:
        best = 1.0
        for cap in capabilities:
            best = max(best, matrix.get(cap, {}).get(issue, 1.0))
        if best >= 1.0:
            neutral_or_better += 1
        if best >= 2.0:
            strong_issues.append(issue)
    return neutral_or_better, strong_issues


def overall_score(
    best_resilience_delta: float,
    best_coverage_headroom: float,
    concentration: float,
    weights: Optional[Dict[str, float]] = None,
    resilience: Optional[float] = None,
) -> float:
    delta_penalty = _weight(weights, "delta_penalty", 0.10) * (
        best_resilience_delta + best_coverage_headroom
    )
    shared_penalty = _weight(weights, "shared_penalty", 0.03) * max(0, 100 - concentration)
    overall = 100 - delta_penalty - shared_penalty
    if resilience is not None:
        floor = _weight(weights, "resilience_floor", 85.0)
        floor_pen = _weight(weights, "resilience_floor_penalty", 0.4)
        if resilience < floor:
            overall -= (floor - resilience) * floor_pen
    return max(0.0, min(100.0, overall))


def coverage_totals(coverage):
    return {
        "weak": sum(c["weak"] for c in coverage),
        "resist": sum(c["resist"] for c in coverage),
        "immune": sum(c["immune"] for c in coverage),
    }


def compute_best_resilience_gain(
    portfolio: List[Any],
    candidates: List[Any],
    matrix: InteractionMatrix,
    issues: Optional[Iterable[str]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    if not candidates:
        return 0.0
    issue_list = _issue_list(matrix, issues)
    base_cov = compute_coverage(portfolio, matrix, issue_list)
    base_score = resilience_score(base_cov, weights=weights)
    current_names = {_item_name(i) for i in portfolio}
    best = 0.0
    for cand in candidates:
        if _item_name(cand) in current_names:
            continue
        sim_cov = compute_coverage(portfolio + [cand], matrix, issue_list)
        delta = resilience_score(sim_cov, weights=weights) - base_score
        if delta > best:
            best = delta
    return min(100.0, best)


def compute_best_coverage_gain(
    portfolio: List[Any],
    candidates: List[Any],
    matrix: InteractionMatrix,
    issues: Optional[Iterable[str]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    if not candidates:
        return 0.0
    issue_list = _issue_list(matrix, issues)
    base_cov = compute_coverage(portfolio, matrix, issue_list)
    base_score = coverage_effectiveness(portfolio, base_cov, matrix, issue_list, weights=weights)
    base_caps = set()
    for item in portfolio:
        base_caps.update(_item_capabilities(item))
    current_names = {_item_name(i) for i in portfolio}
    best = 0.0
    for cand in candidates:
        if _item_name(cand) in current_names:
            continue
        sim_portfolio = portfolio + [cand]
        sim_cov = compute_coverage(sim_portfolio, matrix, issue_list)
        sim_score = coverage_effectiveness(sim_portfolio, sim_cov, matrix, issue_list, weights=weights)
        gain = sim_score - base_score
        neutral, strong = coverage_projection(base_caps | set(_item_capabilities(cand)), matrix, issue_list)
        closed_exposure = 0.0
        base_cov_map = {c["issue"]: c for c in base_cov}
        for sc in sim_cov:
            bc = base_cov_map.get(sc["issue"])
            if not bc:
                continue
            base_exposed = bc["weak"] > (bc["resist"] + bc["immune"])
            sim_exposed = sc["weak"] > (sc["resist"] + sc["immune"])
            if base_exposed and not sim_exposed:
                closed_exposure += 1.0
            elif base_exposed and sc["weak"] < bc["weak"]:
                closed_exposure += 0.5
        new_caps = set(_item_capabilities(cand)) - base_caps
        gain_factor = (1 + 1.0 * closed_exposure) * (1 + 0.25 * len(new_caps))
        strength = _item_strength(cand)
        strength = 0.0 if strength is None else float(strength)
        strength_factor = max(0.8, min(1.3, 0.7 + strength / 450.0))
        strong_factor = 1.0 + 0.05 * min(6, len(strong))
        coverage_penalty = 0.85 if neutral >= (len(issue_list) - 1) and len(strong) < 5 else 1.0
        ranked = gain * gain_factor * strength_factor * strong_factor * coverage_penalty
        if ranked > best:
            best = ranked
    return min(100.0, best)


def predict_overall(
    portfolio: List[Any],
    matrix: InteractionMatrix,
    issues: Optional[Iterable[str]] = None,
    candidates: Optional[List[Any]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, Any]]:
    issue_list = _issue_list(matrix, issues)
    coverage = compute_coverage(portfolio, matrix, issue_list)
    resilience = resilience_score(coverage, weights=weights)
    concentration = concentration_score(coverage, weights=weights)
    coverage_score = coverage_effectiveness(portfolio, coverage, matrix, issue_list, weights=weights)
    best_resilience = compute_best_resilience_gain(portfolio, candidates or [], matrix, issue_list, weights=weights)
    best_coverage = compute_best_coverage_gain(portfolio, candidates or [], matrix, issue_list, weights=weights)
    if resilience == 100:
        best_resilience = 0
    if coverage_score == 100:
        best_coverage = 0
    overall = overall_score(
        best_resilience,
        best_coverage,
        concentration,
        weights=weights,
        resilience=resilience,
    )
    role_counts = defaultdict(int)
    for item in portfolio:
        category = _item_category(item) or "uncategorized"
        role_counts[category] += 1
    role_penalty = 0.0
    for cnt in role_counts.values():
        if cnt >= 3:
            role_penalty += _weight(weights, "category_penalty", 0.25) * (cnt - 2)
    if role_penalty:
        overall = max(0, min(100, overall - role_penalty))
    overall = round(overall, 1)
    components = {
        "resilience": resilience,
        "coverage": coverage_score,
        "concentration": concentration,
        "best_resilience_delta": best_resilience,
        "best_coverage_headroom": best_coverage,
        "coverage_map": coverage,
        "category_penalty": role_penalty,
    }
    return overall, components
