"""Bounded public API tools. Python standard library only; no data ingestion."""
from datetime import datetime, timezone
import json
from time import perf_counter
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

USER_AGENT = "fact-news/0.1 (research; read-only)"

def fetch_json(url, timeout=20, transport=None, *, body=None):
    """Return evidence envelope with URL and retrieval time; fail loudly on HTTP/JSON errors."""
    start = perf_counter()
    if transport:
        payload = transport(url)
    else:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            with urlopen(req, timeout=timeout) as response:
                payload = json.load(response)
        except (URLError, TimeoutError, ValueError) as exc:
            exc.source_url = url
            exc.request_body = body
            raise
    result = {"source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
              "elapsed_seconds": round(perf_counter() - start, 3), "data": payload}
    if body is not None:
        result["request_body"] = body
    return result

def require_rows(result, key):
    payload = result["data"]
    if (not isinstance(payload, dict) or payload.get("ok") is False
            or not isinstance(payload.get(key), list)
            or any(not isinstance(row, dict) for row in payload[key])):
        error = ValueError(f"Expected a JSON object containing a {key} list of records")
        error.source_url = result["source_url"]
        error.request_body = result.get("request_body")
        raise error
    return result


def _openregs(sql, transport=None, **params):
    url = "https://regs.datadawn.org/openregs.json?" + urlencode(
        {"sql": sql, "_shape": "objects", **params}
    )
    return require_rows(fetch_json(url, transport=transport), "rows")


def datadawn_recent_register(limit=10, transport=None):
    """Recent official Federal Register records from DataDawn's replicated dataset."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be 1..100")
    sql = ("SELECT document_number,title,type,publication_date,agency_names,html_url "
           "FROM federal_register WHERE publication_date <= :end "
           "ORDER BY publication_date DESC, document_number LIMIT " + str(limit))
    return _openregs(sql, transport=transport,
                     end=datetime.now(ZoneInfo("America/New_York")).date().isoformat())

def usaspending_agencies(transport=None):
    """USAspending official top-tier agency reference dataset; amounts require fiscal-period context."""
    url = "https://api.usaspending.gov/api/v2/references/toptier_agencies/"
    return require_rows(fetch_json(url, transport=transport), "results")

def gdelt_articles(query="federal government", timespan="24h", limit=10, transport=None):
    """Article discovery only. A headline does not independently verify an event."""
    if not query.strip() or len(query) > 200:
        raise ValueError("query required, <=200 characters")
    if timespan not in ("24h", "48h", "72h", "7d"):
        raise ValueError("timespan must be 24h, 48h, 72h, or 7d")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be 1..50")
    return _gdelt(query, "artlist", timespan, transport,
                  maxrecords=limit, sort="datedesc")


def _gdelt(query, mode, timespan, transport=None, **options):
    params = {"query": query, "mode": mode, "format": "json", "timespan": timespan, **options}
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
    return require_rows(fetch_json(url, transport=transport),
                        "articles" if mode == "artlist" else "timeline")

TOOLS = {
    "datadawn_recent_register": datadawn_recent_register,
    "usaspending_agencies": usaspending_agencies,
    "gdelt_articles": gdelt_articles,
}
