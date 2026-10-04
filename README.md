# BillsSplit

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
**Trigger:** Staff open a table session and diners join through its QR code. **Flow:** Diners view existing items, identify what they consumed or shared, and order from the menu. A personal item is charged to its consumer. A shared item is split equally among its participants, with any remaining cents allocated consistently. Diners settle their shares with synthetic mock cards and choose **10%, 12%, 15%, 20%, Other (manual amount), or None** as a tip. Percentages apply to the item amount being settled. **Result:** Payments update balances and staff close a fully allocated, paid session. Prices and quantities must be positive, ordered items must be available, participants must belong to the table, and duplicate participation is rejected. Payment/tip amounts cannot be negative, and paid allocations cannot change.

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
| F - Git/GitHub | Changes pushed and final model updates reviewed and merged through PR #1; instructor access and submission remain |
| G - AI data and documentation | 18 synthetic records and usage documentation are included |

## Files

| File | What it contains |
|---|---|
| `main.py` | The full demo; no business classes are defined here |
| `bills_split/models.py` | Business classes, relationships, validation, and payments |
| `bills_split/processing.py` | Collections, grouping, sorting, queues, and the local POS view |
| `bills_split/iterators.py` | The custom collection/iterator, generator, and lazy pipeline |
| `bills_split/repository.py` | JSONL loading, object creation, and lookup by ID |
| `bills_split/context_managers.py` | Timing an operation in normal and error cases |
| `bills_split/__init__.py` | The package initializer |
| `data/sample_data.jsonl` | 18 synthetic menu records |
| `README.md` | Proposal, design choices, and run instructions |
| `GUIDE_HE.md` | A short Hebrew companion guide to running the demo and understanding its output |
| `AI_USAGE.md` | Tools used, data-generation request, and verification |
| `.gitignore` | Files that should stay out of Git |
| `pyproject.toml` | Project metadata, Python requirement, and an empty dependency list |

## Model and design choices

I separated the physical table from the meal taking place at it. `Restaurant` contains the menu and tables; `TableSession` contains the diners, orders, and payments for one meal. An `Order` contains `OrderItem` objects, with methods to add, find, remove draft items, and calculate the total. Once submitted, its lines stay fixed. More purchases go into a new order.

For inheritance, `FoodItem` and `DrinkItem` extend `MenuItem`. Both implement `preparation_area()`: food goes to the kitchen, drinks to the bar. `Order.preparation_requests()` calls the same method for either type. It does not need an `if` for each subclass.

Each `Diner` can have a `MockPaymentMethod`. A `MockPayment` records exactly which item shares were paid, with the tip separate. Staff and shift managers are users in the product concept; this demo does not include account permissions or login.

The model uses alternative constructors (`classmethod`), computed properties, a tip helper (`staticmethod`), and `__len__` where it fits. `MenuItem.display_price` formats the current menu price for display and is inherited by food and drink items. `Diner.has_active_payment_method` checks the current mock method before checkout. Both classes also have `from_dict`, so each uses two of the OOP tools required in Part B. `__str__` gives a readable description; `__repr__` shows useful details when debugging. Invalid inputs raise `ValueError` before the valid state changes. Model lookups require positive integer IDs. Booleans, floats, and other invalid values are rejected before they can select an existing record, including during participation, queueing, and checkout. Collection properties return copies, so changes go through the model's methods.

### Money and shared items

I store money as integer cents. This avoids floating-point rounding issues when dividing a bill. A shared item's total is divided among its participants only. Remaining cents go in participation order, so the shares differ by at most one cent and still add up to the original price. The order keeps its agreed price even if the menu price changes later.

A diner pays their current unpaid shares in full. Tips can be 10%, 12%, 15%, 20%, `Other` with a nonnegative manual amount, or `None`. Percentage tips apply to that payment's item amount and round half up to a cent. A tip does not reduce the amount owed for the items.

All items must be allocated before checkout. Once someone pays a share of an item, its participants cannot change. A later order can create a new balance without changing earlier payments. The session closes only when all items are allocated and the item balance is zero.

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

## Running the demo

Python 3.10 or later is required. The full run was verified with Python 3.13.7. Only the standard library is used, so there are no packages to install.

From the `BiilsSplit` root folder:

```sh
python3 --version
python3 main.py
```

For a new checkout:

```sh
git clone https://github.com/elick-chitrit/BiilsSplit.git
cd BiilsSplit
python3 main.py
```

Run from the repository root so `data/sample_data.jsonl` can be found. The demo runs once, prints the results, and exits. There is no interactive menu.

The run shows the menu, table membership, orders, validation, collections, both queues, independent iterators, generators, the two-result pipeline, timed operations, mock payments, and a later order.

The terminal output has eight numbered sections and aligned tables for the menu, ordered items and participants, diner shares/paid amounts/balances, mock receipts, and local POS status. Expected validation failures are marked `PASS - Rejected`, followed by the reason. The final `DEMO COMPLETE` section shows the closed table, total item bill, zero unpaid balance, and mock tips. All values are still produced by the same business model.

Diners A-D initially owe **32.51, 78.00, 37.50, and 0.00**. The shared 19.01 starter splits into 9.51 and 9.50. After an extra 17.00 drink, the item total is **165.01**, unpaid balances are **0.00**, tips total **10.29**, and the table closes. The diner who did not consume anything is never charged. Printed rejection messages are intentional examples of invalid inputs.

## Local Tabit simulation

`local_pos_snapshot` returns the current orders, fulfillment/payment states, receipts, diner balances, and table totals. A new call reflects changes; an older snapshot stays unchanged. Payment states are `unallocated`, `unpaid`, `partially_mock_paid`, and `mock_paid`.

Tabit is the future integration target. This demo does not send data to restaurant computers or use a real API. The QR reference is also a mock label. It demonstrates the business flow locally.

## Verification and submission

The model/processing checks passed 138 checks, and Part D passed another 105. The full demo also ran successfully. The final model review also checked price updates in all three menu classes and diners with missing, active, and inactive mock payment methods. After the identifier correction, all 243 existing checks passed again. Another 160 invalid-identifier operations were rejected without state changes, and 800 allocation/settlement scenarios conserved every cent and charged nonparticipants zero. The full demo passed with the new identifier-rejection examples. Invalid test data and development scripts stay outside the project; the submitted sample file contains valid records only.

The project files are in GitHub. I keep changes small and make a commit and push after each completed, verified task, including separate meaningful changes in the same file. The target is at least nine meaningful commits; the course requires at least seven.

The final model updates were checked in [Pull Request #1](https://github.com/elick-chitrit/BiilsSplit/pull/1) and merged into `main`. The history exceeds nine meaningful commits. The original commits were preserved during the merge.

Before submission:

- Give the instructor access to the currently private repository.
- Include the current `git log --oneline --graph --all` output in the submission.
- Submit the repository link and required materials through the course submission system.
