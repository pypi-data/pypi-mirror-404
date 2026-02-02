import unittest
from decimal import Decimal

from api.services.value_service import _find_closest_hle_lowest_price


class TestPromptLevelBaselineModelSelection(unittest.TestCase):
    def test_find_closest_hle_picks_lowest_price_on_tie(self):
        model_pricing = {
            "a": {"hle_score": 0.80, "blended_price": Decimal("0.010")},
            "b": {"hle_score": 0.80, "blended_price": Decimal("0.005")},  # same HLE, cheaper
            "c": {"hle_score": 0.81, "blended_price": Decimal("0.001")},  # farther HLE
        }
        chosen = _find_closest_hle_lowest_price(0.80, model_pricing)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["model_id"], "b")

    def test_find_closest_hle_ignores_missing_data(self):
        model_pricing = {
            "no_hle": {"hle_score": None, "blended_price": Decimal("0.001")},
            "no_price": {"hle_score": 0.50, "blended_price": None},
            "valid": {"hle_score": 0.49, "blended_price": Decimal("0.002")},
        }
        chosen = _find_closest_hle_lowest_price(0.50, model_pricing)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["model_id"], "valid")

    def test_find_closest_hle_returns_none_without_current_hle(self):
        model_pricing = {
            "a": {"hle_score": 0.80, "blended_price": Decimal("0.010")},
        }
        self.assertIsNone(_find_closest_hle_lowest_price(None, model_pricing))


if __name__ == "__main__":
    unittest.main()


