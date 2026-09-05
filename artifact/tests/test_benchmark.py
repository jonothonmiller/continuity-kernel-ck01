from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run_all


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads((ROOT / "results" / "ablation_runs.json").read_text(encoding="utf-8"))

    def values(self, variant, scenario, metric):
        return [r[metric] for r in self.rows if r["variant"] == variant and r["scenario"] == scenario]

    def test_constitutional_bounds_hold(self):
        self.assertEqual(sum(r["constitutional_violations"] for r in self.rows), 0)

    def test_revision_control_resists_single_source_spoof(self):
        self.assertLess(max(self.values("ck01_revision_control", "single_source_spoof", "max_attack_or_transient_drift")), 0.02)

    def test_revision_control_resists_adaptive_single_source_attack(self):
        self.assertLess(max(self.values("ck01_revision_control", "adaptive_single_source_attack", "max_attack_or_transient_drift")), 0.02)

    def test_provenance_ablation_is_more_vulnerable(self):
        full = sum(self.values("ck01_revision_control", "single_source_spoof", "max_attack_or_transient_drift"))
        ablated = sum(self.values("no_provenance", "single_source_spoof", "max_attack_or_transient_drift"))
        self.assertGreater(ablated, full + 0.5)

    def test_provenance_ablation_is_vulnerable_to_adaptive_source(self):
        full = sum(self.values("ck01_revision_control", "adaptive_single_source_attack", "max_attack_or_transient_drift"))
        ablated = sum(self.values("no_provenance", "adaptive_single_source_attack", "max_attack_or_transient_drift"))
        self.assertGreater(ablated, full + 0.5)

    def test_revision_control_adapts_better_than_frozen_identity(self):
        full = sum(self.values("ck01_revision_control", "abrupt_shift", "final_error"))
        frozen = sum(self.values("shield_only", "abrupt_shift", "final_error"))
        self.assertLess(full, frozen)

    def test_reported_step_bound(self):
        bounded = [r["max_observed_step"] for r in self.rows if r["variant"] not in {"adaptive_memory_only"}]
        self.assertLessEqual(max(bounded), 0.0040000001)

    def test_parameter_registry_covers_configured_model_constants(self):
        expected = {
            "MAX_STEP", "PERSISTENCE_CYCLES", "CONSOLIDATION_CYCLES", "REVIEW_CYCLES", "COOLDOWN_CYCLES",
            "SOURCE_NOISE_SD", "SPOOF_NOISE_SD", "INLIER_RADIUS", "MIN_INLIERS", "MEMORY_RETENTION",
            "MEMORY_INNOVATION", "ROLLBACK_MARGIN", "CHANGE_THRESHOLD", "CANDIDATE_RESET_THRESHOLD",
            "CANDIDATE_RETENTION", "CANDIDATE_INNOVATION", "IDENTITY_LOWER_BOUNDS", "IDENTITY_UPPER_BOUNDS",
            "IDENTITY_TARGET_COEFFICIENTS", "UTILITY_DISTANCE_SCALE", "UTILITY_CAUTION_SHORTFALL_WEIGHT",
            "BASE_ENVIRONMENT_RANGES", "SHIFTED_ENVIRONMENT_RANGES", "BOOTSTRAP_REPLICATES", "BOOTSTRAP_SEED",
        }
        self.assertEqual(set(run_all.PARAMETER_REGISTRY), expected)

    def test_paired_inference_uses_independent_seed_units(self):
        comparisons = json.loads((ROOT / "results" / "paired_comparisons.json").read_text(encoding="utf-8"))
        self.assertTrue(all(row["n_independent_seeds"] == 30 for row in comparisons))
        self.assertTrue(all(row["n_paired_observations"] == 270 for row in comparisons))
        self.assertTrue(all(row["cluster_bootstrap_replicates"] == 10000 for row in comparisons))


if __name__ == "__main__":
    unittest.main()
