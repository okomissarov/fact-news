"""Bounded public API tools. Python standard library only; no data ingestion."""
from datetime import datetime, timezone
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "fact-news/0.1 (research; read-only)"

def fetch_json(url, timeout=20, transport=None):
    """Return evidence envelope with URL and retrieval time; fail loudly on HTTP/JSON errors."""
    if transport:
        payload = transport(url)
    else:
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(req, timeout=timeout) as response:
            payload = json.load(response)
    return {"source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(), "data": payload}

def datadawn_recent_register(limit=10, transport=None):
    """Recent official Federal Register records from DataDawn's replicated dataset."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be 1..100")
    sql = ("SELECT document_number,title,type,publication_date,agency_names,html_url "
           "FROM federal_register WHERE publication_date IS NOT NULL "
           "ORDER BY publication_date DESC LIMIT " + str(limit))
    url = "https://regs.datadawn.org/openregs.json?" + urlencode({"sql": sql, "_shape": "objects"})
    return fetch_json(url, transport=transport)

def usaspending_agencies(transport=None):
    """USAspending official top-tier agency reference dataset; amounts require fiscal-period context."""
    url = "https://api.usaspending.gov/api/v2/references/toptier_agencies/"
    return fetch_json(url, transport=transport)

def gdelt_articles(query="federal government", timespan="24h", limit=10, transport=None):
    """Article discovery only. A headline does not independently verify an event."""
    if not query or len(query) > 200:
        raise ValueError("query required, <=200 characters")
    if timespan not in ("24h", "48h", "72h", "7d"):
        raise ValueError("timespan must be 24h, 48h, 72h, or 7d")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be 1..50")
    params = {"query": query, "mode": "artlist", "format": "json", "maxrecords": limit,
              "timespan": timespan, "sort": "datedesc"}
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
    return fetch_json(url, transport=transport)

TOOLS = {
    "datadawn_recent_register": datadawn_recent_register,
    "usaspending_agencies": usaspending_agencies,
    "gdelt_articles": gdelt_articles,
}
