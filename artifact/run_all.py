from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
VARIANTS = (
    "ck01_revision_control",
    "no_temporal_gate",
    "no_provenance",
    "no_rollback",
    "shield_only",
    "adaptive_memory_only",
)
SCENARIOS = (
    "stationary",
    "abrupt_shift",
    "gradual_shift",
    "recurrent_shift",
    "temporary_shift",
    "single_source_spoof",
    "adaptive_single_source_attack",
    "correlated_source_attack",
    "registry_compromise",
)
SEEDS = tuple(range(10000, 10030))
HORIZON = 1400
MAX_STEP = 0.004
PERSISTENCE_CYCLES = 60
CONSOLIDATION_CYCLES = 80
REVIEW_CYCLES = 60
COOLDOWN_CYCLES = 30
SOURCE_NOISE_SD = 0.018
SPOOF_NOISE_SD = 0.006
INLIER_RADIUS = 0.18
MIN_INLIERS = 3
MEMORY_RETENTION = 0.98
MEMORY_INNOVATION = 0.02
ROLLBACK_MARGIN = 0.01
CHANGE_THRESHOLD = 0.08
CANDIDATE_RESET_THRESHOLD = 0.10
CANDIDATE_RETENTION = 0.95
CANDIDATE_INNOVATION = 0.05
IDENTITY_LOWER_BOUNDS = (-0.20, 0.05, 0.00)
IDENTITY_UPPER_BOUNDS = (0.75, 0.80, 0.75)
IDENTITY_TARGET_COEFFICIENTS = {
    "caution_intercept": 0.05,
    "caution_hazard": 0.85,
    "persistence_intercept": 0.20,
    "persistence_demand": 0.55,
    "persistence_resource_shortfall": 0.20,
    "exploration_intercept": 0.10,
    "exploration_resource_hazard_interaction": 0.70,
}
UTILITY_DISTANCE_SCALE = math.sqrt(3.0)
UTILITY_CAUTION_SHORTFALL_WEIGHT = 0.35
BASE_ENVIRONMENT_RANGES = ((0.14, 0.28), (0.65, 0.80), (0.38, 0.52))
SHIFTED_ENVIRONMENT_RANGES = ((0.62, 0.78), (0.46, 0.62), (0.58, 0.74))
BOOTSTRAP_REPLICATES = 10000
BOOTSTRAP_SEED = 20260904

PARAMETER_REGISTRY = {
    "MAX_STEP": "reference simulation",
    "PERSISTENCE_CYCLES": "synthetic calibration",
    "CONSOLIDATION_CYCLES": "reference simulation",
    "REVIEW_CYCLES": "reference simulation",
    "COOLDOWN_CYCLES": "reference simulation",
    "SOURCE_NOISE_SD": "reference simulation",
    "SPOOF_NOISE_SD": "reference simulation",
    "INLIER_RADIUS": "synthetic calibration",
    "MIN_INLIERS": "security policy",
    "MEMORY_RETENTION": "synthetic calibration",
    "MEMORY_INNOVATION": "synthetic calibration",
    "ROLLBACK_MARGIN": "synthetic calibration",
    "CHANGE_THRESHOLD": "synthetic calibration",
    "CANDIDATE_RESET_THRESHOLD": "synthetic calibration",
    "CANDIDATE_RETENTION": "synthetic calibration",
    "CANDIDATE_INNOVATION": "synthetic calibration",
    "IDENTITY_LOWER_BOUNDS": "reference simulation",
    "IDENTITY_UPPER_BOUNDS": "reference simulation",
    "IDENTITY_TARGET_COEFFICIENTS": "reference simulation",
    "UTILITY_DISTANCE_SCALE": "reference simulation",
    "UTILITY_CAUTION_SHORTFALL_WEIGHT": "reference simulation",
    "BASE_ENVIRONMENT_RANGES": "reference simulation",
    "SHIFTED_ENVIRONMENT_RANGES": "reference simulation",
    "BOOTSTRAP_REPLICATES": "reference simulation",
    "BOOTSTRAP_SEED": "reference simulation",
}


def identity_target(env: np.ndarray) -> np.ndarray:
    hazard, resource, demand = env
    c = IDENTITY_TARGET_COEFFICIENTS
    return np.array([
        np.clip(c["caution_intercept"] + c["caution_hazard"] * hazard, IDENTITY_LOWER_BOUNDS[0], IDENTITY_UPPER_BOUNDS[0]),
        np.clip(c["persistence_intercept"] + c["persistence_demand"] * demand + c["persistence_resource_shortfall"] * (1 - resource), IDENTITY_LOWER_BOUNDS[1], IDENTITY_UPPER_BOUNDS[1]),
        np.clip(c["exploration_intercept"] + c["exploration_resource_hazard_interaction"] * resource * (1 - hazard), IDENTITY_LOWER_BOUNDS[2], IDENTITY_UPPER_BOUNDS[2]),
    ])


def utility(identity: np.ndarray, true_env: np.ndarray) -> float:
    target = identity_target(true_env)
    distance = float(np.linalg.norm(identity - target))
    caution_shortfall = max(0.0, target[0] - identity[0]) * float(true_env[0])
    return float(1.0 - distance / UTILITY_DISTANCE_SCALE - UTILITY_CAUTION_SHORTFALL_WEIGHT * caution_shortfall)


@dataclass
class Scenario:
    name: str
    base: np.ndarray
    shifted: np.ndarray

    def state(self, t: int) -> tuple[np.ndarray, str]:
        if self.name == "stationary":
            return self.base.copy(), "stable"
        if self.name == "abrupt_shift":
            return (self.shifted.copy(), "persistent") if t >= 450 else (self.base.copy(), "stable")
        if self.name == "gradual_shift":
            if t < 350:
                return self.base.copy(), "stable"
            if t < 800:
                w = (t - 350) / 450
                return (1 - w) * self.base + w * self.shifted, "persistent"
            return self.shifted.copy(), "persistent"
        if self.name == "recurrent_shift":
            if 300 <= t < 650 or t >= 1000:
                return self.shifted.copy(), "persistent"
            return self.base.copy(), "stable"
        if self.name == "temporary_shift":
            return (self.shifted.copy(), "transient") if 450 <= t < 650 else (self.base.copy(), "stable")
        return self.base.copy(), "attack" if 450 <= t < 800 else "stable"

    def sources(self, t: int, true_env: np.ndarray, rng: np.random.Generator, identity: np.ndarray) -> list[np.ndarray]:
        values = [np.clip(true_env + rng.normal(0, SOURCE_NOISE_SD, 3), 0, 1) for _ in range(4)]
        if 450 <= t < 800:
            spoof = np.clip(self.shifted + rng.normal(0, SPOOF_NOISE_SD, 3), 0, 1)
            if self.name == "single_source_spoof":
                values[0] = spoof
            elif self.name == "adaptive_single_source_attack":
                corners = (np.array([0.95, 0.05, 0.95]), np.array([0.05, 0.95, 0.05]))
                spoof = max(corners, key=lambda x: float(np.linalg.norm(identity_target(x) - identity)))
                values[0] = np.clip(spoof + rng.normal(0, SPOOF_NOISE_SD, 3), 0, 1)
            elif self.name == "correlated_source_attack":
                values[0] = spoof
                values[1] = spoof.copy()
                values[2] = spoof.copy()
            elif self.name == "registry_compromise":
                values = [spoof.copy() for _ in range(4)]
        return values


class Agent:
    def __init__(self, variant: str, initial: np.ndarray):
        self.variant = variant
        self.initial = initial.copy()
        self.identity = initial.copy()
        self.memory_state = initial.copy()
        self.lo = np.array(IDENTITY_LOWER_BOUNDS)
        self.hi = np.array(IDENTITY_UPPER_BOUNDS)
        self.candidate = None
        self.streak = 0
        self.consolidation_left = 0
        self.review_left = 0
        self.cooldown_left = 0
        self.checkpoint = None
        self.rollback_target = None
        self.revised_utility = 0.0
        self.checkpoint_utility = 0.0
        self.updates = 0
        self.authorizations = 0
        self.rollbacks = 0
        self.constitutional_violations = 0

    def _consensus(self, sources: list[np.ndarray]) -> np.ndarray | None:
        if self.variant == "no_provenance":
            return sources[0].copy()
        matrix = np.vstack(sources)
        center = np.median(matrix, axis=0)
        inliers = np.linalg.norm(matrix - center, axis=1) <= INLIER_RADIUS
        if int(inliers.sum()) < MIN_INLIERS:
            return None
        return np.median(matrix[inliers], axis=0)

    def _bounded_update(self, target: np.ndarray) -> None:
        delta = target - self.identity
        norm = float(np.linalg.norm(delta))
        if norm > MAX_STEP:
            delta *= MAX_STEP / norm
        proposal = np.clip(self.identity + delta, self.lo, self.hi)
        if np.any(proposal < self.lo - 1e-12) or np.any(proposal > self.hi + 1e-12):
            self.constitutional_violations += 1
            return
        self.identity = proposal
        self.updates += 1

    def step(self, sources: list[np.ndarray], true_env: np.ndarray) -> None:
        observed = self._consensus(sources)
        if self.variant == "shield_only":
            return
        if observed is None:
            self.streak = 0
            return
        target = identity_target(observed)
        if self.variant == "adaptive_memory_only":
            self.memory_state = MEMORY_RETENTION * self.memory_state + MEMORY_INNOVATION * target
            return
        if self.variant == "no_temporal_gate":
            self._bounded_update(target)
            return

        # Rollback is a safety-critical identity transition too. It therefore
        # uses the same per-cycle bound as forward consolidation.
        if self.rollback_target is not None:
            self._bounded_update(self.rollback_target)
            if float(np.linalg.norm(self.identity - self.rollback_target)) <= 1e-12:
                self.rollback_target = None
                self.cooldown_left = COOLDOWN_CYCLES
            return

        if self.review_left > 0 and self.checkpoint is not None:
            self.revised_utility += utility(self.identity, true_env)
            self.checkpoint_utility += utility(self.checkpoint, true_env)
            self.review_left -= 1
            if self.review_left == 0:
                revised = self.revised_utility / REVIEW_CYCLES
                checkpoint = self.checkpoint_utility / REVIEW_CYCLES
                if self.variant != "no_rollback" and checkpoint > revised + ROLLBACK_MARGIN:
                    self.rollback_target = self.checkpoint.copy()
                    self.rollbacks += 1
                self.checkpoint = None
                if self.rollback_target is None:
                    self.cooldown_left = COOLDOWN_CYCLES
            return

        if self.consolidation_left > 0 and self.candidate is not None:
            self._bounded_update(self.candidate)
            self.consolidation_left -= 1
            if self.consolidation_left == 0:
                self.review_left = REVIEW_CYCLES
                self.revised_utility = 0.0
                self.checkpoint_utility = 0.0
            return

        if self.cooldown_left > 0:
            self.cooldown_left -= 1
            return

        gap = float(np.linalg.norm(target - self.identity))
        if gap <= CHANGE_THRESHOLD:
            self.candidate = None
            self.streak = 0
            return
        if self.candidate is None or float(np.linalg.norm(target - self.candidate)) > CANDIDATE_RESET_THRESHOLD:
            self.candidate = target.copy()
            self.streak = 1
        else:
            self.candidate = CANDIDATE_RETENTION * self.candidate + CANDIDATE_INNOVATION * target
            self.streak += 1
        if self.streak >= PERSISTENCE_CYCLES:
            self.checkpoint = self.identity.copy()
            self.consolidation_left = CONSOLIDATION_CYCLES
            self.authorizations += 1
            self.streak = 0

    def behavioral_identity(self) -> np.ndarray:
        return self.memory_state if self.variant == "adaptive_memory_only" else self.identity


def make_scenario(name: str, rng: np.random.Generator) -> Scenario:
    base = np.array([
        rng.uniform(*BASE_ENVIRONMENT_RANGES[0]),
        rng.uniform(*BASE_ENVIRONMENT_RANGES[1]),
        rng.uniform(*BASE_ENVIRONMENT_RANGES[2]),
    ])
    shifted = np.array([
        rng.uniform(*SHIFTED_ENVIRONMENT_RANGES[0]),
        rng.uniform(*SHIFTED_ENVIRONMENT_RANGES[1]),
        rng.uniform(*SHIFTED_ENVIRONMENT_RANGES[2]),
    ])
    return Scenario(name, base, shifted)


def run_one(seed: int, scenario_name: str, variant: str) -> dict:
    rng = np.random.default_rng(seed * 1009 + SCENARIOS.index(scenario_name) * 37)
    scenario = make_scenario(scenario_name, rng)
    initial = identity_target(scenario.base)
    agent = Agent(variant, initial)
    utilities = []
    max_attack_drift = 0.0
    max_step = 0.0
    previous = agent.behavioral_identity().copy()
    for t in range(HORIZON):
        true_env, label = scenario.state(t)
        sources = scenario.sources(t, true_env, rng, agent.behavioral_identity())
        agent.step(sources, true_env)
        current = agent.behavioral_identity().copy()
        max_step = max(max_step, float(np.linalg.norm(current - previous)))
        previous = current
        utilities.append(utility(current, true_env))
        if label in {"attack", "transient"}:
            max_attack_drift = max(max_attack_drift, float(np.linalg.norm(current - initial)))

    true_final, _ = scenario.state(HORIZON - 1)
    final_target = identity_target(true_final)
    final_error = float(np.linalg.norm(agent.behavioral_identity() - final_target))
    final_drift = float(np.linalg.norm(agent.behavioral_identity() - initial))
    in_budget_nonchange = scenario_name in {"stationary", "temporary_shift", "single_source_spoof", "adaptive_single_source_attack"}
    persistent_change = scenario_name in {"abrupt_shift", "gradual_shift", "recurrent_shift"}
    return {
        "seed": seed,
        "scenario": scenario_name,
        "variant": variant,
        "mean_utility": float(np.mean(utilities)),
        "final_error": final_error,
        "final_drift": final_drift,
        "max_attack_or_transient_drift": max_attack_drift,
        "false_positive_event": int(in_budget_nonchange and final_drift > 0.05),
        "false_negative_event": int(persistent_change and final_error > 0.10),
        "identity_updates": agent.updates,
        "authorizations": agent.authorizations,
        "rollbacks": agent.rollbacks,
        "constitutional_violations": agent.constitutional_violations,
        "max_observed_step": max_step,
    }


def summarize(rows: list[dict]) -> list[dict]:
    grouped = {}
    for row in rows:
        grouped.setdefault((row["variant"], row["scenario"]), []).append(row)
    out = []
    tcrit = 2.045229642
    for (variant, scenario), group in sorted(grouped.items()):
        result = {"variant": variant, "scenario": scenario, "n": len(group)}
        for metric in ("mean_utility", "final_error", "final_drift", "max_attack_or_transient_drift"):
            vals = [float(x[metric]) for x in group]
            mean = statistics.mean(vals)
            sd = statistics.stdev(vals)
            half = tcrit * sd / math.sqrt(len(vals))
            result[f"{metric}_mean"] = mean
            result[f"{metric}_sd"] = sd
            result[f"{metric}_ci_low"] = mean - half
            result[f"{metric}_ci_high"] = mean + half
        for metric in ("false_positive_event", "false_negative_event", "identity_updates", "authorizations", "rollbacks", "constitutional_violations"):
            result[f"{metric}_sum"] = int(sum(int(x[metric]) for x in group))
        result["max_observed_step"] = max(float(x["max_observed_step"]) for x in group)
        out.append(result)
    return out


def paired_comparisons(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    by_key = {(r["seed"], r["scenario"], r["variant"]): r for r in rows}
    out = []
    seed_rows = []
    tcrit = 2.045229642
    for variant in VARIANTS[1:]:
        for metric in ("mean_utility", "final_error", "max_attack_or_transient_drift"):
            seed_diffs = []
            for seed in SEEDS:
                scenario_diffs = []
                for scenario in SCENARIOS:
                    full = by_key[(seed, scenario, "ck01_revision_control")][metric]
                    other = by_key[(seed, scenario, variant)][metric]
                    scenario_diffs.append(float(full - other))
                aggregate = statistics.mean(scenario_diffs)
                seed_diffs.append(aggregate)
                seed_rows.append({"comparison": f"ck01_revision_control minus {variant}", "metric": metric, "seed": seed, "scenario_count": len(scenario_diffs), "mean_difference": aggregate})
            mean = statistics.mean(seed_diffs)
            sd = statistics.stdev(seed_diffs)
            half = tcrit * sd / math.sqrt(len(seed_diffs))
            rng = np.random.default_rng(BOOTSTRAP_SEED + VARIANTS.index(variant) * 101 + ("mean_utility", "final_error", "max_attack_or_transient_drift").index(metric))
            sample = np.asarray(seed_diffs)
            boot = np.mean(rng.choice(sample, size=(BOOTSTRAP_REPLICATES, len(sample)), replace=True), axis=1)
            out.append({
                "comparison": f"ck01_revision_control minus {variant}",
                "metric": metric,
                "n_independent_seeds": len(seed_diffs),
                "n_paired_observations": len(seed_diffs) * len(SCENARIOS),
                "mean_difference": mean,
                "ci_low": mean - half,
                "ci_high": mean + half,
                "ci_method": "two-sided 95 percent t interval over seed-level means",
                "cluster_bootstrap_low": float(np.quantile(boot, 0.025)),
                "cluster_bootstrap_high": float(np.quantile(boot, 0.975)),
                "cluster_bootstrap_replicates": BOOTSTRAP_REPLICATES,
            })
    return out, seed_rows


def security_boundary(rows: list[dict]) -> list[dict]:
    out = []
    for scenario in ("single_source_spoof", "adaptive_single_source_attack", "correlated_source_attack", "registry_compromise"):
        group = [r for r in rows if r["variant"] == "ck01_revision_control" and r["scenario"] == scenario]
        vals = [r["max_attack_or_transient_drift"] for r in group]
        out.append({
            "scenario": scenario,
            "fault_budget": "within f=1" if scenario in {"single_source_spoof", "adaptive_single_source_attack"} else "outside f=1",
            "n": len(vals),
            "mean_max_drift": statistics.mean(vals),
            "max_drift": max(vals),
            "false_positive_events": sum(r["false_positive_event"] for r in group),
        })
    return out


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def run() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [run_one(seed, scenario, variant) for seed in SEEDS for scenario in SCENARIOS for variant in VARIANTS]
    summary = summarize(rows)
    comparisons, seed_aggregates = paired_comparisons(rows)
    boundary = security_boundary(rows)
    write_json(RESULTS / "ablation_runs.json", rows)
    write_json(RESULTS / "ablation_summary.json", summary)
    write_json(RESULTS / "paired_comparisons.json", comparisons)
    write_json(RESULTS / "paired_seed_aggregates.json", seed_aggregates)
    write_json(RESULTS / "security_boundary.json", boundary)
    manifest = {
        "study": "Continuity Kernel CK-01 controlled ablation benchmark",
        "protocol_documented_before_final_execution": True,
        "implementation_revision_after_failed_bound_test": "Rollback changed from atomic checkpoint assignment to bounded incremental restoration; all runs were then regenerated.",
        "seeds": list(SEEDS),
        "scenarios": list(SCENARIOS),
        "variants": list(VARIANTS),
        "horizon_per_run": HORIZON,
        "total_runs": len(rows),
        "total_cycles": len(rows) * HORIZON,
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "parameter_types": PARAMETER_REGISTRY,
    }
    write_json(RESULTS / "experiment_manifest.json", manifest)
    write_json(RESULTS / "parameter_registry.json", {
        name: {"value": globals()[name], "type": parameter_type}
        for name, parameter_type in PARAMETER_REGISTRY.items()
    })
    return {"manifest": manifest, "summary": summary, "comparisons": comparisons, "boundary": boundary}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    output = run()
    hashes = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(RESULTS.glob("*.json")) if p.name != "sha256_manifest.json"}
    write_json(RESULTS / "sha256_manifest.json", hashes)
    if not args.quiet:
        print(json.dumps({"manifest": output["manifest"], "security_boundary": output["boundary"]}, indent=2))
