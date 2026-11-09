# AI Usage Disclosure

The assignment allows AI tools as long as their use is disclosed. This file
explains which tools I used, what I used them for, and how I checked their
output. I designed and wrote the application myself. AI tools were used as a
reviewer and helper, not to generate the project.

## Tools used

- **ChatGPT**
- **Google Gemini**
- **OpenAI Codex**

## Where AI helped

| Area | How it was used |
|---|---|
| Bug finding | Pasted individual functions and asked for edge cases I might have missed (empty lists, zero or negative quantity, a missing key, repeated confirm/cancel requests). |
| Code quality review | Asked for review comments on naming, long functions and duplicated logic in views and serializers. |
| Quality checking | Asked whether my validation messages were clear, and whether the HTTP status codes (400 / 401 / 403 / 404 / 409) matched each situation. |
| Django / DRF questions | Short "how does this work" questions, e.g. how `select_for_update()` behaves in MySQL, and the order in which DRF runs field validators. |
| Filters and queries | Checked my report queries (customer sales with a date range and `Coalesce`), and asked for search/filter query examples with `Q` objects. |
| Test ideas | Asked for a list of scenarios to test for the order and stock logic, and compared it with the scenarios in the brief. |

## Example prompts

1. *"Here is my Django `confirm_order` function. Can two users confirming
   orders for the same product at the same time make stock negative? What
   would you change?"*
2. *"Review this DRF serializer for bugs. A user should not be able to change
   `stock_quantity` when editing a product. Does my `read_only_fields` setup
   actually stop that?"*
3. *"My customer sales report must include customers with no confirmed orders
   and must not count an order twice when it has several items. Is this
   Django ORM query correct?"*

## How I reviewed the output

- I did not paste suggestions in directly. I read each one, made sure I
  understood it, and rewrote it in my own code style.
- Every change was checked by running the API with real requests against the
  MySQL database (valid inputs, invalid inputs, and the wrong user or role).
- For stock logic I checked the numbers by hand: stock before, stock after,
  and the stock movement rows created.
- When two tools gave different answers, I checked the Django / DRF
  documentation and tested the behaviour myself.

## Issues found and corrected

1. **Stock could be edited through the product update API.**
   `ProductUpdateSerializer` listed `stock_quantity` in `read_only_fields`, but
   DRF ignores that setting for fields declared explicitly on the parent
   serializer. A PATCH could still change stock without creating a stock
   movement. I found it while testing a review suggestion, and fixed it by
   re-declaring the field as `read_only=True` in the subclass.

2. **Server error on an invalid discount.** The error message
   `"Discount cannot be more than 20%."` crashed with `ValueError: incomplete
   format`, because Django formats validator messages with `%`. I changed the
   message to "Discount must be between 0 and 20." The custom error handler had
   already stopped a traceback from reaching the client.

3. **Wrong status code when not logged in.** One suggestion relied on DRF's
   default session authentication, which returns 403 for a user who isn't
   logged in. That made "not logged in" look like "no permission". I added a
   small authentication subclass so these requests return 401.

## Limitations

- AI suggestions were sometimes generic or written for a different Django
  version, so each one was checked before use.
- I am responsible for all the submitted code and can explain, debug and
  modify any part of it.
