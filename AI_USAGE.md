# AI Usage

## Tools and scope

I defined the product requirements and expected function behavior. I used ChatGPT and Codex for planning, code generation and review, documentation (including Hebrew function comments), and synthetic data. I remain responsible for understanding the implementation.

## Data-generation request

Tool: Codex. File: `data/sample_data.jsonl`.

Final prompt:

```text
Generate exactly 18 fully synthetic restaurant menu records as JSONL, with one
JSON object per line and no Markdown fences in the data file. Use exactly these
fields: id, category, name, price_cents, available. IDs must be unique positive
integers from 1 to 18. Records 1-12 must have category "food" and records 13-18
category "drink". Names must be nonempty English menu names, invented for this
academic project rather than copied from a real restaurant. price_cents must be
a positive integer, with varied values and one entry at 1901 cents to support
rounding demonstrations. Set exactly one food and one drink unavailable; use
JSON booleans. Do not include personal information, real restaurant identifiers,
card data, credentials, or any additional fields.
```

The fields are `id`, `category`, `name`, `price_cents`, and `available`. Category selects FoodItem or DrinkItem; `from_dict` creates validated objects.

## Data checks and corrections

The 18 JSONL records were checked for unique IDs, required fields, types, valid categories, positive prices, and availability. No generated record needed correction. Invalid examples confirmed rejection of malformed JSON, duplicate IDs, missing fields, and invalid values.

## Code verification

Codex ran the demo and development checks under Python 3.13.7. They passed for bill allocation, tips, validation, queues, iterators, lazy processing, and cleanup on errors. Review corrections included per-item payment tracking and rejecting boolean/float identifiers, and preventing closure before all items are served. Closure checks covered ordered, preparing, served, and unpaid cases. The final demo closes the table after all items are served and paid.
