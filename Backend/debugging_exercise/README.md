# Debugging Exercise: `calculate_total`

## The original function
```python
def calculate_total(items):
    total = 0
    for item in items:
        amount = item["qty"] * item["rate"]
        total = amount
    return total
```
With `[{"qty": 2, "rate": 100}, {"qty": 3, "rate": 50}]` it returns **150**, but the expected result is **350**.

## Cause of the incorrect result
`total = amount` **replaces** the running total on every pass of the loop instead of adding to it. After the loop, `total` only holds the amount of the **last** item (3 × 50 = 150). The first item's 200 is thrown away.

The fix is one character: `total += amount`.

## Corrected function
See [`calculate_total.py`](calculate_total.py). Besides the `+=` fix, it also:

| Situation | Behaviour |
|---|---|
| Normal input | Returns the sum of qty × rate as a `Decimal` rounded to 2 places (`Decimal("350.00")`). |
| **Empty list** | Returns `Decimal("0.00")`. With no items the total is zero, which is not an error. |
| **qty or rate missing** (or `None`) | Raises `ValueError("Item 2: rate is missing.")`. The original raised a bare `KeyError: 'rate'`, which doesn't say which item is wrong. Skipping the item silently would give a wrong total, so failing loudly is safer. |
| **Invalid quantity** | qty must be a whole number > 0. `0`, `-1`, `2.5`, `"2"` and `True` are rejected with a clear `ValueError`. |
| **Invalid rate** | rate must be a number >= 0. `-10`, `"abc"`, `NaN` and `True` are rejected. Numeric strings like `"99.50"` are accepted, because values from forms or CSV files arrive as text. |
| `items` is `None` | Raises `ValueError` instead of `TypeError: 'NoneType' is not iterable`. |

`Decimal` is used instead of float so money adds up exactly. For example, `0.1 + 0.2` gives `0.30`, not `0.30000000000000004`.

## Tests demonstrating the correction
[`tests.py`](tests.py) covers:
- the example from the brief (= 350.00)
- the original buggy version returning 150 for the same input, which proves the bug was real
- empty list, single item, rounding and float rates
- missing qty or rate, plus zero, negative, decimal, text and boolean quantities
- negative, text and NaN rates

Run them from the `Backend/` folder:
```bash
python manage.py test debugging_exercise
```

## How I approached it
1. Ran the function with the given input and got 150, not 350.
2. Noticed that 150 is exactly the last item's amount, which points straight at the assignment inside the loop.
3. Wrote a failing test for 350, fixed `=` to `+=`, and the test passed.
4. Added the edge-case rules and a test for each one.
