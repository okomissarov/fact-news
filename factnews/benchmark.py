"""Run the repository's fixed benchmark cases against bounded public APIs."""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import platform
from time import perf_counter
from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from .sources import _gdelt, _openregs, fetch_json, gdelt_articles, require_rows

QUESTIONS = Path(__file__).resolve().parents[1] / "benchmark" / "questions.json"
SPENDING = "https://api.usaspending.gov/api/v2/"
FY2026 = ("2025-10-01", "2026-09-30")
REGISTER_FIELDS = "document_number, title, publication_date, type, html_url"
ACTION_FIELDS = "a.bill_id, l.title, a.action_date, a.action_text, l.url"
# One extra row exposes a result cutoff instead of silently implying completeness.
REGISTER = {
    "Q01": (
        "SELECT document_number, title, executive_order_number, publication_date, html_url "
        "FROM presidential_documents WHERE publication_date BETWEEN :start AND :end "
        "AND document_type = 'executive_order' ORDER BY publication_date DESC, document_number LIMIT 101"
    ),
    "Q02": (
        "SELECT a.id AS agency_id, a.name, COUNT(DISTINCT f.document_number) AS rule_count "
        "FROM federal_register f JOIN federal_register_agencies fa USING (document_number) "
        "JOIN agencies a ON a.id = fa.agency_id "
        "WHERE f.publication_date BETWEEN :start AND :end AND f.type = 'Rule' "
        "GROUP BY a.id, a.name ORDER BY rule_count DESC, a.name, a.id LIMIT 10"
    ),
    "Q03": (
        f"SELECT {REGISTER_FIELDS} FROM federal_register "
        "WHERE publication_date BETWEEN :start AND :end AND type = 'Proposed Rule' "
        "AND (title LIKE '%artificial intelligence%' OR abstract LIKE '%artificial intelligence%') "
        "ORDER BY publication_date DESC, document_number LIMIT 101"
    ),
    "Q04": (
        f"SELECT {REGISTER_FIELDS}, abstract FROM federal_register "
        "WHERE publication_date BETWEEN :start AND :end "
        "AND (title LIKE '%semiconductor%' OR abstract LIKE '%semiconductor%') "
        "ORDER BY publication_date DESC, document_number LIMIT 101"
    ),
    "Q05": (
        f"SELECT DISTINCT {ACTION_FIELDS} FROM legislation_actions a JOIN legislation l USING (bill_id) "
        "WHERE a.action_date BETWEEN :start AND :end AND l.bill_type IN ('hr', 's') "
        "AND (a.action_text LIKE 'Passed %' OR a.action_text LIKE 'Signed by President%' "
        "OR a.action_text LIKE 'Became Public Law%' OR a.action_text LIKE 'Presented to President%') "
        "ORDER BY a.action_date DESC, a.bill_id, a.action_text LIMIT 101"
    ),
    "Q06": (
        "SELECT congress, session, roll_call_number, date, question, result, yea_count, nay_count, source_url "
        "FROM roll_call_votes WHERE date BETWEEN :start AND :end AND chamber = 'senate' "
        "ORDER BY date DESC, roll_call_number DESC LIMIT 101"
    ),
    "Q07": (
        f"SELECT DISTINCT {ACTION_FIELDS} FROM legislation_actions a JOIN legislation l USING (bill_id) "
        "WHERE a.action_date BETWEEN :start AND :end "
        "AND (l.title LIKE '%defense procurement%' OR l.summary_text LIKE '%defense procurement%' "
        "OR l.title LIKE '%National Defense Authorization Act%' "
        "OR (l.policy_area = 'Armed Forces and National Security' "
        "AND (l.title LIKE '%procurement%' OR l.summary_text LIKE '%procurement%'))) "
        "ORDER BY a.action_date DESC, a.bill_id, a.action_text LIMIT 101"
    ),
    "Q08": (
        "SELECT document_number, title, signing_date, publication_date, html_url, abstract "
        "FROM presidential_documents WHERE publication_date BETWEEN :start AND :end "
        "AND (title LIKE '%amend%' OR title LIKE '%supersed%' OR title LIKE '%revok%' "
        "OR abstract LIKE '%executive order%is hereby amended%' "
        "OR abstract LIKE '%executive order%is hereby revoked%') "
        "ORDER BY publication_date DESC, document_number LIMIT 101"
    ),
}
UNSUPPORTED = {
    "Q18": "No event specified and no method to establish outlet independence or detect syndication.",
    "Q20": "No reliable matching and corroboration of news claims against official records.",
}
SCOPE = {
    "Q01": "Seven calendar dates through the as-of date, compared with the primary Federal Register search.",
    "Q02": "Top ten agency IDs by distinct Rule documents. Jointly attributed rules count once per listed agency.",
    "Q03": "Thirty days, literal phrase in title or abstract. Full text and AI synonyms are outside this search.",
    "Q04": "Thirty days, semiconductor keyword in title or abstract. Matches are candidates for supply-chain relevance.",
    "Q05": "Week to date (Monday start), H.R. and S. selected passage and enactment milestones. Other stages may be missing.",
    "Q06": "Seven calendar dates, comparing DataDawn with the primary Senate vote index.",
    "Q07": "Thirty days, defense-procurement phrase, defense authorization title, or procurement in the defense policy area. Candidate actions require relevance review.",
    "Q08": "Thirty-day candidate search for actions with amendment, revocation or supersession language. Legal relationships require primary-text review.",
    "Q09": "Top-tier agency reference rows returned by USAspending.",
    "Q10": "Agency total obligations in USD, FY2026, for DOE (top-tier code 089).",
    "Q11": "Top five awarding agencies by net prime-contract transaction obligations in USD, FY2026.",
    "Q12": "Thirty days, keyword search for artificial intelligence. Post-filter award start dates and show up to 20 candidates. Reporting lag and keyword coverage are unknown.",
    "Q13": "Keyword proxy for cybersecurity in prime-contract transactions. Compare complete FY2025 and FY2026 in USD.",
    "Q14": "Top five states by recipient location, FY2026, using the official Research and Development Product and Service Code category for prime contracts.",
    "Q15": "Seven-day GDELT index search. Up to 20 candidate reports.",
    "Q16": "Seven-day GDELT index search. Up to 20 candidate reports.",
    "Q17": "GDELT TimelineVol share of monitored coverage for the phrase critical minerals over 30 days.",
    "Q19": "GDELT article candidates over 24 hours. Significance and occurrence require independent review.",
}
PARTIAL_SPENDING = {"Q12", "Q13"}


def contract_filters(start, end, keyword=None):
    filters = {
        "time_period": [{"start_date": str(start), "end_date": str(end)}],
        "award_type_codes": ["A", "B", "C", "D"],
    }
    if keyword:
        filters["keywords"] = [keyword]
    return filters


def spending(path, body=None, key="results"):
    return require_rows(fetch_json(SPENDING + path, body=body), key)


def federal_register_search(start, end, doc_type, **options):
    params = {
        "conditions[type][]": doc_type,
        "conditions[publication_date][gte]": str(start),
        "conditions[publication_date][lte]": str(end),
        **options,
    }
    return fetch_json("https://www.federalregister.gov/api/v1/documents.json?" +
                      urlencode(params, doseq=True))


def senate_votes(year, start, end):
    congress = (year - 1789) // 2 + 1
    session = 1 if year % 2 else 2
    base = "https://www.senate.gov/legislative/LIS/"
    url = f"{base}roll_call_lists/vote_menu_{congress}_{session}.xml"
    began = perf_counter()
    try:
        with urlopen(url, timeout=20) as response:
            root = ElementTree.parse(response).getroot()
    except (OSError, ElementTree.ParseError) as exc:
        exc.source_url = url
        raise
    votes = root.find("votes")
    if votes is None:
        raise ValueError("Senate vote index is missing its votes element")
    rows = []
    for vote in votes.findall("vote"):
        stamp = datetime.strptime(f"{vote.findtext('vote_date').strip()}-{year}", "%d-%b-%Y").date()
        if start <= stamp <= end:
            number = int(vote.findtext("vote_number"))
            rows.append({
                "congress": congress, "session": session, "date": str(stamp), "roll_call_number": number,
                "question": vote.findtext("question").strip(), "title": vote.findtext("title"),
                "result": vote.findtext("result"), "yea_count": int(vote.findtext("vote_tally/yeas")),
                "nay_count": int(vote.findtext("vote_tally/nays")),
                "source_url": f"{base}roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{number:05d}.htm",
            })
    return {"source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(perf_counter() - began, 3), "data": rows}


def register_case(case, end):
    days = {"Q01": 7, "Q05": end.weekday() + 1, "Q06": 7}.get(case, 30)
    start = end - timedelta(days=days - 1)
    result = _openregs(REGISTER[case], start=str(start), end=str(end))
    rows = result["data"]["rows"]
    evidence = [result]
    if case == "Q01":
        primary = federal_register_search(
            start, end, "PRESDOCU", per_page=100,
            **{"conditions[presidential_document_type][]": "executive_order"},
        )
        evidence.append(primary)
        official = primary["data"]
        expected = {row["document_number"] for row in official.get("results", [])}
        observed = {row["document_number"] for row in rows}
        if official["count"] != len(expected) or expected != observed:
            return rows, evidence, "partial", "Primary search and replica coverage differ."
        return rows, evidence, "verified", "Record IDs and count agree with the primary search."
    if case == "Q02":
        primary = federal_register_search(start, end, "RULE", per_page=1000,
                                          **{"fields[]": ["document_number", "agencies"]})
        records = primary["data"].get("results", [])
        counts = Counter(agency_id for record in records
                         for agency_id in {agency.get("id") for agency in record["agencies"]}
                         if agency_id is not None)
        expected_counts = sorted(counts.values(), reverse=True)[:10]
        primary["data"] = {"count": primary["data"]["count"],
                           "records_read": len(records), "agency_counts": dict(counts)}
        evidence.append(primary)
        if (primary["data"]["count"] == len(records)
                and expected_counts == [row["rule_count"] for row in rows]
                and all(counts[row["agency_id"]] == row["rule_count"] for row in rows)):
            return rows, evidence, "verified", "Top counts and listed agency IDs agree with primary records."
        return rows, evidence, "partial", "Replica ranking and bounded primary comparison did not fully agree."
    if case in {"Q03", "Q04", "Q08"} and rows:
        # Verify a bounded sample of indexed documents against the publisher.
        fields = ["document_number", "title", "publication_date", "html_url", "abstract"]
        primary = [
            fetch_json(f"https://www.federalregister.gov/api/v1/documents/{row['document_number']}.json?"
                       + urlencode({"fields[]": fields}, doseq=True))
            for row in rows[:3]
        ]
        matches = sum(all(check["data"][key] == row[key] for key in
                          ("document_number", "title", "publication_date"))
                      for row, check in zip(rows, primary))
        note = (f"Primary metadata matched {matches} of {len(primary)} sampled documents. "
                "Search scope and topical or legal relevance remain partial.")
        return rows[:100], evidence + primary, "partial", note
    if case == "Q06":
        primary = [senate_votes(year, start, end) for year in range(start.year, end.year + 1)]
        official = [row for page in primary for row in page["data"]]
        replica_ids = {(row["congress"], row["session"], row["roll_call_number"]) for row in rows}
        primary_ids = {(row["congress"], row["session"], row["roll_call_number"]) for row in official}
        note = f"Primary Senate index returned {len(official)} votes. DataDawn returned {len(rows)}."
        if replica_ids != primary_ids:
            note += " The replica differs from the official index. The answer uses the official index."
        return official, evidence + primary, "verified", note
    if result["data"].get("truncated") or len(rows) > 100:
        return rows[:100], evidence, "partial", "Bounded result reached its row cutoff."
    return rows, evidence, "partial", "Replica query executed. Underlying records need independent checks."


def spending_case(case, end):
    if case == "Q09":
        result = spending("references/toptier_agencies/")
        rows = result["data"]["results"]
        answer = [{key: row[key] for key in ("agency_id", "toptier_code", "agency_name")} for row in rows]
    elif case == "Q10":
        result = spending("agency/089/budgetary_resources/", key="agency_data_by_year")
        row, = [row for row in result["data"]["agency_data_by_year"] if row["fiscal_year"] == 2026]
        period = max(row["agency_obligation_by_period"], key=lambda item: item["period"])
        amount = row["agency_total_obligated"]
        if period["period"] != 12 or amount is None or period["obligated"] != amount:
            return row, [result], "partial", "Full-year total unavailable or inconsistent with period 12."
        answer = {"toptier_code": "089", "fiscal_year": 2026, "reporting_period": 12,
                  "obligations_usd": amount}
    elif case == "Q11":
        result = spending("search/spending_by_category/awarding_agency/", {
            "filters": contract_filters(*FY2026), "spending_level": "transactions", "limit": 5, "page": 1,
        })
        answer = result["data"]["results"]
    elif case == "Q12":
        start = end - timedelta(days=29)
        result = spending("search/spending_by_award/", {
            "filters": contract_filters(start, end, "artificial intelligence"),
            "spending_level": "awards", "limit": 20, "page": 1, "sort": "Start Date", "order": "desc",
            "fields": ["Award ID", "Start Date", "Recipient Name", "Description", "Awarding Agency"],
        })
        answer = [row for row in result["data"]["results"]
                  if str(start) <= (row["Start Date"] or "") <= str(end)]
    elif case == "Q13":
        result = spending("search/spending_over_time/", {
            "filters": contract_filters("2024-10-01", FY2026[1], "cybersecurity"),
            "spending_level": "transactions", "group": "fiscal_year",
        })
        totals = {str(row["time_period"]["fiscal_year"]): row["aggregated_amount"]
                  for row in result["data"]["results"]}
        answer = {"obligations_usd_by_fy": totals}
        if "2025" in totals and "2026" in totals:
            answer["change_usd"] = round(totals["2026"] - totals["2025"], 2)
    else:
        filters = contract_filters(*FY2026)
        filters["psc_codes"] = {"require": [["Research and Development"]]}
        result = spending("search/spending_by_geography/", {
            "filters": filters, "spending_level": "transactions",
            "scope": "recipient_location", "geo_layer": "state",
        })
        rows = result["data"]["results"]
        answer = sorted(rows, key=lambda row: row["aggregated_amount"], reverse=True)[:5]
    status = "partial" if case in PARTIAL_SPENDING else "verified"
    note = ("Official API returned records for the stated proxy or bounded search." if status == "partial"
            else "Answer derived directly from the official USAspending response for the stated scope.")
    return answer, [result], status, note


def news_case(case):
    query, timespan = {
        "Q15": ('semiconductor investment', "7d"),
        "Q16": ('"defense procurement" contract', "7d"),
        "Q17": ('"critical minerals"', "30d"),
        "Q19": ('"energy infrastructure"', "24h"),
    }[case]
    if case == "Q17":
        result = _gdelt(query, "timelinevol", timespan)
        series, = result["data"]["timeline"]
        points = series["data"]
        # Compare equal-sized chronological halves without assuming a daily bucket.
        points = sorted(points, key=lambda point: point["date"])
        n = len(points) // 2
        if not n:
            return points, [result], "partial", "Too few observations for a comparison."
        answer = {"early_mean_share_percent": sum(p["value"] for p in points[:n]) / n,
                  "late_mean_share_percent": sum(p["value"] for p in points[-n:]) / n}
        return answer, [result], "partial", "Index share comparison. Provider coverage and lag were not independently checked."
    result = gdelt_articles(query, timespan, limit=20)
    return result["data"]["articles"], [result], "partial", "Discovery only. Article relevance and claims need review."


def run_case(case, end):
    scores = dict.fromkeys(("correctness", "provenance", "coverage", "freshness"))
    if case in UNSUPPORTED:
        return {"status": "unsupported", "note": UNSUPPORTED[case], "scores": scores,
                "elapsed_seconds": None}
    start = perf_counter()
    try:
        if case in REGISTER:
            answer, evidence, status, note = register_case(case, end)
        elif "Q09" <= case <= "Q14":
            answer, evidence, status, note = spending_case(case, end)
        else:
            answer, evidence, status, note = news_case(case)
        verified = status == "verified"
        record_urls = isinstance(answer, list) and any(
            row.get("html_url") or row.get("source_url") or row.get("url") for row in answer
        )
        scores.update(correctness=2 if verified else int(bool(answer)), provenance=2 if record_urls else 1,
                      coverage=2 if verified else int(bool(answer)), freshness=1)
        for item in evidence:
            payload = item.get("data")
            if isinstance(payload, dict):
                for field in ("rows", "results", "articles", "agency_data_by_year"):
                    if field in payload:
                        rows = payload.pop(field)
                        payload[field + "_count"] = len(rows)
                        if rows and rows != answer and case != "Q09":
                            payload[field + "_sample"] = rows[:2]
        result = {"status": status, "note": note, "answer": answer, "evidence": evidence}
    except (OSError, ValueError, KeyError, TypeError, ElementTree.ParseError) as exc:
        result = {"status": "blocked", "note": str(exc), "source_url": getattr(exc, "source_url", None)}
        if getattr(exc, "request_body", None) is not None:
            result["request_body"] = exc.request_body
        if hasattr(exc, "code"):
            result["http_status"] = exc.code
    return {"scope": SCOPE[case], "scores": scores,
            "elapsed_seconds": round(perf_counter() - start, 3), **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat,
                        default=datetime.now(ZoneInfo("America/New_York")).date())
    args = parser.parse_args()
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "as_of": str(args.as_of),
        "environment": {"python": platform.python_version(), "system": platform.system()},
        "note": "The as-of date controls government query windows. GDELT windows are relative to retrieval.",
        "questions": [],
    }
    for question in json.loads(QUESTIONS.read_text())["questions"]:
        case = question["id"]
        report["questions"].append({
            "id": case, "source": question["source"], "question": question["question"],
            **run_case(case, args.as_of),
        })
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
