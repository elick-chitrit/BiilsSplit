"""Iterating over order items and producing kitchen requests lazily."""

from .models import OrderItem


def _order_item(item):
    # בודקת שהאיבר שקיבלנו הוא פריט הזמנה.
    if not isinstance(item, OrderItem):
        raise ValueError("Iteration requires order item objects.")
    return item


class OrderItemCollection:
    """Keep items in order and give each iterator its own position.

    Item objects are shared, so status changes remain visible.
    """

    def __init__(self, items):
        # מכינה את הנתונים ההתחלתיים של אוסף פריטי הזמנה.
        self._items = []
        seen = set()
        for item in items:
            _order_item(item)
            if item.id in seen:
                raise ValueError("Order item IDs must be unique in the collection.")
            self._items.append(item)
            seen.add(item.id)

    def __iter__(self):
        # יוצרת איטרטור חדש כדי שכל מעבר יתקדם בנפרד.
        return OrderItemIterator(self._items)

    def __len__(self):
        # מחזירה את מספר הפריטים באוסף.
        return len(self._items)

    def __repr__(self):
        # מחזירה פרטים על אוסף פריטי הזמנה שעוזרים לבדוק את מצב האובייקט.
        return f"OrderItemCollection(items={len(self)})"


class OrderItemIterator:
    """One pass over the items, with an independent position."""

    def __init__(self, items):
        # מכינה את הנתונים ההתחלתיים של מעבר על פריטי ההזמנה.
        self._items = items
        self._index = 0

    def __iter__(self):
        # מחזירה את אותו איטרטור כדי להמשיך מהמיקום הנוכחי.
        return self

    def __next__(self):
        # מחזירה את הפריט הבא ועוצרת עם StopIteration כשאין עוד פריטים.
        if self._index >= len(self._items):
            raise StopIteration
        item = self._items[self._index]
        self._index += 1
        return item


def pending_order_items(items):
    # מחזירה בהדרגה רק פריטים שעדיין לא הוגשו.
    """Yield items that have not been served."""
    for item in items:
        if _order_item(item).status != "served":
            yield item


def kitchen_request_pipeline(items):
    # בונה שלושה שלבים עצלים שמחזירים בקשות הכנה למטבח.
    """Filter pending kitchen items and return their ID and quantity.

    The three stages are lazy and do not create intermediate lists.
    """
    pending = (item for item in items if _order_item(item).status != "served")
    kitchen = (item for item in pending if item.preparation_area() == "kitchen")
    requests = ((item.id, item.quantity) for item in kitchen)
    return requests
