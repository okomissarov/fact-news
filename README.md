# Fact News

API-first, read-only factual research agent. Sources: DataDawn/OpenRegs (government records), USAspending (federal awards and spending), and GDELT (news discovery).

## Principles

- Query authoritative external datasets on demand; avoid bulk ingestion.
- Preserve source links, event timestamps, retrieval timestamps and query parameters.
- Separate recorded official actions from media reports and inferences.
- Distinguish budget authority, obligations and outlays.
- Benchmark source coverage, correctness, latency and provenance before expanding.

Run the live benchmark with `python -m factnews.benchmark --as-of YYYY-MM-DD`.
See the [benchmark guide](benchmark/README.md) for results and coverage.
