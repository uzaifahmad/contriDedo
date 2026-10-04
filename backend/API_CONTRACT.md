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

`payer_id` and each `user_id` are PostgreSQL `BIGINT` IDs represented as JSON integers. `calculation_method` is one of `equal`, `percentage`, or `exact`. Equal splits allocate integer cents in participant order, assigning any remainder cents to earlier participants. The API endpoint is a client contract; it still needs a backend route implementation.
