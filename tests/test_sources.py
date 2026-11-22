import unittest
from urllib.parse import parse_qs, urlparse
from factnews.sources import datadawn_recent_register, usaspending_agencies, gdelt_articles

class SourceTests(unittest.TestCase):
    def test_datadawn_query_bounded_and_provenance(self):
        result = datadawn_recent_register(3, transport=lambda u: {"ok": True, "rows": []})
        params = parse_qs(urlparse(result["source_url"]).query)
        self.assertIn("LIMIT 3", params["sql"][0])
        self.assertEqual(params["_shape"], ["objects"])
        self.assertIn("retrieved_at", result)

    def test_spending_official_endpoint(self):
        result = usaspending_agencies(transport=lambda u: {"results": []})
        self.assertEqual(urlparse(result["source_url"]).netloc, "api.usaspending.gov")

    def test_gdelt_is_article_search(self):
        result = gdelt_articles("semiconductor investment", transport=lambda u: {"articles": []})
        self.assertEqual(parse_qs(urlparse(result["source_url"]).query)["mode"], ["artlist"])
        self.assertIn("source_url", result)

    def test_limits(self):
        with self.assertRaises(ValueError):
            datadawn_recent_register(1001)
        with self.assertRaises(ValueError):
            gdelt_articles("x", timespan="900d")
        with self.assertRaises(ValueError):
            gdelt_articles("x", limit=500)

if __name__ == "__main__":
    unittest.main()
