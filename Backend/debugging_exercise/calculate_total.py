"""
Part 11 - Debugging exercise.

Original (buggy) version, kept here for reference:

    def calculate_total(items):
        total = 0
        for item in items:
            amount = item["qty"] * item["rate"]
            total = amount          # <-- bug: overwrites instead of adding
        return total

See README.md in this folder for the explanation.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

TWO_PLACES = Decimal("0.01")


def calculate_total(items):
    """
    Return the total of qty x rate for every item, as a Decimal rounded to
    2 decimal places.

    - An empty list returns Decimal("0.00").
    - A missing "qty" or "rate" raises ValueError naming the item.
    - qty must be a whole number greater than 0.
    - rate must be a number that is 0 or more.
    """
    if items is None:
        raise ValueError("items must be a list, not None.")

    total = Decimal("0")
    for position, item in enumerate(items, start=1):
        qty = _read_quantity(item, position)
        rate = _read_rate(item, position)
        total += qty * rate  # the fix: add each amount to the running total

    return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _read_quantity(item, position):
    if "qty" not in item or item["qty"] is None:
        raise ValueError(f"Item {position}: qty is missing.")
    qty = item["qty"]
    # bool is a subclass of int in Python, so True would otherwise count as 1
    if isinstance(qty, bool) or not isinstance(qty, int):
        raise ValueError(f"Item {position}: qty must be a whole number, got {qty!r}.")
    if qty <= 0:
        raise ValueError(f"Item {position}: qty must be greater than 0, got {qty}.")
    return qty


def _read_rate(item, position):
    if "rate" not in item or item["rate"] is None:
        raise ValueError(f"Item {position}: rate is missing.")
    raw = item["rate"]
    if isinstance(raw, bool):
        raise ValueError(f"Item {position}: rate must be a number, got {raw!r}.")
    try:
        # str() first so a float like 0.1 becomes exactly 0.1, not 0.1000000000000000055...
        rate = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Item {position}: rate must be a number, got {raw!r}.")
    if not rate.is_finite():
        raise ValueError(f"Item {position}: rate must be a number, got {raw!r}.")
    if rate < 0:
        raise ValueError(f"Item {position}: rate cannot be negative, got {raw}.")
    return rate
