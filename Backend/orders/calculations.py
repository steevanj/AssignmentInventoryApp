"""
The only place order money is calculated. Services, serializers and the
seed command all call these functions, so there is one rounding rule.

    Item Amount     = Quantity x Rate
    Subtotal        = Sum of Item Amounts
    Discount Amount = Subtotal x Discount Percentage / 100
    Grand Total     = Subtotal - Discount Amount

Rounding rule: every money value is rounded to 2 decimal places with
ROUND_HALF_UP (0.005 -> 0.01), which is how people round money by hand.
Each line amount is rounded first, the subtotal is the sum of the rounded
lines, and the grand total is subtotal minus the rounded discount, so the
numbers on screen always add up exactly.
"""

from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
HUNDRED = Decimal("100")

OrderTotals = namedtuple("OrderTotals", ["line_amounts", "subtotal", "discount_amount", "grand_total"])


def to_decimal(value):
    """Convert safely. Going through str() avoids float noise like Decimal(0.1)."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_money(value):
    return to_decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_line_amount(quantity, rate):
    return round_money(to_decimal(quantity) * to_decimal(rate))


def calculate_order_totals(lines, discount_percentage):
    """
    lines: iterable of (quantity, rate) pairs.
    Returns OrderTotals with each line amount plus the order level totals.
    """
    line_amounts = [calculate_line_amount(quantity, rate) for quantity, rate in lines]
    subtotal = round_money(sum(line_amounts, Decimal("0")))
    discount_amount = round_money(subtotal * to_decimal(discount_percentage) / HUNDRED)
    grand_total = subtotal - discount_amount
    return OrderTotals(line_amounts, subtotal, discount_amount, grand_total)
