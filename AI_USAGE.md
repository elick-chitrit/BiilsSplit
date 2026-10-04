# AI Usage

## Tool and responsibility

Tools: ChatGPT for the original discussion and Codex for proposal editing, implementation, review, and development verification. The student is responsible for understanding the design and code and explaining or modifying them during assessment. This file summarizes material assistance; it does not publish private conversation transcripts.

## Material assistance so far

| Work | Request / constraints | Result |
|---|---|---|
| Part A proposal | Describe the restaurant concept in English using exactly the nine business sections; menu, QR joining, consumption-based splitting, tipping, mock cards, and locally simulated Tabit synchronization | Standalone proposal; later shortened without removing required sections |
| Part B model | Check for missing entities, implement only with course material, and preserve synthetic payments | Restaurant/table/session, diners, menu inheritance, orders/lines, mock payment method and receipt; business validations |
| Part B review | Ensure earlier paid lines remain identifiable when subsequent orders are placed | Receipts store the settled amount per item; item payment states are derived from the payment ledger |
| Part C | Implement list/tuple/set/dictionaries, FIFO/priority queues, comprehensions, unpacking, and named/lambda sorting for restaurant work | Processing module and a local POS-shaped snapshot, with no external integration |
| Documentation | Check the original assignment and document the single-student scope and remaining requirements | README, data-structure rationale, mutation table, current smoke example, and remaining work |

The implementation avoids unlearned frameworks, external payment providers, genuine card fields, real personal sample data, and a real Tabit connection.

## Review findings and corrections

- The initial model plan omitted Restaurant, Table, and MockPaymentMethod; these were added before Part B implementation.
- Receipt totals alone did not explicitly identify settled items. Added validated item-share allocations, separate from tips, and ledger-derived per-item payment status.
- Clarified cent rounding and retained agreed order prices when a menu price changes.
- Added FIFO and priority duplicate protection, deterministic priority ties, empty handling, and stale-request selection rules. Selecting a request does not imply it has been prepared or served.
- Condensed the 692-word proposal while retaining all nine sections and the agreed business scope.

## Verification

The original Part B implementation passed 79 ad hoc checks. On 2026-10-04, the current revision passed 138 development checks under Python 3.13.7, using synthetic scenarios for individual/shared consumption, cent conservation, item allocation sums, repeat checkout after new orders, unchanged historical receipts, tips, invalid inputs, and closure. Processing verification covers three FIFO entries, three distinct priority values, equal-priority arrival order, duplicates, empty and stale queues, collection views, sorting, and locally refreshed POS snapshots.

Checks are executed in the development workspace without adding a test module to the academic project. The reproducible queue smoke example is in README.md. Complete demonstration code belongs in the later `main.py` deliverable.

## Required AI-generated data — pending

No `data/sample_data.jsonl` has been created yet. When working on the repository/loading stage:

1. Record the AI tool and the final data-generation prompt here.
2. Define a schema consistent with the model's required fields and business rules.
3. Generate at least 15 fully synthetic JSON records, one object per JSONL line.
4. Check duplicate IDs, missing fields, invalid values, and malformed JSON; record actual issues and fixes.
5. Load one line at a time and convert each dictionary to a business object.

The final data-generation prompt, record schema, and loading verification are intentionally not claimed complete before the data exists.

The development verifier was saved as `work/verify_parts_bc.py` in the Codex working directory, outside the academic repository, and executed with `python3 -B work/verify_parts_bc.py`. The README smoke example was also run directly and passed. No persistent test module, sample dataset, or application entry point was added to the academic project at this stage.
