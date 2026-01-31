import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from matrixscore.core.scoring import (
    compute_coverage,
    resilience_score,
    concentration_score,
    coverage_effectiveness,
    predict_overall,
)


class TestScoring(unittest.TestCase):
    def test_resilience_and_concentration(self):
        matrix = {
            "a": {"a": 2.0, "b": 0.5},
            "b": {"a": 0.5, "b": 2.0},
        }
        items = [
            {"name": "i1", "issues": ["a"], "capabilities": ["a"]},
            {"name": "i2", "issues": ["b"], "capabilities": ["b"]},
        ]
        coverage = compute_coverage(items, matrix)
        self.assertEqual(resilience_score(coverage), 100)
        self.assertEqual(concentration_score(coverage), 100)

    def test_exposure_penalty(self):
        matrix = {
            "a": {"a": 2.0, "b": 2.0},
            "b": {"a": 1.0, "b": 1.0},
        }
        items = [
            {"name": "i1", "issues": ["a"], "capabilities": ["a"]},
            {"name": "i2", "issues": ["b"], "capabilities": ["b"]},
        ]
        coverage = compute_coverage(items, matrix)
        # issue "a" should be exposed with overlap
        self.assertLess(resilience_score(coverage), 100)

    def test_coverage_effectiveness(self):
        matrix = {
            "a": {"a": 2.0, "b": 1.0},
            "b": {"a": 0.5, "b": 2.0},
        }
        items = [
            {"name": "i1", "issues": ["a"], "capabilities": ["a"]},
            {"name": "i2", "issues": ["a"], "capabilities": ["b"]},
        ]
        coverage = compute_coverage(items, matrix)
        score = coverage_effectiveness(items, coverage, matrix)
        self.assertGreaterEqual(score, 0)

    def test_predict_overall(self):
        matrix = {
            "a": {"a": 2.0, "b": 1.0},
            "b": {"a": 0.5, "b": 2.0},
        }
        items = [
            {"name": "i1", "issues": ["a"], "capabilities": ["a"], "category": "x"},
            {"name": "i2", "issues": ["b"], "capabilities": ["b"], "category": "y"},
        ]
        overall, components = predict_overall(items, matrix, candidates=items)
        self.assertIn("coverage_map", components)
        self.assertIsInstance(overall, float)


if __name__ == "__main__":
    unittest.main()
