# Engineering notes

## What changed

The original implementation put metadata access, comparison, occurrence counting, and mutation in a single script. The revised version separates pure comparison, incident memory, reporting, and command-line input. It adds missing-field and added-field checks alongside type comparisons, validates inputs, escapes report content, and protects existing baselines from accidental replacement.

Repeated checks no longer count as new incidents. Identity includes the field, change category, and before/after types. History is scoped by dataset and baseline fingerprint. Recovery removes an incident from the active set; a later return opens it again. A transition to a different type is a different incident.

High severity means review is required under this policy. It is not a measured impact score. A harmless type widening can still receive high severity.

## Evidence

The included demo contains 21 baseline fields and 20 current fields: two removals, two type changes, and one addition. The lifecycle contains five new incidents at the first drift, none on the next unchanged check, five resolutions at recovery, and five reopened incidents when drift returns. These numbers come from fixtures, not a production benchmark.

Run `python -m unittest discover -s tests -v` and `python scripts/demo.py` to reproduce the checks. Local validation used Python 3.13; other configured CI versions need an actual GitHub Actions run before being called verified.

## Tradeoffs

Standard-library-only execution keeps setup small. Exact native type strings are predictable but do not implement semantic compatibility. JSON is convenient for one process and unsuitable for concurrent writers. Independent output writes are not transactional. State grows with distinct baselines and change fingerprints; archival and retention policies are future work. Baseline files are flat schema contracts and do not bind themselves to a dataset identity: the operator must select the correct file.

## Discussing this work

Be ready to explain why repeated polls do not create new incidents, what a baseline reset means, why lineage cannot prove cause, and where local state stops being suitable. Do not claim a measured reduction in model failures or production validation without an experiment that establishes it.

The original archive contains no assignment instructions or contributor history. Keep appropriate course, team, or hackathon credit if applicable, and describe your own contribution accurately. Editing help should not be presented as work you implemented independently.
