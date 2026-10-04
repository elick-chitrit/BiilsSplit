# BillsSplit

Academic Python project by one student. The product concept is dine-in ordering and fair bill splitting; the current deliverable is its local business model, not a deployed app.

## Current scope and progress

| Part | Current state |
|---|---|
| A — Business proposal | Approved; concise standalone [proposal](PROJECT_PROPOSAL.md) |
| B — Object-oriented model | Implemented, including item-level synthetic payment receipts |
| C — Collections and processing | Implemented; verification described below |
| D — Iterators, generators, file loading, context manager | Pending |
| E — Package setup and full `main.py` demonstration | Pending |
| F — Git/GitHub | Private repository exists; continue meaningful commits toward the required seven |
| G — AI data and documentation | AI usage documented; 15+ synthetic JSONL records still pending |

The four-student extension does not apply. Part A remains a separate approval artifact for now. For final submission, move its content under **Project Proposal** in this README and retire the standalone file so the specification is not duplicated.

## Current file map

```text
BiilsSplit/
├── PROJECT_PROPOSAL.md
├── README.md
├── AI_USAGE.md
├── .gitignore
└── bills_split/
    ├── models.py
    └── processing.py
```

Future required files: `bills_split/__init__.py`, `repository.py`, `iterators.py`, `context_managers.py`, `data/sample_data.jsonl`, `main.py`, and `pyproject.toml`. They have not been created or claimed complete.

## Business model and OOP decisions

- `Restaurant` owns menu entries and physical `Table` objects. `TableSession` represents one meal and contains diners, orders, and accepted mock payments.
- `Order` contains `OrderItem` objects and supports adding, finding, removing draft lines, and calculating totals. Submitted orders are fixed; extra purchases form new orders.
- `MenuItem` is the base for `FoodItem` and `DrinkItem`. Both override `preparation_area()`. `Order.preparation_requests()` calls that common operation without branching on the subtype: kitchen for food, bar for drinks.
- `Diner` holds a `MockPaymentMethod`. An accepted `MockPayment` records exactly which item shares it settles, with the tip separate. Staff and shift managers are business actors; Stage 1 does not implement login or access-control roles.
- Alternative constructors use `classmethod`; computed properties, `staticmethod`, and `__len__` serve business needs. Invalid business inputs raise explanatory `ValueError`s before changing valid state. Collections are exposed as copies; mutation uses model methods.

All money is stored as integer cents. A shared line splits equally among its associated diners; remaining cents go in association order. Shares differ by at most one cent and sum to the exact line total. A nonparticipant owes zero. Menu price changes do not alter an existing line's agreed price.

Payments settle a diner's current outstanding item shares in full. Tips are 10%, 12%, 15%, 20%, `Other` with a nonnegative manual cent amount, or `None`. Percentage tips apply to the item amount settled in that payment and round half up to a cent. Tips never reduce the table's item debt.

Every line must have participants before checkout. Once any share of a line is paid, that line's participation is locked. Later orders may create new balances without changing earlier paid lines. A table closes only when all lines are allocated and its balance is zero.

## Part C: data structures and processing

| Business need | Structure | Reason |
|---|---|---|
| Ordered, editable work list | `list` | Preserves submission order and supports appending |
| Fixed preparation record | `tuple` | Item ID, destination, quantity, status; `*details` collects the remaining fields |
| Unique participants and queued IDs | `set` | Membership, `add`, `discard`, intersection, and difference; stores integer IDs |
| Locate a line by ID | `dict` | Index comprehension; duplicate IDs are rejected before constructing it |
| Group work by preparation area | `dict` of lists | `get` handles a destination not yet seen; `items()` and unpacking support workload counts |
| Routine preparation requests | `deque` | `append`/`popleft` keep arrival order and avoid routine overtaking |
| Staff-marked urgency | `heapq` | Priority 1 urgent, 2 elevated, 3 routine; lower means higher priority |

Queue workflows are alternatives for the same session, not two dispatch channels to run concurrently. Priority entries contain `(priority, arrival_counter, item_id)`; ties preserve arrival order without comparing model objects. The internal heap is not assumed sorted. Empty queues return `None`; already-preparing/served requests and closed sessions are skipped when selecting. Dequeueing does not advance fulfillment; staff use `OrderItem.advance_status()` separately.

`pending_items`, `participating_diner_ids`, and `index_items` demonstrate list, set, and dictionary comprehensions. `sorted_preparation_items` uses a named key function; `sorted_diner_balances` uses a short lambda. Both use tuple keys with multiple fields. Display sets with `sorted()` when deterministic output matters.

| Changes an existing collection/state | Creates a new collection/view |
|---|---|
| `Order.add_item` / `remove_item` | `pending_items` |
| `OrderItem.associate_diner` / `remove_diner` | `participating_diner_ids` / `common_diner_ids` |
| Queue `enqueue` / `dequeue` | `index_items` / `group_pending_by_area` |
| `TableSession.pay` | `sorted_preparation_items` / `sorted_diner_balances` |
| `TableSession.close` | `local_pos_snapshot` |

## Local POS simulation

`local_pos_snapshot(session)` generates a fresh dictionary of orders, fulfillment and item-payment states, receipts, diner balances, and table totals. A new call reflects subsequent changes; an earlier snapshot stays unchanged. States include `unallocated`, `unpaid`, `partially_mock_paid`, and `mock_paid`.

Tabit is the future integration target. This view does not transmit data, run background synchronization, connect to restaurant computers, or call any payment service. The QR reference is a synthetic label; there is no scanner or visual UI in Stage 1.

## Python and current verification

Use Python 3.10 or later. The implementation uses only the standard library and concepts from course presentations 1–4. Run commands from the repository root. The package currently imports as a namespace package; the required `__init__.py` will be added during package setup.

A complete `python main.py` run is not available yet. This minimal synthetic smoke check can run now and demonstrates three FIFO insertions, three distinct priorities, tie handling, and empty queues:

```sh
python3 -B - <<'PY'
from bills_split.models import Restaurant, Table, FoodItem, Order, OrderItem
from bills_split.processing import PreparationQueue, PriorityPreparationQueue

restaurant = Restaurant(1, "Synthetic Bistro")
table = Table(1, 1, restaurant)
restaurant.add_table(table)
food = FoodItem(1, "Synthetic dish", 1000)
restaurant.add_menu_item(food)
session = table.open_session(1)
order = Order(1)
for item_id in (1, 2, 3, 4):
    order.add_item(OrderItem(item_id, food))
session.add_order(order)

fifo = PreparationQueue(session)
for item_id in (1, 2, 3):
    fifo.enqueue(item_id)
assert [fifo.dequeue().id for _ in range(3)] == [1, 2, 3]
assert fifo.dequeue() is None

urgent = PriorityPreparationQueue(session)
for item_id, priority in [(1, 3), (2, 1), (3, 2), (4, 1)]:
    urgent.enqueue(item_id, priority)
assert [urgent.dequeue().id for _ in range(4)] == [2, 4, 3, 1]
assert urgent.dequeue() is None
assert all(item.status == "ordered" for item in session.items)
print("Preparation queue checks passed.")
PY
```

Part B previously passed 79 ad hoc business and validation checks. The current revision passed 138 development checks under Python 3.13.7. Verification covers payment allocation totals, repeat checkout, item status after later orders, all tip options, queue ordering/ties/empty/stale cases, grouping, sorting, and independent local snapshots. These development checks do not replace the final `main.py` demonstration or later course-stage tests.

## Pending final documentation

After Part D, document the two independent iterators, generator exhaustion and recreation, three-stage lazy pipeline and partial consumption, and context-manager cleanup on exceptions. After data creation, document the AI-generated record schema, line-by-line loading, conversion to objects, and validation. Add final execution instructions and record the Git history required for submission.
