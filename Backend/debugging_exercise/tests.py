from decimal import Decimal

from django.test import SimpleTestCase

from .calculate_total import calculate_total


def original_calculate_total(items):
    """The function exactly as given in the assignment (with the bug)."""
    total = 0
    for item in items:
        amount = item["qty"] * item["rate"]
        total = amount
    return total


EXAMPLE_ITEMS = [{"qty": 2, "rate": 100}, {"qty": 3, "rate": 50}]


class OriginalBugTests(SimpleTestCase):
    def test_original_only_returns_the_last_item(self):
        self.assertEqual(original_calculate_total(EXAMPLE_ITEMS), 150)


class CalculateTotalTests(SimpleTestCase):
    def test_example_from_assignment_is_350(self):
        self.assertEqual(calculate_total(EXAMPLE_ITEMS), Decimal("350.00"))

    def test_empty_list_returns_zero(self):
        self.assertEqual(calculate_total([]), Decimal("0.00"))

    def test_single_item(self):
        self.assertEqual(calculate_total([{"qty": 4, "rate": "12.50"}]), Decimal("50.00"))

    def test_float_rates_add_up_exactly(self):
        items = [{"qty": 1, "rate": 0.1}, {"qty": 1, "rate": 0.2}]
        self.assertEqual(calculate_total(items), Decimal("0.30"))

    def test_rounds_half_up_to_two_places(self):
        self.assertEqual(calculate_total([{"qty": 1, "rate": "10.005"}]), Decimal("10.01"))

    def test_zero_rate_is_allowed(self):
        self.assertEqual(calculate_total([{"qty": 3, "rate": 0}]), Decimal("0.00"))

    def test_none_items_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_total(None)


class MissingValueTests(SimpleTestCase):
    def test_missing_qty(self):
        with self.assertRaisesMessage(ValueError, "Item 1: qty is missing."):
            calculate_total([{"rate": 100}])

    def test_missing_rate_names_the_item(self):
        with self.assertRaisesMessage(ValueError, "Item 2: rate is missing."):
            calculate_total([{"qty": 1, "rate": 10}, {"qty": 2}])

    def test_none_values_count_as_missing(self):
        with self.assertRaises(ValueError):
            calculate_total([{"qty": None, "rate": 10}])
        with self.assertRaises(ValueError):
            calculate_total([{"qty": 1, "rate": None}])


class InvalidValueTests(SimpleTestCase):
    def test_invalid_quantities(self):
        for bad_qty in [0, -1, 2.5, "2", True]:
            with self.subTest(qty=bad_qty), self.assertRaises(ValueError):
                calculate_total([{"qty": bad_qty, "rate": 10}])

    def test_invalid_rates(self):
        for bad_rate in [-10, "abc", "NaN", True, [10]]:
            with self.subTest(rate=bad_rate), self.assertRaises(ValueError):
                calculate_total([{"qty": 1, "rate": bad_rate}])
