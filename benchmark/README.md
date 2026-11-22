# Fact News evaluation benchmark

`questions.json` defines the 20 evaluation questions. Run the fixed queries
from the repository root with Python 3.11+ and network access:

```sh
python -m unittest discover -s tests -v
python -m factnews.cli --source all
python -m factnews.benchmark --as-of 2026-11-21
```

The as-of date controls government query windows. Results reflect source
coverage at retrieval time, and GDELT windows are relative to that time.

## Result labels and scores

- **Verified** means the answer follows from the official API for the stated scope or has been checked against primary records.
- **Partial** means the API returned a bounded search, proxy, or replica result with incomplete coverage or verification.
- **Blocked** means execution failed and no answer was scored.
- **Unsupported** means no reliable method was implemented for that question.

Each observed answer records correctness, provenance, coverage, and freshness
on the 0–2 rubric. A score of 0 indicates missing or unsupported evidence, 1
indicates partial evidence, and 2 indicates evidence meeting the rubric for
the stated scope. Provenance scores of 2 include record-level links and
retrieval timestamps. Freshness scores of 2 require established reporting lag
as well as dates. Latency is measured wall-clock time per question. Null scores
indicate there was no answer to evaluate. Read the scope and notes alongside
the scores, especially for empty keyword matches and media discovery.

See [the live results](results/2026-11-21-live.json) and
[the validation notes](results/2026-11-21-validation.md).
