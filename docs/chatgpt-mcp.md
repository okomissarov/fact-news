# ChatGPT-first deployment path

## What works immediately
The GitHub connector can save and version code. ChatGPT web research can investigate public documents and sites. Neither operation makes Python source files automatically executable as ChatGPT tools.

## Shortest path to native agent tools
1. Validate the read-only functions with `python -m unittest discover -s tests -v` and `python -m factnews.cli --source all` on a network-enabled machine.
2. Wrap the functions with a small remote HTTP MCP server, exposing only named, parameter-validated tools (rather than unrestricted SQL or arbitrary URLs).
3. Host it on a runtime of your choice (local runtime with supported secure exposure, or AWS). Require appropriate authorization and request logging.
4. Register the MCP endpoint through the ChatGPT custom connector/plugin creation path if the user's workspace permits it.
5. Test the registered tools in a new ChatGPT conversation. Separately verify whether scheduled tasks can invoke these tools; this is not assumed.

## Alternative
Run a local agent (OpenCode with MCP tools) and store all evidence in versioned JSON; ChatGPT can review results shared via the repository or uploaded files.

## No secret keys
The v0.1 connectors only use public APIs. Do not expose a generic remote code executor or an arbitrary `query_sql` tool to LLMs.
