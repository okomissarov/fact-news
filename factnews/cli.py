"""CLI: python -m factnews.cli --source all [--query TEXT]."""
import argparse
import json
from time import perf_counter
from .sources import TOOLS

def main():
    parser = argparse.ArgumentParser(description="Read-only public API smoke tests")
    parser.add_argument("--source", choices=["all", *TOOLS.keys()], default="all")
    parser.add_argument("--query", default="federal government", help="GDELT article search")
    args = parser.parse_args()
    names = list(TOOLS) if args.source == "all" else [args.source]
    output = {}
    for name in names:
        start = perf_counter()
        try:
            kwargs = {"query": args.query} if name == "gdelt_articles" else {}
            result = TOOLS[name](**kwargs)
            payload = result["data"]
            if name == "datadawn_recent_register":
                count = len(payload.get("rows", []))
            elif name == "gdelt_articles":
                count = len(payload.get("articles", []))
            else:
                count = len(payload.get("results", [])) if isinstance(payload, dict) else None
            output[name] = {"ok": True, "source_url": result["source_url"],
                            "retrieved_at": result["retrieved_at"],
                            "elapsed_seconds": result["elapsed_seconds"], "record_count": count, "sample": str(payload)[:800]}
        except Exception as exc:
            output[name] = {"ok": False, "elapsed_seconds": round(perf_counter() - start, 3),
                            "error": str(exc)}
    print(json.dumps(output, indent=2))
    return 0 if all(v["ok"] for v in output.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
