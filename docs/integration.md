# Integration and fact-checking contract

## Current scope
Three read-only, on-demand API connectors; no local corpus, database, scheduled job or deployed MCP server.

**DataDawn**: SQL queries to the hosted OpenRegs Datasette database. This first tool reads the `federal_register` table using an explicit LIMIT and returns its original document URL. DataDawn is a *replica/aggregator*, so confirm sensitive conclusions against the original Federal Register document.

**USAspending**: official top-tier agency reference endpoint. Agency totals must be qualified by reporting year and period. A contract obligation is not the same as an outlay. Future tools should support bounded, date-filtered spending searches with validated parameters.

**GDELT**: DOC API ArticleList. A list of news articles is *discovery evidence* and does **not** establish an event as fact. Recheck underlying source reports and relevant primary documents.

## Citation and trust rules
- Every response should preserve source URLs and retrieval timestamps.
- Differentiate event dates from publication and retrieval dates.
- Do not fabricate missing values; report null or error and why.
- Quote or paraphrase copyrighted reporting within applicable limits; do not bulk archive full articles.
- Keep query builders constrained; never pass free-form model-generated SQL to a hosted API without a separate read-only validator and limits.
- Never send secrets, private data or sensitive queries to public APIs without approval.

## ChatGPT limitation
Repository code persists in GitHub, but ChatGPT's GitHub integration does not automatically execute it. To expose these as native ChatGPT tools, deploy an HTTP MCP server, register it through supported custom integrations, or run the CLI locally. Custom MCP support and publishing depend on account and workspace capabilities.

## Next iterations
1. Live smoke tests against all endpoints from a network-enabled runner.
2. Add strict structured award-search endpoint with date filters.
3. Add policy-bill queries via DataDawn with primary record linking.
4. Score benchmark questions for correctness, coverage, latency and provenance.
5. Only then consider persistent snapshots and advanced graph retrieval.
