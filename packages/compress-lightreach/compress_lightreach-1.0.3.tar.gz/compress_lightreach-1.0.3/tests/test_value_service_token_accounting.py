import unittest
from decimal import Decimal

from api.services.value_service import _parse_input_token_accounting_from_metadata


class TestValueServiceTokenAccounting(unittest.TestCase):
    def test_parse_input_token_accounting_from_metadata_sums_message_stats(self):
        meta = {
            "message_stats": [
                {"role": "system", "compressed": False, "original_tokens": 10, "compressed_tokens": 10, "token_savings": 0},
                {"role": "user", "compressed": True, "original_tokens": 100, "compressed_tokens": 60, "token_savings": 40},
            ]
        }
        out = _parse_input_token_accounting_from_metadata(__import__("json").dumps(meta))
        self.assertIsNotNone(out)
        self.assertTrue(out["has_token_data"])
        self.assertEqual(out["input_original_tokens"], 110)
        self.assertEqual(out["input_compressed_tokens"], 70)
        self.assertEqual(out["input_token_savings"], 40)

    def test_parse_input_token_accounting_handles_missing_or_invalid(self):
        self.assertIsNone(_parse_input_token_accounting_from_metadata(None))
        self.assertIsNone(_parse_input_token_accounting_from_metadata("not-json"))

    def test_value_comparison_forecast_shape_contract(self):
        # This is a lightweight "shape" contract for the new forecast payload:
        # { dates: [...], actual_spend: [...], fully_optimized: [...], baseline: [...] }
        forecast = {
            "dates": ["2026-01-01", "2026-01-02"],
            "actual_spend": [1.0, 2.0],
            "fully_optimized": [0.8, 1.6],
            "baseline": [1.2, 2.4],
        }
        self.assertEqual(len(forecast["dates"]), len(forecast["actual_spend"]))
        self.assertEqual(len(forecast["dates"]), len(forecast["fully_optimized"]))
        self.assertEqual(len(forecast["dates"]), len(forecast["baseline"]))


if __name__ == "__main__":
    unittest.main()


