"""Reserve limited menu stock before creating orders in the main thread."""

from threading import Thread, Lock

from .models import MenuItem, _integer


class MenuStock:
    def __init__(self, item, quantity):
        # מכינה מלאי משותף לפריט אחד בתפריט.
        if not isinstance(item, MenuItem):
            raise ValueError("Stock requires a menu item.")
        self.item = item
        self._remaining = _integer(quantity, "Stock quantity", 0)
        self._reserved_diners = set()
        self._lock = Lock()

    @property
    def remaining(self):
        # מחזירה כמה מנות נשארו במלאי.
        with self._lock:
            return self._remaining

    def reserve(self, diner_id):
        # שומרת מנה רק אם עוד יש מלאי.
        _integer(diner_id, "Diner ID")
        with self._lock:
            if diner_id in self._reserved_diners or not self.item.available or self._remaining == 0:
                return False
            self._remaining -= 1
            self._reserved_diners.add(diner_id)
            return True


class ReservationThread(Thread):
    def __init__(self, stock, diner_id):
        # מחברת בקשת סועד לאותו מלאי משותף.
        super().__init__()
        self.stock = stock
        self.diner_id = diner_id
        self.approved = None

    def run(self):
        # מנסה לשמור מנה עבור הסועד.
        self.approved = self.stock.reserve(self.diner_id)


def reserve_for_diners(stock, diner_ids):
    # מפעילה את הבקשות ורק אז ממתינה לתוצאות.
    diner_ids = list(diner_ids)
    for diner_id in diner_ids:
        _integer(diner_id, "Diner ID")
    threads = [ReservationThread(stock, diner_id) for diner_id in diner_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return [{"diner_id": thread.diner_id, "approved": thread.approved} for thread in threads]
