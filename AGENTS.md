# Fact News — repository instructions for Codex and coding agents

## Mission and scope
Build a **facts-first, read-only research assistant** that helps a user ask questions in ChatGPT about government actions, federal spending, economic and political developments, and global news. **Query established providers on demand**; do not create a conventional news aggregator, duplicate provider data warehouses, or ingest news content into a local knowledge graph unless a measured need justifies it.

The initial three integrations:
1. **DataDawn/OpenRegs** — structured US government records, including regulations and legislative activity where offered by its hosted API.
2. **USAspending** — official federal awards, agency, obligations, and spending data.
3. **GDELT** — international news/event discovery. GDELT-indexed articles are reports and signals, not automatically independently confirmed facts.

Long-term sources may include Federal Register, Congress.gov, Treasury, FRED, SEC EDGAR, Reuters/Bloomberg/AP, and other institutional records, but **do not expand integrations until the three-source benchmark is measured**.

## Architecture principles
- **ChatGPT-first:** the desired user interface is ChatGPT calling supported, narrowly scoped MCP tools, not a new custom frontend. A local MCP server is a useful development and testing step; ChatGPT access requires a supported *remote* MCP connection, secure hosting, and actual configuration. Do not assume a GitHub repo or a local stdio server is automatically callable in ChatGPT.
- **No ingestion by default:** query hosted structured APIs, keep only small reproducible query/result/evidence snapshots when necessary for benchmarking, caching, change tracking, or auditability.
- **Modular, simple, low cost:** Python standard library for API adapters where practical; add dependencies only for a concrete reason. Prefer minimal local development, then optional AWS portability (Lambda/ECS/S3), without mandatory always-on databases.
- **Read-only and least privilege:** never expose arbitrary SQL, arbitrary URLs, code execution, secrets, or administrative operations as agent tools. Validate user-controlled query parameters, dates, and limits. Do not make persistent provider-side changes.
- **Reliable provenance:** preserve origin URL, raw record/document identifier, source name, retrieval timestamp, source publication date and event date when available, and the exact query parameters. Differentiate originals from aggregates and secondary sources.
- **Structured facts first:** calculate counts, amounts and changes from authoritative structured responses using deterministic code. LLMs can explain and relate results, but must not fabricate data, dates, citations or confidence.
- **Epistemic distinctions:** identify official acts, claims made by officials, media-reported developments, calculations/inferences, forecasts, and unverified allegations separately. A source's existence does not validate all its assertions. Track corrections when possible.
- **Fiscal semantics:** budget requests, authority, appropriations, obligations, awards and actual outlays are different concepts. Report fiscal year, agency/program, scope and measurement units when comparing.
- **Source licensing:** do not scrape or redistribute paywalled articles or bulk-store copyrighted reporting. Respect rate limits, API terms, and robots/permissions.

## Current implementation
- `factnews/sources.py` contains three bounded connector functions and a provenance envelope.
- `factnews/cli.py` runs read-only connector smoke checks.
- `factnews/mcp_server.py` exposes example tools using FastMCP over local stdio; this does **not** deploy a remotely accessible ChatGPT MCP integration.
- `tests/test_sources.py` has mocked parameter/URL tests.
- `benchmark/questions.json` defines **20 benchmark questions**, not 20 validated answers.
- `docs/integration.md`, `docs/local-mcp.md`, and `docs/chatgpt-mcp.md` document current constraints.

Treat existing code as **prototype only**: verify real DataDawn table names/columns, endpoint and payload shapes, GDELT response behavior, network access, timeouts, and MCP SDK compatibility. A mocked unit test passing does not demonstrate live API success. Avoid implying benchmark completion without source-grounded answers.

## Immediate tasks (in order)
1. Review current feature branch and reproduce tests **from a real checkout**, reporting commands, environment and failures.
2. Execute **live** bounded API requests to each of DataDawn, USAspending and GDELT. Fix real endpoint, SQL schema, response shape, timeout and handling issues. If network is unavailable, explicitly mark live checks blocked, never passed.
3. Test local stdio MCP server via a real MCP client, including tool discovery and tool invocations. Add automated contract tests where appropriate.
4. Extend narrowly scoped queries to support the benchmark. Avoid generic free-form SQL tool calls. Use primary-source linking to verify consequential government actions and distinguish GDELT discovery from verification.
5. Execute and score all **20** benchmark questions. Record each exact query, observed answer/evidence or blocker, source URLs, correctness, provenance, coverage, freshness and elapsed latency; mark partial/unsupported honestly.
6. Only after validation, investigate a securely hosted remote MCP service, and whether the user's ChatGPT account supports registering and using it. A deployment must not be publicly unauthenticated.
7. Keep this work in `feat/api-first-benchmark` and update pull request #1; do **not** merge into `main` unless explicitly requested.

## Testing and reporting
- `python -m unittest discover -s tests -v`
- `python -m factnews.cli --source all`
- For local MCP: `python -m pip install mcp`, then use a proper MCP client to test `python -m factnews.mcp_server`.
- Prefer deterministic tests with mocked HTTP payloads plus separate optional live integration tests.
- Never label code or a proposed prompt as an executed test. Report whether a result is **unit-tested**, **live-API-tested**, **MCP-tested**, or **not verified**.
- Do not introduce fabricated example outputs into benchmark results.
- Commit reproducible test reports to `benchmark/results/` with a timestamp and environment notes.

## Developer collaboration
The user values factual precision, independent source corroboration, clear evidence, minimal custom infrastructure, and rapid practical prototyping. The user intends to use ChatGPT as the research/analysis interface and Codex as a repository implementation/testing assistant. Explain limitations clearly; avoid overbuilding or changing architecture without evidence.
