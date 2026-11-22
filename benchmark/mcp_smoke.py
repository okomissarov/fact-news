"""Run the local MCP smoke check with the optional mcp 1.x SDK."""
import asyncio
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
import sys
from time import perf_counter

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # The SDK starts with a small environment. Preserve network and CA configuration.
    env = {key: value for key, value in os.environ.items()
           if key.lower().endswith("_proxy") or key in {"SSL_CERT_FILE", "SSL_CERT_DIR"}}
    server = StdioServerParameters(command=sys.executable, args=["-m", "factnews.mcp_server"], env=env)
    report = {"tested_at": datetime.now(timezone.utc).isoformat(), "sdk_version": version("mcp"),
              "transport": "stdio", "calls": []}
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            report["protocol_version"] = (await session.initialize()).protocolVersion
            report["tools"] = sorted(tool.name for tool in (await session.list_tools()).tools)
            for name, args, field in [
                ("recent_federal_register", {"limit": 2}, "rows"),
                ("federal_agency_reference", {}, "results"),
                ("discover_news_articles", {"query": "semiconductor", "timespan": "7d", "limit": 2}, "articles"),
                ("recent_federal_register", {"limit": 101}, None),
            ]:
                start = perf_counter()
                result = await session.call_tool(name, args)
                entry = {"tool": name, "arguments": args, "elapsed_seconds": round(perf_counter() - start, 3)}
                if result.isError:
                    entry["error"] = result.content[0].text
                    entry["status"] = "rejected" if field is None and "limit must be" in entry["error"] else "blocked"
                else:
                    payload = result.structuredContent or json.loads(result.content[0].text)
                    entry.update(status="returned" if field else "unexpected_success",
                                 source_url=payload.get("source_url"), retrieved_at=payload.get("retrieved_at"),
                                 record_count=len(payload["data"][field]) if field else None)
                report["calls"].append(entry)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
