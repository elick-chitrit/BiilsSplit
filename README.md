# BillsSplit

[GitHub repository](https://github.com/elick-chitrit/BiilsSplit)

[Hebrew guide: running the demo and reading the output](GUIDE_HE.md)

A few years ago, I came up with the idea for BillsSplit after running into a problem at restaurant dinners with a large group of friends: figuring out who should pay for what. Some people shared dishes, others ordered for themselves, and splitting the bill equally did not always make sense.

The goal is simple: each person should pay for what they actually ate or drank. If they shared something, they pay their share. If they did not have it, they should not pay for it.

This project is a local Python demo of that startup idea, built for my Advanced Programming course. It covers the business logic: the restaurant menu, table orders, shared items, individual balances, tips, and mock payments. The full product would connect to Tabit. For this stage, the POS state is simulated locally and all payments are fake.

Written and edited by Elick Chitrit.

## Project Proposal

### 1. Project Name and One-Sentence Description
**BillsSplit** lets restaurant diners join a table by QR code, browse the menu, order, and pay only for items they consumed or shared.

### 2. Business Need / Problem
Splitting a bill among many friends can take time and leave someone paying for things they did not order or share. Additional orders also depend on staff availability. Diners and staff need a clear view of the table's orders and balances.

### 3. Main Users and Roles
**Diners:** view the menu and orders, join the items they consumed, order more, and make mock payments with optional tips. **Restaurant staff:** receive orders and update fulfillment. **Shift managers:** monitor tables, balances, and closure.

### 4. Main Business Process: Trigger, Flow, and Result
**Trigger:** Staff open a table session and diners join through its QR code. **Flow:** Diners view existing items, identify what they consumed or shared, and order from the menu. A personal item is charged to its consumer. A shared item is split equally among its participants, with any remaining cents allocated consistently. Diners settle their shares with synthetic mock cards and choose **10%, 12%, 15%, 20%, Other (manual amount), or None** as a tip. Percentages apply to the item amount being settled. **Result:** Payments update balances and staff close an allocated, paid, served session. Prices and quantities must be positive, ordered items must be available, participants must belong to the table, and duplicate participation is rejected. Payment/tip amounts cannot be negative, and paid allocations cannot change.

### 5. Information Flow
The restaurant supplies tables and menus. Diners create orders, item participation, and tip choices. Staff update fulfillment. The system calculates personal amounts and produces the current order, item/payment, and table state. **Tabit is the external POS integration target** so these updates can appear on restaurant computers. Stage 1 simulates synchronization locally; it does not use a real Tabit API. All demo data and payments are synthetic, with no real card data, payment provider, or payment API.

### 6. Expected Business Value
A fairer bill, fewer arguments and calculation errors, quicker ordering and checkout, and less manual work for staff.

### 7. Core Entities and Initial Relationships
A **Restaurant** has **Tables** and **Menu Items**. A **Table Session** belongs to a table and contains **Diners** and **Orders**. Orders contain **Order Items** linked to menu items and their participating diners. A diner's **Mock Payment Method** supports **Mock Payments**, which record item shares and tips separately. Tabit is external.

### 8. Two Central Use Cases / Decisions Supported
1. **Split a shared item:** Three friends share a dish and each pays one-third, allowing for cent rounding. Anyone who did not share it owes nothing for it.
2. **Order more:** A diner chooses from the menu, staff update the order, and everyone at the table sees the new order and locally simulated POS state.

### 9. One Future Extension
Connect to Tabit in a later course stage, subject to authorized access and supported capabilities. Payments remain mock-only.

## Project status

| Part | Status |
|---|---|
| A - Proposal | Approved and included above |
| B - OOP model | Implemented |
| C - Collections and processing | Implemented |
| D - Iterators, generators, loading, context manager | Implemented |
| E - Structure and full demo | Implemented; the full run passed |
| F - Git/GitHub | Changes pushed, PR #1 merged, and the repository is public; submission remains |
| G - AI data and documentation | 18 synthetic records and usage documentation are included |

## Model and design choices

Each function and method starts with a short Hebrew comment explaining its purpose.

I separated the physical table from the meal taking place at it. `Restaurant` contains the menu and tables; `TableSession` contains the diners, orders, and payments for one meal. An `Order` contains `OrderItem` objects, with methods to add, find, remove draft items, and calculate the total. Once submitted, its lines stay fixed. More purchases go into a new order.

For inheritance, `FoodItem` and `DrinkItem` extend `MenuItem`. Both implement `preparation_area()`: food goes to the kitchen, drinks to the bar. `Order.preparation_requests()` calls the same method for either type. It does not need an `if` for each subclass.

Each `Diner` can have a `MockPaymentMethod`. A `MockPayment` records exactly which item shares were paid, with the tip separate. Staff and shift managers are users in the product concept; this demo does not include account permissions or login.

The model uses alternative constructors (`classmethod`), computed properties, a tip helper (`staticmethod`), and `__len__` where it fits. `MenuItem.display_price` formats the current menu price for display and is inherited by food and drink items. `Diner.has_active_payment_method` checks the current mock method before checkout. Both classes also have `from_dict`, so each uses two of the OOP tools required in Part B. `__str__` gives a readable description; `__repr__` shows useful details when debugging. Invalid inputs raise `ValueError` before the valid state changes. Model lookups require positive integer IDs. Booleans, floats, and other invalid values are rejected before they can select an existing record, including during participation, queueing, and checkout. Collection properties return copies, so changes go through the model's methods.

### Money and shared items

I store money as integer cents. This avoids floating-point rounding issues when dividing a bill. A shared item's total is divided among its participants only. Remaining cents go in participation order, so the shares differ by at most one cent and still add up to the original price. The order keeps its agreed price even if the menu price changes later.

A diner pays their current unpaid shares in full. Tips can be 10%, 12%, 15%, 20%, `Other` with a nonnegative manual amount, or `None`. Percentage tips apply to that payment's item amount and round half up to a cent. A tip does not reduce the amount owed for the items.

All items must be allocated before checkout. Once someone pays a share of an item, its participants cannot change. A later order can create a new balance without changing earlier payments. The session closes only when all items are allocated, all items have been served, and the item balance is zero. If any item is still ordered or preparing, closure raises `ValueError` and leaves the session open so staff can finish serving it.

## Data structures

| Need | Structure | Why I used it |
|---|---|---|
| Ordered work list | `list` | Keeps the order and allows changes |
| Fixed preparation record | `tuple` | Stores ID, preparation area, quantity, and status; `*details` collects the remaining fields |
| Unique diner and queued IDs | `set` | Supports membership, `add`, `discard`, intersection, and difference |
| Find an item by ID | `dict` | Direct lookup; duplicate IDs are rejected |
| Group items by kitchen/bar | `dict` of lists | Keeps each area's items together; uses `get`, `items()`, and unpacking |
| Routine preparation requests | `deque` | `append` and `popleft` keep arrival order |
| Urgent preparation requests | `heapq` | Lower numbers mean higher priority: 1 urgent, 2 elevated, 3 routine |

The two queues demonstrate alternative workflows for the same table. They are not two simultaneous dispatch channels. Priority entries use `(priority, arrival_counter, item_id)`, so ties follow arrival order and model objects do not need to be compared. The internal heap is not a sorted list.

An empty queue returns `None`. Requests are skipped if they have already moved to preparation/served or the session has closed. Selecting a request does not mark it as served; staff update fulfillment separately.

The module includes list, set, and dictionary comprehensions. Preparation sorting uses a named function; balance sorting uses a short lambda. Both use tuple keys with more than one field. Sets are sorted before display because their iteration order is not part of the result.

| Changes existing state | Returns a new collection or view |
|---|---|
| Adding/removing draft order items | Pending-item list |
| Adding/removing item participants | Unique/common diner IDs |
| Enqueueing/dequeueing requests | ID index and preparation groups |
| Recording a payment | Sorted preparation work and balances |
| Closing a session | Local POS snapshot |

## Iterators and lazy processing

`OrderItemCollection` keeps the original order of its members. It stores the same item objects, so their updated statuses remain visible. Each `iter(collection)` returns a new `OrderItemIterator` with its own position. The iterator returns itself from `__iter__` and raises `StopIteration` when finished. Two iterators can move independently over the same collection.

`pending_order_items` uses `yield` for items that have not been served. Creating the generator does not inspect items. `next` starts the work; a following `for` continues where it stopped. After it finishes, it cannot restart. A new generator is needed for another pass.

The kitchen pipeline has three generator-expression stages:

1. Filter out served items.
2. Keep kitchen items.
3. Return `(item_id, quantity)` requests.

There are no intermediate lists. Calling `next` pulls only enough input for the next result. In the demo, item 1 is served and item 2 is a drink. The first two kitchen results are items 3 and 4, so the pipeline does not inspect items 5 or 6. The `visited` list just records what the demo inspected; it is not an intermediate pipeline result.

A list comprehension processes all input immediately and stores the result. A generator expression waits for consumption, which lets the caller stop early. For another complete pass, create a new pipeline and a fresh source if the old source was itself a consumed generator.

## Sample data and loading

The JSONL file has 18 synthetic menu items: 12 foods, 6 drinks, and two unavailable items. Each line is one JSON object:

| Field | Rule |
|---|---|
| `id` | Unique positive integer; not a boolean |
| `category` | `food` or `drink` |
| `name` | Nonempty English name |
| `price_cents` | Positive integer cents; one entry is 1901 for rounding examples |
| `available` | JSON boolean |

The data was generated with AI as required by the assignment. The request and checks are in [AI_USAGE.md](AI_USAGE.md). No real restaurant, personal, or card data is used.

The loader opens the file with `with open(..., encoding="utf-8")` and reads one line at a time. `json.loads` produces a dictionary, and `from_dict` creates the appropriate menu object. The loader checks malformed JSON, missing/extra fields, bad values, and duplicate IDs. Errors include the line number. The file closes on success or error; `read()` and `readlines()` are not used.

The resulting small menu is kept in a list. Reading line by line does not mean the final list uses constant memory. `MenuRepository` provides ID lookup: a missing valid ID returns `None`, and adding a duplicate raises `ValueError` without overwriting anything.

## Context manager

`OperationTimer` uses `time.perf_counter`, as shown in class. `__enter__` saves the start time and returns the timer for `with ... as ...`. `__exit__` records the duration and whether an error occurred, then ends the measurement. It returns `False`, so the original exception is not hidden.

The demo measures a normal operation and a checkout with an invalid tip. Both finish timing, but the invalid checkout still raises `ValueError`. A timer can be reused after finishing; nesting the same timer is rejected.

## Stage 1 demo results

The first eight sections cover the original menu, orders, validation, collections, queues, iterators, generators, timing, payments, and closure. Diners A-D initially owe **32.51, 78.00, 37.50, and 0.00**. After the later order, the item bill is **165.01**, the unpaid balance is **0.00**, and tips total **10.29**. Expected rejection messages are intentional. Stage 2 follows in section 9; installation and commands are below.

## Local Tabit simulation

`local_pos_snapshot` returns the current orders, fulfillment/payment states, receipts, diner balances, and table totals. A new call reflects changes; an older snapshot stays unchanged. Payment states are `unallocated`, `unpaid`, `partially_mock_paid`, and `mock_paid`.

Tabit is the future integration target. This demo does not send data to restaurant computers or use a real Tabit API. The QR reference is also a mock label. It demonstrates the business flow locally.

## Stage 1 verification

The existing development checks still pass: models and processing, iterators and loading, invalid identifiers, allocation rounding, and closure. The original model review was merged in [PR #1](https://github.com/elick-chitrit/BiilsSplit/pull/1). The repository is public and the original commit history is preserved.

## Stage 2

### 1. What I added

Diners can see an estimate of their unpaid item share in another currency before choosing a tip. I also added independent availability checks and protected reservations for limited dishes. Reserving one dish does not stop friends from sharing it: only diners who join that item split its price. Payments stay synthetic and in ILS; Tabit stays a local simulation. This is an individual submission with instructor approval.

### 2. How to run

Python 3.10+; verified with 3.13.7. Run from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python main.py            # offline demo, synthetic rates
python main.py --live     # real reference-rate request
python -m pytest -q       # offline tests
```

No API key or environment variables are needed. Settings are in `config.py`. No `.env.example` is needed for this service; `.env` files are ignored. The demo labels live and simulated data and has no interactive menu.

### 3. Code organization

```text
BiilsSplit/
  main.py                      # original demo and Stage 2 flow
  pyproject.toml               # Python requirement, requests, pytest, packaging
  .gitignore                   # local environments, caches, and secrets
  bills_split/
    __init__.py                # package initializer
    models.py                  # menu, tables, sharing, mock payments
    repository.py              # JSONL loading and item lookup
    factories.py               # create food or drink items from records
    strategies.py              # percentage, manual, or no tip
    services.py                # checkout and personal currency estimates
    api_client.py              # real/demo rate clients and response validation
    config.py                  # endpoint, timeout, retry, supported currencies
    async_processing.py        # sequential/concurrent availability checks
    threaded_processing.py     # shared stock and protected reservations
    processing.py              # collections, queues, local POS view
    iterators.py                # iterator and lazy processing
    context_managers.py        # operation timing
  data/
    sample_data.jsonl          # synthetic menu
    demo_rates.json            # synthetic offline reference rates
  tests/                       # models, patterns, API, services, concurrency, integration
  README.md                    # requirements, design, commands, evidence
  GUIDE_HE.md                  # short Hebrew guide
  AI_USAGE.md                  # assistance and verification record
```

### 4. Main design decisions

- **External service:** [Frankfurter v2 documentation](https://frankfurter.dev/). GET `/v2/rates` with `base=ILS`, `quotes=USD` (also EUR/GBP), and a connection/read timeout. The client checks HTTP status, JSON, currencies, a positive finite rate, and a nonempty date. The service converts only the diner's unpaid item share, before tip. This is a dated reference estimate, not a payment exchange rate.
- **Failures:** retry only Timeout/ConnectionError, up to three total attempts, with a wait between attempts. HTTP, malformed JSON, and invalid fields are distinct failures and are not retried. If the request fails, the estimate is unavailable; the original ILS bill and checkout remain usable. Live mode never silently substitutes demo rates. Logs contain request attempts and failure categories, without diner/payment details.
- **Factory:** `menu_item_from_dict` creates FoodItem or DrinkItem from input. The loader delegates creation to this single location.
- **Strategy:** PercentageTip, ManualTip, and NoTip share `calculate`. PaymentService receives its strategy; CurrencyQuoteService receives its rate client. The real client also accepts request/wait dependencies. This keeps calculation, communication, and coordination separate and lets tests replace dependencies.
- **Async:** three independent menu checks simulate waiting with `asyncio.sleep`. Sequential and `gather` versions use identical inputs and return input-order results, even if completion order differs. No blocking requests run inside async functions.
- **Threads:** two reservation threads share one MenuStock and one Lock. Both start before joining. The lock protects the stock check, decrement, and reservation record together. Without it, both could see one remaining dish and both approve it. Tests check approval count and final stock, not which diner wins. Orders are created afterward in the main thread; ordinary session operations are not claimed to be thread-safe. Sharing remains a separate action.

### 5. Evidence

- **55 pytest cases passed** on Python 3.13.7. Tests cover Stage 1 regressions, tip alternatives, factories, files with `tmp_path`, API errors/retry, async ordering, protected stock, and a complete checkout. Fixtures, parametrization, `pytest.raises`, Mock, and patch are used. Real HTTP is blocked in the test suite and retry waits are replaced.
- **Live run, 2026-10-29:** `python main.py --live` completed. Frankfurter returned an ILS/USD rate of **0.32121**, dated **2026-10-29**. A personal item balance of **ILS 9.00** displayed **USD 2.89**. Mock checkout then closed the table with zero outstanding balance. Future reference rates may differ.
- **TDD - personal currency estimate:** [Red](https://github.com/elick-chitrit/BiilsSplit/commit/fe1d718) failed because quote behavior was missing; [Green](https://github.com/elick-chitrit/BiilsSplit/commit/d70c4da) implemented conversion; [Refactor](https://github.com/elick-chitrit/BiilsSplit/commit/4353761) separated quote formatting from session coordination. The same test passed after both later steps. All final tests pass.

Submit the repository link through the course system. Stage 2 does not require a separate Git log file.
