# Integration and fact-checking contract

## Current scope
Three read-only, on-demand API connectors; no local corpus, database, scheduled job or deployed MCP server.

**DataDawn**: SQL queries to the hosted OpenRegs Datasette database. The MCP tool reads the `federal_register` table using an explicit LIMIT and returns its original document URL. DataDawn is a *replica/aggregator*, so confirm sensitive conclusions against the original Federal Register document.

**USAspending**: official top-tier agency reference endpoint. Agency totals must be qualified by reporting year and period. A contract obligation is not the same as an outlay. The benchmark also uses agency budgetary resources and bounded spending searches for obligations, awards, trends, and recipient geography.

**GDELT**: DOC API ArticleList, with TimelineVol attempted by the benchmark. A list of news articles is *discovery evidence* and does **not** establish an event as fact. Recheck underlying source reports and relevant primary documents.

## Citation and trust rules
- Every response should preserve source URLs and retrieval timestamps.
- Differentiate event dates from publication and retrieval dates.
- Do not fabricate missing values; report null or error and why.
- Quote or paraphrase copyrighted reporting within applicable limits; do not bulk archive full articles.
- Keep query builders constrained; never pass free-form model-generated SQL to a hosted API without a separate read-only validator and limits.
- Never send secrets, private data or sensitive queries to public APIs without approval.

## ChatGPT limitation
Repository code persists in GitHub, but ChatGPT's GitHub integration does not automatically execute it. To expose these as native ChatGPT tools, deploy an HTTP MCP server, register it through supported custom integrations, or run the CLI locally. Custom MCP support and publishing depend on account and workspace capabilities.

## Validation

The [benchmark guide](../benchmark/README.md) links to observed live API and
local stdio results, including unsupported capabilities.
