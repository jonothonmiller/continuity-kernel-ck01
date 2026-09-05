# Evidence provenance

## Controlled benchmark

`run_all.py`, `tests/test_benchmark.py`, `specification/gate_spec.json`, and all
files under `results` form a self-contained synthetic study accompanying the
manuscript. Results can be regenerated with one command and are
hashed in `results/sha256_manifest.json`.

## Earlier project evidence

The manuscript also reports earlier Continuity Kernel and CK-01 materials with
explicit evidence tiers:

- v1.0 source and validation were executed in a clean audit environment.
- v1.5 persistent-agent, key-governance, sensor, and certificate outputs were
  inspected, but several complete orchestration paths were not present in the
  closure archive.
- earlier v0.1 through v0.4 studies are historical regression evidence.

Those legacy sources are not silently copied into this package, and this
package does not convert output-audited evidence into externally reproduced
evidence.

## Naming and authorship

The canonical names are Continuity Kernel and CK-01. The manuscript author is
Jon Miller.

The software and benchmark package are licensed under Apache License 2.0.
