# Expense API contract

Both the web and Android clients create expenses with the same request shape:

`POST /api/trips/{trip_id}/expenses`

The trip ID is supplied in the URL, not duplicated in the JSON body. Amounts are decimal strings with two fractional digits so clients do not serialize money through binary floating-point values.

```json
{
  "description": "Market groceries",
  "total_amount": "24.00",
  "payer_id": 101,
  "splits": [
    {
      "user_id": 101,
      "amount_owed": "8.00",
      "calculation_method": "equal"
    },
    {
      "user_id": 102,
      "amount_owed": "8.00",
      "calculation_method": "equal"
    },
    {
      "user_id": 103,
      "amount_owed": "8.00",
      "calculation_method": "equal"
    }
  ]
}
```

`payer_id` and each `user_id` are PostgreSQL `BIGINT` IDs represented as JSON integers. `calculation_method` is one of `equal`, `percentage`, or `exact`. Equal splits allocate integer cents in participant order, assigning any remainder cents to earlier participants. Expense requests may also include `currency` (three-letter code, defaults to `USD`) and `category` (defaults to `Other`). A percentage split may include a `percentage` decimal string on every split; when omitted, the server validates the supplied amounts sum exactly to the total.

## Authentication and trips

- `POST /api/auth/sign-up` accepts `email`, `password`, and optional `display_name`; `POST /api/auth/sign-in` accepts `email` and `password`. Both return a bearer `access_token` and user object.
- `GET /api/auth/me` returns the authenticated user.
- `GET /api/trips` lists the caller's trips. `POST /api/trips` accepts `name` and optional `destination`.
- `GET /api/trips/{trip_id}` returns the trip, members, expenses, member count, and `total_spent_by_currency` so amounts in different currencies are never combined.
- `POST /api/trips/{trip_id}/members` adds an existing account by email.
- `GET /api/trips/{trip_id}/expenses` and `GET /api/trips/{trip_id}/balances` return expenses and current simplified balances, grouped by currency.

Except for health and authentication routes, requests require `Authorization: Bearer <access_token>`. Trip membership is checked before returning or modifying trip data.

## Idempotency

Clients may send `X-Idempotency-Key: <opaque unique string>` on `POST /api/trips/{trip_id}/expenses`. A client generates one key per user action and reuses it when retrying the same request after a timeout or network failure. A server that supports the header should return the original result for a repeated key with an identical body, and respond `422` if the key is reused with a different body. The header is optional, so servers that do not implement it yet remain compatible.

## Errors

Error responses should be JSON with a human-readable `detail` string. Both clients display `detail` when present and otherwise fall back to the HTTP status code.

```json
{ "detail": "Exact shares must add up to the total." }
```

## Split rules shared by every layer

`backend/contri_dedo/debt_simplifier.py` implements the canonical rules: `split_equally`, `split_by_percentage` (percentages up to two decimals that add up to 100; leftover cents go to the largest fractional remainders, ties to the earlier participant), and `split_exact` (shares must add up to the total). The web and Android calculators must produce the same amounts.
