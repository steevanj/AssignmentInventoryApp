from decimal import Decimal

from django.test import SimpleTestCase

from orders.calculations import calculate_line_amount, calculate_order_totals, round_money


class OrderCalculationTests(SimpleTestCase):
    def test_example_from_brief_multiple_items_with_discount(self):
        totals = calculate_order_totals([(2, Decimal("1500.00")), (3, Decimal("500.00"))], Decimal("10"))

        self.assertEqual(totals.line_amounts, [Decimal("3000.00"), Decimal("1500.00")])
        self.assertEqual(totals.subtotal, Decimal("4500.00"))
        self.assertEqual(totals.discount_amount, Decimal("450.00"))
        self.assertEqual(totals.grand_total, Decimal("4050.00"))

    def test_no_discount(self):
        totals = calculate_order_totals([(1, Decimal("99.99"))], Decimal("0"))
        self.assertEqual(totals.discount_amount, Decimal("0.00"))
        self.assertEqual(totals.grand_total, Decimal("99.99"))

    def test_discount_is_rounded_half_up(self):
        # 33.33 x 12.5% = 4.16625 -> 4.17
        totals = calculate_order_totals([(1, Decimal("33.33"))], Decimal("12.5"))
        self.assertEqual(totals.discount_amount, Decimal("4.17"))
        self.assertEqual(totals.grand_total, Decimal("29.16"))

    def test_grand_total_always_equals_subtotal_minus_discount(self):
        totals = calculate_order_totals([(3, Decimal("19.99")), (7, Decimal("0.35"))], Decimal("17.5"))
        self.assertEqual(totals.grand_total, totals.subtotal - totals.discount_amount)

    def test_round_money_and_line_amount(self):
        self.assertEqual(round_money("2.675"), Decimal("2.68"))
        self.assertEqual(calculate_line_amount(3, "0.1"), Decimal("0.30"))
