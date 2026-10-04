# AI Usage

**Elick Chitrit**

## How I used the tools

I used ChatGPT to discuss the idea and course requirements, and Codex to help with the proposal, code, documentation, and verification. I supplied the product requirements and approved the direction as the project progressed. The assistance included generated code and text, not just explanations.

This file records that work as required by the assignment. I remain responsible for understanding the code and being able to explain the design or make changes during assessment.

| Part | Help received |
|---|---|
| A | An English proposal with the nine required sections, based on my restaurant idea |
| B | Entity planning, OOP implementation, validation, and per-item mock payment tracking |
| C | Collections, preparation queues, grouping, sorting, and a local POS view |
| D | Iterators, generators, file loading, timing, and synthetic menu data |
| E | The full demo, package files, README, and local verification |
| Writing | A simpler personal introduction and shorter comments, without changing the business logic |

The project stays within the course material. It has no real card data, payment service, or Tabit connection.

## What changed during review

- The first model plan missed Restaurant, Table, and MockPaymentMethod. They were added before implementation.
- A payment total was not enough to track individual paid items. Receipts now record each settled item share separately from the tip.
- Shared amounts use cents, and existing orders keep their original price if the menu changes.
- Queues reject duplicates, handle ties and empty/stale requests, and do not automatically mark selected items as served.
- The proposal was shortened, then moved into README. All nine sections remain there, with no duplicate proposal file.
- The final Part B review added `display_price` to MenuItem and `has_active_payment_method` to Diner. Together with `from_dict`, these give each class two required OOP tools. The price property is used in item descriptions, and the payment property is used at checkout.

## Data-generation request

Tool: Codex. Date: 2026-10-04. File: `data/sample_data.jsonl`.

The final request used for the data was:

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

The schema is `id`, `category`, `name`, `price_cents`, and `available`. Category selects FoodItem or DrinkItem, and `from_dict` uses the same model validation as other constructors.

## Data checks and corrections

The output has 18 valid JSON objects on 18 lines, unique IDs 1-18, 12 foods, 6 drinks, two unavailable items, positive integer prices, and one 1901-cent item. No generated record needed correction.

Separate invalid examples checked duplicate IDs, malformed JSON, missing/extra fields, blank/non-object lines, invalid categories, bad IDs, empty names, noninteger prices, and invalid availability. The loader rejected them with a line number and closed the file. A tracked file object also confirmed that neither `read` nor `readlines` was used. These invalid examples were not put in the project dataset.

## Code verification

All verification below ran under Python 3.13.7 on 2026-10-04:

- The initial Part B version passed 79 development checks.
- After the payment and processing work, 138 checks passed for the model, bill allocation, tips, queues, grouping, sorting, and local POS snapshots.
- Part D passed 105 checks for independent iterators, exhaustion/recreation, deferred work, the three-stage pipeline, early stopping, repository validation, file cleanup, and timer cleanup without hiding exceptions.
- The full `main.py` run passed, including expected initial balances of 3251, 7800, 3750, and 0 cents. After a later 1700-cent drink, the final item total is 16501 cents, tips are 1029 cents, all items are served and mock-paid, and the table is closed.
- The pipeline trace confirms that two results require items 1-4 only. Items 5 and 6 are not inspected.
- After the final model changes, all 138 model/processing checks and 105 Part D checks passed again, along with the full demo. Focused checks covered inherited display prices, price updates, and missing, active, and inactive mock payment methods.

Codex ran the development checks. The verification scripts are in its working directory (`work/verify_parts_bc.py` and `work/verify_part_d.py`), outside the academic repository. `main.py` is the reproducible project demonstration. Python 3.10 is the declared minimum, but it was not separately run in this environment.

The final writing pass changes the introduction, wording, comments, and long dashes. The executable code is checked against its previous version, and the demo is run again. The completed code, data, and documentation are committed and pushed. Pull-request review, instructor access, and actual submission still need to be completed.
