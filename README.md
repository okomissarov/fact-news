# Fact News

API-first, read-only factual research agent. Sources: DataDawn/OpenRegs (government records), USAspending (federal awards and spending), and GDELT (news discovery).

## Principles

- Query authoritative external datasets on demand; avoid bulk ingestion.
- Preserve source links, event timestamps, retrieval timestamps and query parameters.
- Separate recorded official actions from media reports and inferences.
- Distinguish budget authority, obligations and outlays.
- Benchmark source coverage, correctness, latency and provenance before expanding.

Initial scaffold only; no integrations or automated jobs are running yet.
