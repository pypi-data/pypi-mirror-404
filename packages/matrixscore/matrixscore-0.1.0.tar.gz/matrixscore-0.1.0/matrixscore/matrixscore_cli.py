"""Agnostic CLI for the rating engine."""
import argparse
import json
from pathlib import Path

from matrixscore.core.schema import load_config
from matrixscore.core.scoring import (
    compute_coverage,
    predict_overall,
)


def _load_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def _resolve_portfolio(config):
    items_by_name = {item.name: item for item in config.items}
    if config.portfolio:
        portfolio = []
        missing = []
        for name in config.portfolio:
            item = items_by_name.get(name)
            if item:
                portfolio.append(item)
            else:
                missing.append(name)
        return portfolio, missing
    return list(config.items), []


def main():
    parser = argparse.ArgumentParser(description="Rating engine CLI")
    parser.add_argument("config", help="Path to a JSON config file")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    raw = _load_json(config_path)
    config = load_config(raw)
    portfolio, missing = _resolve_portfolio(config)
    issues = raw.get("issues")
    overall, components = predict_overall(
        portfolio,
        config.interaction_matrix,
        issues=issues,
        candidates=config.items,
        weights=config.weights,
    )
    coverage = compute_coverage(portfolio, config.interaction_matrix, issues=issues)

    print("Rating Engine Summary")
    if missing:
        print(f"Missing items from portfolio: {', '.join(missing)}")
    print(f"Portfolio size: {len(portfolio)}")
    print(f"Overall score: {overall}/100")
    print(f"Resilience score: {components['resilience']}/100")
    print(f"Coverage score: {components['coverage']}/100")
    print(f"Concentration score: {components['concentration']}/100")
    print(f"Best resilience delta: {components['best_resilience_delta']:.1f}")
    print(f"Best coverage headroom: {components['best_coverage_headroom']:.1f}")

    print("\nExposure Map")
    for row in coverage:
        issue = row["issue"]
        weak = row["weak"]
        resist = row["resist"]
        immune = row["immune"]
        neutral = row["neutral"]
        exposed = weak > (resist + immune)
        marker = "EXPOSED" if exposed else "OK"
        print(f"- {issue}: weak={weak}, resist={resist}, immune={immune}, neutral={neutral} [{marker}]")


if __name__ == "__main__":
    main()
