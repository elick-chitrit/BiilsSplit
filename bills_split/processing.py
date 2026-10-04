"""Lists, groups, queues, and the local table view.

The queues are two alternatives for handling a session's preparation work.
Selecting a request does not mean the item has been prepared or served.
"""

from collections import deque
import heapq

from .models import TableSession


def _session(session):
    # בודקת שקיבלנו אובייקט של ארוחה בשולחן.
    if not isinstance(session, TableSession):
        raise ValueError("A table session is required.")
    return session


def pending_items(session):
    # מחזירה רשימה חדשה של הפריטים שעדיין לא הוגשו.
    """Get the items that have not been served."""
    _session(session)
    return [item for item in session.items if item.status != "served"]


def preparation_records(session):
    # יוצרת רשומות הכנה לפריטים שטרם הוגשו.
    """Preparation records: ID, area, quantity, and status."""
    return [(item.id, item.preparation_area(), item.quantity, item.status)
            for item in pending_items(session)]


def describe_preparation_record(record):
    # מפרקת את רשומת ההכנה ומחזירה שורה קריאה להצגה.
    """Turn a preparation record into a readable line."""
    if not isinstance(record, tuple) or len(record) != 4:
        raise ValueError("A preparation record requires four tuple fields.")
    item_id, area, *details = record
    quantity, status = details
    return f"Item {item_id} -> {area}: quantity {quantity}, status {status}"


def participating_diner_ids(session):
    # אוספת את מזהי המשתתפים בפריטים בלי כפילויות.
    _session(session)
    return {diner.id for item in session.items for diner in item.participants}


def diners_without_items(session):
    # מוצאת מי הצטרף לארוחה אבל לא השתתף באף פריט.
    """Find diners who did not participate in any items."""
    _session(session)
    joined = set()
    for diner in session.diners:
        joined.add(diner.id)
    return joined - participating_diner_ids(session)


def common_diner_ids(first_item, second_item):
    # מוצאת אילו סועדים משתתפים בשני הפריטים.
    first = {diner.id for diner in first_item.participants}
    second = {diner.id for diner in second_item.participants}
    return first & second


def index_items(session):
    # בונה מילון של פריטים לפי מזהה ובודקת שאין כפילויות.
    """Index items by ID without replacing duplicates."""
    _session(session)
    items = session.items
    seen = set()
    for item in items:
        if item.id in seen:
            raise ValueError("Cannot index duplicate order item IDs.")
        seen.add(item.id)
    return {item.id: item for item in items}


def group_pending_by_area(session):
    # מקבצת את הפריטים שטרם הוגשו לפי יעד ההכנה שלהם.
    groups = {}
    for item in pending_items(session):
        area = item.preparation_area()
        group = groups.get(area)
        if group is None:
            group = []
            groups[area] = group
        group.append(item)
    return groups


def area_workload(session):
    # סופרת כמה יחידות טרם הוגשו בכל יעד הכנה.
    """Count how many units each preparation area needs to handle."""
    counts = {}
    for area, items in group_pending_by_area(session).items():
        counts[area] = sum(item.quantity for item in items)
    return counts


def preparation_sort_key(item):
    # מגדירה סדר מיון לפי יעד הכנה, מצב ואז מזהה.
    """Sort by area, status, and ID."""
    status_rank = {"ordered": 0, "preparing": 1, "served": 2}
    return (item.preparation_area(), status_rank[item.status], item.id)


def sorted_preparation_items(session):
    # מחזירה את הפריטים הממתינים ממוינים לפי מפתח ההכנה.
    return sorted(pending_items(session), key=preparation_sort_key)


def sorted_diner_balances(session):
    # ממיינת סועדים לפי יתרה מהגבוהה לנמוכה, ואז לפי מזהה.
    """Sort by amount owed, then diner ID."""
    _session(session)
    balances = [(diner.id, session.diner_owed_cents(diner.id))
                for diner in session.diners]
    return sorted(balances, key=lambda row: (-row[1], row[0]))


class PreparationQueue:
    """Handle routine requests in arrival order."""

    def __init__(self, session):
        # מכינה את הנתונים ההתחלתיים של תור הכנה לפי סדר הגעה.
        self._session = _session(session)
        self._queue = deque()
        self._pending_ids = set()

    def enqueue(self, item_id):
        # מוסיפה בקשת הכנה לסוף התור בלי להוסיף אותה פעמיים.
        self._session._require_open()
        item = self._session.find_item(item_id)
        if item.status != "ordered":
            raise ValueError("Only items awaiting preparation can be queued.")
        if item.id in self._pending_ids:
            raise ValueError("This preparation request is already queued.")
        self._queue.append(item.id)
        self._pending_ids.add(item.id)

    def dequeue(self):
        # Skip requests whose status has already changed.
        # מוציאה את הבקשה התקפה הראשונה לפי סדר הגעה.
        while self._queue:
            item_id = self._queue.popleft()
            self._pending_ids.discard(item_id)
            item = self._session.find_item(item_id)
            if self._session.status == "open" and item.status == "ordered":
                return item
        return None

    def __len__(self):
        # מחזירה את מספר הרשומות שעדיין בתור.
        return len(self._queue)


class PriorityPreparationQueue:
    """Preparation priority: 1 urgent, 2 elevated, 3 routine.

    Arrival order breaks ties. Use heappop to select the next request;
    the heap itself is not a sorted list.
    """

    def __init__(self, session):
        # מכינה את הנתונים ההתחלתיים של תור הכנה לפי עדיפות.
        self._session = _session(session)
        self._heap = []
        self._pending_ids = set()
        self._arrival = 0

    def enqueue(self, item_id, priority=3):
        # מוסיפה בקשה לפי עדיפות, עם סדר הגעה לשבירת שוויון.
        self._session._require_open()
        if (not isinstance(priority, int) or isinstance(priority, bool)
                or priority not in (1, 2, 3)):
            raise ValueError("Preparation priority must be 1, 2, or 3.")
        item = self._session.find_item(item_id)
        if item.status != "ordered":
            raise ValueError("Only items awaiting preparation can be queued.")
        if item.id in self._pending_ids:
            raise ValueError("This preparation request is already queued.")
        heapq.heappush(self._heap, (priority, self._arrival, item.id))
        self._pending_ids.add(item.id)
        self._arrival += 1

    def dequeue(self):
        # מוציאה את הבקשה התקפה הדחופה ביותר ומדלגת על בקשות ישנות.
        while self._heap:
            priority, arrival, item_id = heapq.heappop(self._heap)
            self._pending_ids.discard(item_id)
            item = self._session.find_item(item_id)
            if self._session.status == "open" and item.status == "ordered":
                return item
        return None

    def __len__(self):
        # מחזירה את מספר הרשומות שעדיין בתור העדיפויות.
        return len(self._heap)


def local_pos_snapshot(session):
    # בונה תמונת מצב מקומית של השולחן, בלי לשלוח מידע ל-Tabit.
    """Get the current table state in a local POS view.

    Call again after a change to get a new snapshot. No data is sent to Tabit.
    """
    _session(session)
    return {
        "integration_target": "Tabit",
        "mode": "local_simulation",
        "restaurant_id": session.table.restaurant.id,
        "table_id": session.table.id,
        "session_id": session.id,
        "session_status": session.status,
        "orders": [{"id": order.id, "status": order.status}
                   for order in session.orders],
        "items": [{"id": item.id, "menu_item_id": item.menu_item.id,
                   "quantity": item.quantity, "total_cents": item.total_cents,
                   "fulfillment_status": item.status,
                   "payment_status": session.item_payment_status(item.id),
                   "paid_cents": session.item_paid_cents(item.id),
                   "participant_ids": [diner.id for diner in item.participants]}
                  for item in session.items],
        "payments": [{"id": payment.id, "diner_id": payment.diner_id,
                      "status": payment.status,
                      "item_allocations": payment.item_allocations,
                      "amount_cents": payment.amount_cents,
                      "tip_cents": payment.tip_cents}
                     for payment in session.payments],
        "diner_balances": sorted_diner_balances(session),
        "total_cents": session.total_cents,
        "outstanding_cents": session.outstanding_cents,
        "tips_cents": session.tips_cents,
    }
