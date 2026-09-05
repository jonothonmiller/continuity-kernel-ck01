# Public release checklist

The manuscript and artifact must become public together. Do not submit the manuscript while its reproducibility claims point only to a private or local package.

- Confirm the author affiliation displayed on the manuscript and metadata.
- Confirm the funding and competing-interests declaration.
- Choose and add an explicit software/data license.
- Create a public GitHub repository named `continuity-kernel-ck01` or another canonical Continuity Kernel / CK-01 name.
- Add this package, including raw results, tests, the one-command runner, manifest, hashes, gate specification, and citation audit.
- Add the final DOCX and PDF under a `manuscript` directory.
- Run `python artifact/run_all.py` and `python -m unittest discover -s artifact/tests -v` from the repository root.
- Create a signed or annotated `v1.0.0` release and attach the complete release ZIP.
- Enable the repository in Zenodo, archive the GitHub release, and reserve or mint the DOI.
- Add the public GitHub URL and Zenodo DOI to the manuscript’s Data and Code Availability section and `CITATION.cff`.
- Rebuild the manuscript and verify all links before public submission.
