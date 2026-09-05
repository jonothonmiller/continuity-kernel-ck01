# Continuity Kernel CK-01 reproducibility package

This package contains the controlled comparison accompanying the Continuity Kernel / CK-01 manuscript.

Public repository: https://github.com/jonothonmiller/continuity-kernel-ck01. Permanent archive: https://doi.org/10.5281/zenodo.22314251.

## Run

Use Python 3.12 or later with NumPy installed.

```text
python run_all.py
python -m unittest discover -s tests -v
```

The runner executes 1,620 deterministic runs: 30 seeds, nine scenario families, six architecture variants, and 1,400 cycles per run. It writes raw run records, grouped summaries, paired comparisons, the security-boundary analysis, an environment manifest, and SHA-256 hashes under `results`.

## Scope

The benchmark is a controlled synthetic ablation. It tests whether individual CK-01 controls change measured behavior under a shared toy environment. It does not establish deployment safety, biological validity, or generalization to language-model agents.

## Variants

- `ck01_revision_control` is the CK-01 revision-control subset used in this benchmark. It includes independent-source consensus, temporal persistence, bounded updates, review, and rollback. It is not the complete CK-01 architecture.
- `no_temporal_gate` removes evidence persistence.
- `no_provenance` trusts one source while retaining the temporal and rollback controls.
- `no_rollback` retains provenance and temporal controls but never reverses a completed revision.
- `shield_only` freezes identity and applies no persistent self-revision.
- `adaptive_memory_only` uses an exponentially smoothed behavioral state without identity authorization.

## Threat boundary

The declared provenance budget is one compromised source among four independent sources. The fixed and adaptive single-source attacks are within that budget. The adaptive attacker observes the current behavioral identity and chooses between extreme reports to maximize distance from it. The correlated-source and registry-compromise scenarios deliberately exceed the budget and should be read as boundary tests rather than guaranteed cases.

For general membership size `n >= 3f + 1`, the quorum rule is `q = n - f`. This gives quorum intersection of at least `n - 2f >= f + 1`. In the benchmark, `n = 4`, `f = 1`, and `q = 3`.

## Negative result retained

The first controlled execution restored a checkpoint by direct assignment and
produced a maximum identity step of 0.32 despite a configured 0.004 bound on
forward updates. That failed the predeclared step-bound test. Rollback now uses
the same incremental bound as consolidation, and the full benchmark is rerun
from scratch. The manuscript records this failure because it materially changed
the mechanism.

## Authorship

Research manuscript author: Jon Miller, Independent Researcher.

Licensed under the Apache License, Version 2.0. See `LICENSE` and `NOTICE`.

## Citation verification

`RECENT_CITATION_VERIFICATION.md` records a final publisher-level check of every 2025–2026 citation used by the manuscript.

## License status

No license has been inferred. Add the author-selected license before public release so that readers know how the software and data may be reused.
