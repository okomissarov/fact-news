# Local MCP execution

```sh
python -m pip install 'mcp>=1,<2'
python -m unittest discover -s tests -v
python -m factnews.cli --source all
python -m factnews.mcp_server
```

The final command starts an MCP server over **stdio**, suitable for a local MCP-capable agent (such as OpenCode) configured to launch this Python module in the repository working directory. It intentionally does not bind an HTTP port.

Tools:
- `recent_federal_register(limit)`
- `federal_agency_reference()`
- `discover_news_articles(query, timespan, limit)`

These are bounded examples rather than full research answers. The code does **not** implement an LLM planning loop. It does not run inside ChatGPT automatically simply because it is saved in GitHub.

To use this MCP service inside ChatGPT itself, a **supported remote custom MCP connection** must be configured and deployed separately. Do not expose a local stdio bridge as unauthenticated public HTTP.

Run a real stdio client smoke check from the repository root with
`python benchmark/mcp_smoke.py`. It initializes the session, lists tools, calls all
three providers, and checks the limit rejection path. The server uses the MCP
1.x FastMCP API. The live report records the tested version and per-call outcomes.
