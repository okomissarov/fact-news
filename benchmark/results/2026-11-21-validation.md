# Live validation on November 21, 2026

Linux x86_64, Python 3.12.14, with outbound network access through the
workspace proxy. Machine-readable timestamps use UTC. Government benchmark
cutoffs use November 21 in America/New_York.

| Check | Observed outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | Four baseline tests passed. All six tests passed after changes. |
| `python -m compileall -q factnews tests benchmark/mcp_smoke.py` | Passed. |
| `python -m factnews.cli --source all` | DataDawn and USAspending returned JSON without credentials. GDELT returned HTTP 503, so the command exited 1. |
| `python -m factnews.benchmark --as-of 2026-11-21` | 18 cases attempted. Seven verified, seven partial, four blocked. Two unsupported. |
| `python benchmark/mcp_smoke.py` | Stdio initialization and tool discovery passed with SDK 1.30.0. DataDawn and USAspending returned records. The invalid limit was rejected and the GDELT upstream error propagated. |

## Benchmark evidence

- **Q01 and Q02.** The primary Federal Register search agreed with zero executive orders in the seven-date window and with the top agency rule counts. FAA and the Transportation Department each had 46. The ranking counts jointly attributed rules once per agency ID.
- **Q03, Q04, Q05, Q07 and Q08.** Federal Register metadata matched the three sampled regulatory records. Legislative milestones and procurement candidates came from the replica. The presidential amendment candidate search returned no hits, so amendment and supersession relationships remain unresolved.
- **Q06.** The official Senate index listed 17 votes between November 15 and 21. DataDawn returned zero for the same window. The answer uses the official index and links to each vote.
- **Q09, Q10, Q11 and Q14.** USAspending returned 111 agency reference records. Its fiscal year 2026 Department of Energy total was $77,494,806,227.17 in obligations through period 12. The Department of Defense led FY2026 prime-contract transaction obligations by awarding agency. California led FY2026 obligations classified as Research and Development by recipient location.
- **Q12 and Q13.** The bounded AI keyword award search yielded no candidates in its window. The cybersecurity year-over-year change describes a keyword-defined subset. Reporting lag and keyword coverage are unresolved.
- **Q15, Q16, Q17 and Q19.** GDELT ArticleList and TimelineVol attempts returned HTTP 503. A direct probe returned an upstream connection timeout from the proxy. Live response schema and authentication behavior remain unverified.
- **Q18 and Q20.** Outlet independence, article clustering, and corroboration of geopolitical claims against official records remain unsupported.

The unpinned MCP install selected 2.3.0 and failed on the FastMCP import.
The tested installation uses `mcp>=1,<2`. The stdio client preserved the
workspace proxy and CA configuration when launching the server. Hosted MCP
and ChatGPT registration were outside this validation run.

[Per-question scores and request evidence](2026-11-21-live.json) ·
[CLI smoke results](2026-11-21-cli.json) ·
[Local MCP results](2026-11-21-mcp.json)
