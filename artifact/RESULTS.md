# Controlled benchmark results

The final benchmark executed 1,620 runs and 2,268,000 cycles across 30
deterministic seeds, nine scenarios, and six architecture variants. All nine
package tests pass.

## Main findings

- The CK-01 revision-control subset had zero identity movement under fixed and state-adaptive
  one-source attacks, both within the declared `f = 1` budget.
- Removing provenance produced mean maximum movement of 0.320 under both
  one-source attacks. The revised identity later returned near baseline, so
  final drift alone would conceal the attack effect.
- The CK-01 revision-control subset had substantially lower final target error than a frozen shield
  across abrupt, gradual, and recurrent shifts. Adaptive memory tracked the
  target faster than the CK-01 revision-control subset.
- Across 270 paired observations nested within 30 independent seeds, mean utility differences for the CK-01 revision-control subset were -0.0082 versus no temporal gate, +0.0053 versus no provenance,
  +0.0155 versus no rollback, +0.0485 versus shield only, and -0.0123 versus
  adaptive memory. Primary 95% t intervals are computed over 30 seed-level means; a 10,000-replicate cluster bootstrap over seeds is included as a sensitivity check in `results/paired_comparisons.json`.
- A 200-cycle temporary regime caused mean maximum movement of 0.320 in the revision-control subset before it returned near baseline. The configured 60-cycle persistence
  threshold therefore does not reject disturbances of that duration.
- Three correlated sources and registry compromise, both outside the declared
  budget, caused mean maximum movement of 0.320 before later recovery.
- No run recorded a constitutional violation. After the rollback correction,
  the maximum one-cycle identity displacement was 0.00400000000000008.

## Negative result and correction

The first controlled execution failed the step-bound test because rollback
restored a checkpoint atomically, producing a one-cycle displacement of 0.32.
Rollback was changed to use the same incremental bound as forward
consolidation, and all runs were regenerated. This is a mechanism correction,
not a deleted outlier.

## Interpretation

The benchmark supports a scoped safety tradeoff. Provenance aggregation and
rollback reduce specified attack effects, and persistent revision avoids the
rigidity of a frozen shield. Temporal authorization is not a free performance
gain: faster ungated and adaptive-memory baselines achieve higher utility in
this synthetic generator. The results do not establish deployment safety,
psychological validity, or superiority over production cognitive architectures.
