from datetime import date
import unittest
from unittest.mock import patch

from factnews.benchmark import register_case


class BenchmarkTests(unittest.TestCase):
    @patch("factnews.benchmark.federal_register_search")
    @patch("factnews.benchmark._openregs")
    def test_agency_count_handles_duplicate_and_unmapped_attributions(self, replica, primary):
        ranking = [{"agency_id": 159, "name": "Federal Aviation Administration", "rule_count": 1}]
        replica.return_value = {"data": {"rows": ranking}}
        primary.return_value = {"data": {"count": 1, "results": [
            {"document_number": "test-record", "agencies": [
                {"id": 159}, {"id": 159}, {"raw_name": "Unmapped attribution"},
            ]},
        ]}}
        answer, evidence, status, _ = register_case("Q02", date(2026, 11, 21))
        self.assertEqual(answer, ranking)
        self.assertEqual(status, "verified")
        self.assertEqual(evidence[1]["data"]["agency_counts"], {159: 1})
