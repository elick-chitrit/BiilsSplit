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
    # מריצה פעולה לא תקינה ומראה שהיא נדחתה כמו שציפינו.
    """Show that an invalid action is rejected."""
    try:
        action()
    except ValueError as error:
        print(f"  PASS - Rejected {label}")
        print(f"         {error}")
    else:
        raise AssertionError(f"Expected rejection: {label}")


def trace_demo_items(items, visited):
    # רושמת באילו פריטים עברנו כדי להראות מתי הגנרטור באמת עובד.
    """Track which items the generator actually visits."""
    for item in items:
        visited.append(item.id)
        yield item


def show_section(number, title):
    # מדפיסה כותרת והפרדה ברורה בין חלקי הדמו.
    print("\n" + "=" * 68)
    print(f"{number}. {title}")
    print("=" * 68)


def show_menu(session):
    # מציגה את התפריט בטבלה עם מחיר וזמינות.
    print(f"  {'ID':<4} {'Menu item':<24} {'Price':>8}  {'Availability':<12}")
    print("  " + "-" * 52)
    for item in session.menu:
        availability = "Available" if item.available else "Unavailable"
        print(f"  {item.id:<4} {item.name:<24} {item.display_price:>8}  {availability:<12}")


def show_order(order):
    # מציגה את פריטי ההזמנה ואת הסועדים שמשתתפים בכל פריט.
    print(f"\n  {'Line':<4} {'Ordered item':<22} {'Qty':>3} {'Total':>8}  Shared by")
    print("  " + "-" * 64)
    for item in order.items:
        names = ", ".join(diner.name for diner in item.participants)
        print(f"  {item.id:<4} {item.menu_item.name:<22} {item.quantity:>3} {item.total_cents / 100:>8.2f}  {names}")


def show_balances(session):
    # מציגה לכל סועד את חלקו, התשלום והיתרה.
    print(f"\n  {'Diner':<14} {'Item share':>10} {'Paid':>10} {'Still owed':>10}")
    print("  " + "-" * 47)
    for diner in session.diners:
        subtotal = session.diner_subtotal_cents(diner.id)
        owed = session.diner_owed_cents(diner.id)
        paid = subtotal - owed
        print(f"  {diner.name:<14} {subtotal / 100:>10.2f} {paid / 100:>10.2f} {owed / 100:>10.2f}")
    print("  Item amounts exclude tips. Nonparticipants owe zero.")


def show_payments(session):
    # מציגה את קבלות המוקאפ, הטיפים והפריטים ששולמו בכל קבלה.
    print(f"\n  {'Receipt':<8} {'Diner':<12} {'Items':>8} {'Tip':>8} {'Total':>8}")
    print("  " + "-" * 48)
    for payment in session.payments:
        name = session.find_diner(payment.diner_id).name
        print(f"  {payment.id:<8} {name:<12} {payment.amount_cents / 100:>8.2f} {payment.tip_cents / 100:>8.2f} {payment.total_cents / 100:>8.2f}")
    print("\n  Paid item shares per receipt (line ID: cents):")
    for payment in session.payments:
        print(f"  Receipt {payment.id}: {payment.item_allocations}")


def show_pos_view(session):
    # מציגה את מצב השולחן והפריטים מתוך הסימולציה המקומית.
    snapshot = local_pos_snapshot(session)
    print(f"\n  Local POS view | Table {snapshot['table_id']} | {snapshot['session_status'].upper()}")
    print(f"  Mode: {snapshot['mode']} (Tabit target)")
    print(f"  {'Line':<4} {'Item':<22} {'Fulfillment':<12} {'Payment':<20}")
    print("  " + "-" * 61)
    for item in snapshot['items']:
        name = session.find_item(item['id']).menu_item.name
        print(f"  {item['id']:<4} {name:<22} {item['fulfillment_status']:<12} {item['payment_status']:<20}")
    print(f"\n  Item total:  {snapshot['total_cents'] / 100:>8.2f}")
    print(f"  Still owed:  {snapshot['outstanding_cents'] / 100:>8.2f}")
    print(f"  Tips:        {snapshot['tips_cents'] / 100:>8.2f}")


def main():
    # מריצה את הארוחה לדוגמה, מהתפריט ועד תשלום וסגירת השולחן.
    print("=" * 68)
    print("BillsSplit - Stage 1 local demonstration")
    print("Each diner pays only for the items they consumed or shared.")
    print("=" * 68)
    print("Synthetic menu and mock payments. QR and Tabit are simulated locally.")

    show_section(1, "Menu and table setup")
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
    show_menu(session)
    print(f"  Debug representation: {repository.find(1)!r}")
    print(f"  Missing valid menu ID returns: {repository.find(999)}")

    for diner_id, name in [(1, "Diner A"), (2, "Diner B"), (3, "Diner C"), (4, "Diner D")]:
        method = MockPaymentMethod(diner_id, diner_id)
        session.join(Diner.from_dict({"id": diner_id, "name": name}, method))

    show_section(2, "Orders, shared items, and validation")
    order = Order.from_dict({"id": 1})
    for item_id, menu_id in [(1, 1), (2, 13), (3, 2), (4, 12), (5, 14), (6, 3)]:
        order.add_item(OrderItem.from_dict({"id": item_id, "quantity": 1}, repository.find(menu_id)))
    session.add_order(order)
    participation = {1: [1, 2, 3], 2: [1], 3: [2, 3], 4: [1, 2], 5: [3], 6: [2]}
    for item_id, diner_ids in participation.items():
        for diner_id in diner_ids:
            session.associate_diner(item_id, diner_id)
    print(f"  {order}; participants in shared starter: {len(session.find_item(4))}")
    show_order(order)
    print("\n  Polymorphic preparation destinations:")
    for item_id, area in order.preparation_requests():
        print(f"  Line {item_id}: {area}")
    print("  Starter shares in cents:", [session.find_item(4).share_cents(session.find_diner(i)) for i in (1, 2)])
    show_balances(session)
    assert [session.diner_owed_cents(i) for i in (1, 2, 3, 4)] == [3251, 7800, 3750, 0]
    assert sum(session.diner_subtotal_cents(i) for i in (1, 2, 3, 4)) == session.total_cents
    print("\n  Validation examples (expected rejections):")
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

    show_section(3, "Collections, grouping, and sorting")
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

    show_section(4, "FIFO and priority preparation queues")
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
    show_section(5, "Independent iterators and lazy processing")
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

    show_section(6, "Context manager: normal and error cases")
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

    show_section(7, "Mock payments and tips")
    print("  Tip options:", MockPayment.TIP_OPTIONS)
    print("  Percentage tips on 10.00:", {rate: MockPayment.calculate_tip(1000, rate) for rate in (10, 12, 15, 20)})
    for payment_id, diner_id, choice, manual in [(1, 1, 10, None), (2, 2, "Other", 500), (3, 3, "None", None)]:
        session.pay(payment_id, diner_id, choice, manual)
    show_payments(session)
    assert session.outstanding_cents == 0
    expected_rejection("changing paid participation", lambda: session.find_item(1).remove_diner(session.find_diner(1)))

    show_section(8, "Later order and final table state")
    later = Order(2)
    later.add_item(OrderItem(7, repository.find(15)))
    session.add_order(later)
    session.associate_diner(7, 1)
    assert session.item_payment_status(2) == "mock_paid"
    assert session.item_payment_status(7) == "unpaid"
    print("  Earlier personal drink:", session.item_payment_status(2))
    print("  New drink:", session.item_payment_status(7))
    later_payment = session.pay(4, 1, 12)
    print(f"  New mock payment recorded: receipt {later_payment.id}")
    show_payments(session)
    show_balances(session)
    assert session.diner_owed_cents(4) == 0
    expected_rejection("closing a paid table before all items are served", session.close)
    assert session.status == "open" and table.active_session is session
    for item in session.items:
        while item.status != "served":
            item.advance_status()
    session.close()
    show_pos_view(session)
    assert session.outstanding_cents == 0 and session.total_cents == 16501
    assert session.tips_cents == 1029 and table.active_session is None
    print("\n" + "=" * 68)
    print("DEMO COMPLETE")
    print("=" * 68)
    print(f"  Table state:      {session.status.upper()}")
    print(f"  Total item bill:  {session.total_cents / 100:>8.2f}")
    print(f"  Unpaid items:     {session.outstanding_cents / 100:>8.2f}")
    print(f"  Mock tips:        {session.tips_cents / 100:>8.2f}")
    print("  Diner D consumed no items and was never charged.")


if __name__ == "__main__":
    main()
