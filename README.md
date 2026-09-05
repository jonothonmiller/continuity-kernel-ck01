# Continuity Kernel / CK-01 v1.0.0

This public release accompanies Jon Miller's manuscript, *Continuity Kernel: A Cognitive Architecture and AI Safety Framework for Persistent Artificial Identity*.

## Contents

- `manuscript/` contains the editable DOCX and shareable PDF.
- `artifact/` contains the one-command benchmark runner, exact configurations and seeds, raw results, grouped summaries, machine-readable gate specification, tests, manifests, and hashes.
- `legacy_evidence/` preserves the v1.0 source bundle and v1.5 closure package assessed by the manuscript.
- `SHA256SUMS.txt` authenticates every file in this release candidate.

## Reproduce the benchmark

From the repository root, with Python 3.12 or later and NumPy installed:

```text
python artifact/run_all.py
python -m unittest discover -s artifact/tests -v
```

The runner executes 1,620 deterministic runs and rewrites the machine-readable outputs under `artifact/results/`.

## Availability

The public repository is https://github.com/jonothonmiller/continuity-kernel-ck01. The permanent archive is https://doi.org/10.5281/zenodo.22314251. The manuscript is distributed under CC BY 4.0; the software and benchmark materials are licensed under Apache License 2.0.
