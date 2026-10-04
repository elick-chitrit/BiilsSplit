"""Run the BillsSplit demo from the project root: python3 main.py.

The business logic stays in bills_split; this file runs the example meal.
"""

from bills_split.models import Restaurant, Table, Diner, MockPaymentMethod, Order, OrderItem, MockPayment
from bills_split.repository import MenuRepository
from bills_split.processing import (
    preparation_records, describe_preparation_record, participating_diner_ids,
    diners_without_items, common_diner_ids, index_items, group_pending_by_area,
    area_workload, sorted_preparation_items, sorted_diner_balances,
    PreparationQueue, PriorityPreparationQueue, local_pos_snapshot,
)
from bills_split.iterators import OrderItemCollection, pending_order_items, kitchen_request_pipeline
from bills_split.context_managers import OperationTimer


def expected_rejection(label, action):
    """Show that an invalid action is rejected."""
    try:
        action()
    except ValueError as error:
        print(f"  Rejected {label}: {error}")
    else:
        raise AssertionError(f"Expected rejection: {label}")


def trace_demo_items(items, visited):
    """Track which items the generator actually visits."""
    for item in items:
        visited.append(item.id)
        yield item


def show_balances(session):
    for diner in session.diners:
        amount = session.diner_owed_cents(diner.id)
        print(f"  {diner.name}: {amount / 100:.2f}")


def show_pos_view(session):
    snapshot = local_pos_snapshot(session)
    print(f"  Local POS view: {snapshot['mode']}, table {snapshot['table_id']}, {snapshot['session_status']}")
    for item in snapshot['items']:
        print(f"  Item {item['id']}: {item['fulfillment_status']}, {item['payment_status']}")
    print(f"  Outstanding: {snapshot['outstanding_cents'] / 100:.2f}; tips: {snapshot['tips_cents'] / 100:.2f}")


def main():
    print("BillsSplit - Stage 1 local demonstration")
    print("Synthetic data and payments; no real QR scanner, Tabit connection, or payment API.\n")

    print("1. Load the synthetic menu and open a table")
    with OperationTimer("load restaurant menu") as load_timer:
        repository = MenuRepository.from_jsonl("data/sample_data.jsonl")
    print(f"  Loaded {len(repository)} validated menu items; timer completed: {load_timer.completed}")
    restaurant = Restaurant.from_dict({"id": 1, "name": "Synthetic Bistro"})
    for item in repository.items:
        restaurant.add_menu_item(item)
    table = Table.from_dict({"id": 1, "number": 1}, restaurant)
    restaurant.add_table(table)
    session = table.open_session(1)
    print(f"  {table}; join reference: {table.qr_label}")
    for item in session.menu:
        print(f"  {item} ({'available' if item.available else 'unavailable'})")
    print(f"  Debug representation: {repository.find(1)!r}")
    print(f"  Missing valid menu ID returns: {repository.find(999)}")

    for diner_id, name in [(1, "Diner A"), (2, "Diner B"), (3, "Diner C"), (4, "Diner D")]:
        method = MockPaymentMethod(diner_id, diner_id)
        session.join(Diner.from_dict({"id": diner_id, "name": name}, method))

    print("\n2. Place an order, allocate only consumed items, and validate inputs")
    order = Order.from_dict({"id": 1})
    for item_id, menu_id in [(1, 1), (2, 13), (3, 2), (4, 12), (5, 14), (6, 3)]:
        order.add_item(OrderItem.from_dict({"id": item_id, "quantity": 1}, repository.find(menu_id)))
    session.add_order(order)
    participation = {1: [1, 2, 3], 2: [1], 3: [2, 3], 4: [1, 2], 5: [3], 6: [2]}
    for item_id, diner_ids in participation.items():
        for diner_id in diner_ids:
            session.associate_diner(item_id, diner_id)
    print(f"  {order}; participants in shared starter: {len(session.find_item(4))}")
    print(f"  Polymorphic preparation destinations: {order.preparation_requests()}")
    print("  Starter shares in cents:", [session.find_item(4).share_cents(session.find_diner(i)) for i in (1, 2)])
    show_balances(session)
    assert [session.diner_owed_cents(i) for i in (1, 2, 3, 4)] == [3251, 7800, 3750, 0]
    assert sum(session.diner_subtotal_cents(i) for i in (1, 2, 3, 4)) == session.total_cents
    original_price = repository.find(1).price_cents
    expected_rejection("a zero menu price", lambda: setattr(repository.find(1), "price_cents", 0))
    assert repository.find(1).price_cents == original_price
    expected_rejection("zero quantity", lambda: OrderItem(99, repository.find(1), 0))
    expected_rejection("an unavailable item", lambda: OrderItem(99, repository.find(11)))
    expected_rejection("duplicate participation", lambda: session.associate_diner(1, 1))
    expected_rejection("a boolean diner ID", lambda: session.associate_diner(1, True))
    expected_rejection("a floating-point item ID", lambda: session.find_item(1.0))
    expected_rejection("an invalid payment diner ID", lambda: session.pay(99, True))
    assert not session.payments and not session.find_item(1).locked
    expected_rejection("duplicate menu ID", lambda: repository.add(repository.find(1)))
    expected_rejection("closure before settlement", session.close)

    print("\n3. Collections, grouping, and sorting")
    indexed = index_items(session)
    print(f"  Indexed line 2: {indexed[2]}; missing ID: {indexed.get(999)}")
    for area, items in group_pending_by_area(session).items():
        print(f"  {area} line IDs: {[item.id for item in items]}")
    print("  Workload:", area_workload(session))
    print("  Unique participants:", sorted(participating_diner_ids(session)))
    print("  Diners without items:", sorted(diners_without_items(session)))
    print("  Participants common to pizza and salad:", sorted(common_diner_ids(session.find_item(1), session.find_item(3))))
    print("  Tuple unpacking:", describe_preparation_record(preparation_records(session)[0]))
    print("  Named-key preparation sort:", [item.id for item in sorted_preparation_items(session)])
    print("  Lambda balance sort:", sorted_diner_balances(session))

    print("\n4. Alternative FIFO and priority preparation workflows")
    fifo = PreparationQueue(session)
    for item_id in (2, 3, 4):
        fifo.enqueue(item_id)
    fifo_ids = [fifo.dequeue().id for _ in range(3)]
    print(f"  FIFO selections: {fifo_ids}; empty result: {fifo.dequeue()}")
    assert fifo_ids == [2, 3, 4]
    priority = PriorityPreparationQueue(session)
    for item_id, urgency in [(2, 3), (3, 1), (4, 2), (5, 1)]:
        priority.enqueue(item_id, urgency)
    priority_ids = [priority.dequeue().id for _ in range(4)]
    print(f"  Priority selections (1 highest): {priority_ids}; empty result: {priority.dequeue()}")
    assert priority_ids == [3, 5, 4, 2]
    print("  Selection leaves fulfillment unchanged:", [item.status for item in session.items])

    # Serve one item so the generator can skip it.
    session.find_item(1).advance_status()
    session.find_item(1).advance_status()
    print("\n5. Independent iterators, yield, and lazy pipeline")
    collection = OrderItemCollection(session.items)
    first, second = iter(collection), iter(collection)
    print(f"  First iterator: {next(first).id}, {next(first).id}; second: {next(second).id}")
    print("  First remaining:", [item.id for item in first])
    print(f"  Second continues independently: {next(second).id}")
    try:
        next(first)
    except StopIteration:
        print("  First iterator raises StopIteration after exhaustion.")
    visited = []
    generator = pending_order_items(trace_demo_items(collection, visited))
    print("  Source inspected at generator creation:", visited)
    print("  First yielded pending line:", next(generator).id)
    remaining = []
    for item in generator:
        remaining.append(item.id)
    print("  Continued with for:", remaining)
    print("  Exhausted generator:", list(generator))
    print("  Fresh generator:", [item.id for item in pending_order_items(collection)])
    visited = []
    pipeline = kitchen_request_pipeline(trace_demo_items(collection, visited))
    assert visited == []
    requests = (next(pipeline), next(pipeline))
    print("  Only two pipeline results:", requests)
    print("  Inspected source IDs:", visited, "; unprocessed IDs: [5, 6]")
    assert requests == ((3, 1), (4, 1)) and visited == [1, 2, 3, 4]

    print("\n6. Normal and failing context-manager exit")
    with OperationTimer("calculate local table view") as view_timer:
        show_pos_view(session)
    print(f"  Normal exit completed: {view_timer.completed}; failed: {view_timer.failed}")
    failed_timer = OperationTimer("invalid synthetic checkout")
    try:
        with failed_timer as measured:
            session.pay(99, 1, "Other", -1)
    except ValueError as error:
        print(f"  Payment error propagated: {error}")
    else:
        raise AssertionError("Expected the invalid tip to propagate.")
    assert failed_timer.completed and failed_timer.failed and failed_timer.duration_seconds >= 0
    assert not session.payments
    print(f"  Exceptional exit completed: {failed_timer.completed}; failed: {failed_timer.failed}")

    print("\n7. Settle shares with mock cards and optional tips")
    print("  Tip options:", MockPayment.TIP_OPTIONS)
    print("  Percentage tips on 10.00:", {rate: MockPayment.calculate_tip(1000, rate) for rate in (10, 12, 15, 20)})
    for payment_id, diner_id, choice, manual in [(1, 1, 10, None), (2, 2, "Other", 500), (3, 3, "None", None)]:
        payment = session.pay(payment_id, diner_id, choice, manual)
        print(f"  {payment}; settled item cents: {payment.item_allocations}")
    assert session.outstanding_cents == 0
    expected_rejection("changing paid participation", lambda: session.find_item(1).remove_diner(session.find_diner(1)))

    print("\n8. Add a later order and preserve earlier paid items")
    later = Order(2)
    later.add_item(OrderItem(7, repository.find(15)))
    session.add_order(later)
    session.associate_diner(7, 1)
    assert session.item_payment_status(2) == "mock_paid"
    assert session.item_payment_status(7) == "unpaid"
    print("  Earlier personal drink:", session.item_payment_status(2))
    print("  New drink:", session.item_payment_status(7))
    print("  Later receipt:", session.pay(4, 1, 12))
    show_balances(session)
    assert session.diner_owed_cents(4) == 0
    for item in session.items:
        while item.status != "served":
            item.advance_status()
    session.close()
    show_pos_view(session)
    assert session.outstanding_cents == 0 and session.total_cents == 16501
    assert session.tips_cents == 1029 and table.active_session is None
    print("\nDemonstration complete: table closed, item balance 0.00, synthetic tips 10.29.")


if __name__ == "__main__":
    main()
