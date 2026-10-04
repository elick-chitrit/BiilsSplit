"""Restaurant, table, order, and mock payment models.

Money is stored in cents. State changes go through the model's methods.
The QR reference, POS state, and payments are local mock data.
"""


def _integer(value, field, minimum=1):
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{field} must be an integer of at least {minimum}.")
    return value


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text.")
    return value.strip()


def _record(data, fields):
    if not isinstance(data, dict):
        raise ValueError("An alternative constructor requires a dictionary.")
    for field in fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}.")


class MenuItem:
    """A menu item with a price and availability."""

    def __init__(self, item_id, name, price_cents, available=True):
        self._id = _integer(item_id, "Menu item ID")
        self._name = _text(name, "Menu item name")
        self.price_cents = price_cents
        self.set_availability(available)

    @classmethod
    def from_dict(cls, data):
        _record(data, ("id", "name", "price_cents"))
        return cls(data["id"], data["name"], data["price_cents"],
                   data.get("available", True))

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def price_cents(self):
        return self._price_cents

    @price_cents.setter
    def price_cents(self, value):
        self._price_cents = _integer(value, "Menu price")

    @property
    def display_price(self):
        return f"{self.price_cents / 100:.2f}"

    @property
    def available(self):
        return self._available

    def set_availability(self, available):
        if not isinstance(available, bool):
            raise ValueError("Availability must be True or False.")
        self._available = available

    def preparation_area(self):
        return "service"

    def __str__(self):
        return f"{self.name}: {self.display_price}"

    def __repr__(self):
        return (f"{type(self).__name__}(id={self.id}, name={self.name!r}, "
                f"price_cents={self.price_cents}, available={self.available})")


class FoodItem(MenuItem):
    """Food is prepared in the kitchen."""

    def preparation_area(self):
        return "kitchen"


class DrinkItem(MenuItem):
    """Drinks are prepared at the bar."""

    def preparation_area(self):
        return "bar"


class Restaurant:
    """The restaurant menu and physical tables."""

    def __init__(self, restaurant_id, name):
        self._id = _integer(restaurant_id, "Restaurant ID")
        self._name = _text(name, "Restaurant name")
        self._menu = {}
        self._tables = {}

    @classmethod
    def from_dict(cls, data):
        _record(data, ("id", "name"))
        return cls(data["id"], data["name"])

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def menu(self):
        return list(self._menu.values())

    @property
    def tables(self):
        return list(self._tables.values())

    def add_menu_item(self, item):
        if not isinstance(item, MenuItem):
            raise ValueError("The menu accepts only menu items.")
        if item.id in self._menu:
            raise ValueError("Menu item ID already exists.")
        self._menu[item.id] = item

    def find_menu_item(self, item_id):
        _integer(item_id, "Menu item ID")
        item = self._menu.get(item_id)
        if item is None:
            raise ValueError("Menu item does not exist in this restaurant.")
        return item

    def add_table(self, table):
        if not isinstance(table, Table) or table.restaurant is not self:
            raise ValueError("The table must belong to this restaurant.")
        if table.id in self._tables:
            raise ValueError("Table ID already exists.")
        for existing in self.tables:
            if existing.number == table.number:
                raise ValueError("Table number already exists.")
        self._tables[table.id] = table

    def find_table(self, table_id):
        _integer(table_id, "Table ID")
        table = self._tables.get(table_id)
        if table is None:
            raise ValueError("Table does not exist in this restaurant.")
        return table

    def __len__(self):
        return len(self._menu)

    def __str__(self):
        return f"{self.name}: {len(self)} menu items, {len(self._tables)} tables"

    def __repr__(self):
        return f"Restaurant(id={self.id}, name={self.name!r})"


class Table:
    """A physical table, separate from the meal taking place at it."""

    def __init__(self, table_id, number, restaurant):
        if not isinstance(restaurant, Restaurant):
            raise ValueError("A table requires a restaurant.")
        self._id = _integer(table_id, "Table ID")
        self._number = _integer(number, "Table number")
        self._restaurant = restaurant
        self._active_session = None

    @classmethod
    def from_dict(cls, data, restaurant):
        _record(data, ("id", "number"))
        return cls(data["id"], data["number"], restaurant)

    @property
    def id(self):
        return self._id

    @property
    def number(self):
        return self._number

    @property
    def restaurant(self):
        return self._restaurant

    @property
    def qr_label(self):
        return f"MOCK-TABLE-{self.restaurant.id}-{self.id}"

    @property
    def active_session(self):
        return self._active_session

    def open_session(self, session_id):
        return TableSession(session_id, self)

    def __str__(self):
        return f"Table {self.number} at {self.restaurant.name}"

    def __repr__(self):
        return f"Table(id={self.id}, number={self.number}, restaurant_id={self.restaurant.id})"


class MockPaymentMethod:
    """A mock card label with no real card details."""

    def __init__(self, method_id, diner_id):
        self._id = _integer(method_id, "Mock payment method ID")
        self._diner_id = _integer(diner_id, "Payment method owner ID")
        self._active = True

    @classmethod
    def from_dict(cls, data):
        _record(data, ("id", "diner_id"))
        return cls(data["id"], data["diner_id"])

    @property
    def id(self):
        return self._id

    @property
    def diner_id(self):
        return self._diner_id

    @property
    def active(self):
        return self._active

    @property
    def synthetic_card_label(self):
        return f"MOCK-CARD-{self.id}"

    def deactivate(self):
        self._active = False

    def __str__(self):
        return f"{self.synthetic_card_label} ({'active' if self.active else 'inactive'})"

    def __repr__(self):
        return f"MockPaymentMethod(id={self.id}, diner_id={self.diner_id}, active={self.active})"


class Diner:
    """A diner and their optional mock payment method."""

    def __init__(self, diner_id, name, payment_method=None):
        self._id = _integer(diner_id, "Diner ID")
        self._name = _text(name, "Diner name")
        self._payment_method = None
        if payment_method is not None:
            self.set_payment_method(payment_method)

    @classmethod
    def from_dict(cls, data, payment_method=None):
        _record(data, ("id", "name"))
        return cls(data["id"], data["name"], payment_method)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def payment_method(self):
        return self._payment_method

    @property
    def has_active_payment_method(self):
        return self.payment_method is not None and self.payment_method.active

    def set_payment_method(self, method):
        if not isinstance(method, MockPaymentMethod) or method.diner_id != self.id:
            raise ValueError("The mock payment method must belong to this diner.")
        self._payment_method = method

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Diner(id={self.id}, name={self.name!r})"


class OrderItem:
    """An ordered item and the diners who consumed it."""

    def __init__(self, item_id, menu_item, quantity=1):
        if not isinstance(menu_item, MenuItem) or not menu_item.available:
            raise ValueError("An order item requires an available menu item.")
        self._id = _integer(item_id, "Order item ID")
        self._quantity = _integer(quantity, "Order quantity")
        self._menu_item = menu_item
        self._unit_price_cents = menu_item.price_cents
        self._participants = []
        self._session = None
        self._order = None
        self._locked = False
        self._status = "ordered"

    @classmethod
    def from_dict(cls, data, menu_item):
        _record(data, ("id", "quantity"))
        return cls(data["id"], menu_item, data["quantity"])

    @property
    def id(self):
        return self._id

    @property
    def menu_item(self):
        return self._menu_item

    @property
    def quantity(self):
        return self._quantity

    @property
    def unit_price_cents(self):
        return self._unit_price_cents

    @property
    def total_cents(self):
        return self.unit_price_cents * self.quantity

    @property
    def participants(self):
        return list(self._participants)

    @property
    def locked(self):
        return self._locked

    @property
    def status(self):
        return self._status

    def _require_open_session(self):
        if self._session is None or self._session.status != "open":
            raise ValueError("The item must belong to an open table session.")

    def associate_diner(self, diner):
        self._require_open_session()
        self._session._require_member(diner)
        if self.locked:
            raise ValueError("Participation cannot change after an item share is paid.")
        if diner in self._participants:
            raise ValueError("The diner is already associated with this item.")
        self._participants.append(diner)

    def remove_diner(self, diner):
        self._require_open_session()
        self._session._require_member(diner)
        if self.locked:
            raise ValueError("Participation cannot change after an item share is paid.")
        if diner not in self._participants:
            raise ValueError("The diner is not associated with this item.")
        self._participants.remove(diner)

    def share_cents(self, diner):
        if diner not in self._participants:
            return 0
        # Give leftover cents in participation order so the total stays exact.
        count = len(self._participants)
        share = self.total_cents // count
        remainder = self.total_cents % count
        if self._participants.index(diner) < remainder:
            share += 1
        return share

    def advance_status(self):
        self._require_open_session()
        next_status = {"ordered": "preparing", "preparing": "served"}
        if self.status not in next_status:
            raise ValueError("A served item has no further fulfillment step.")
        self._status = next_status[self.status]

    def preparation_area(self):
        # Food and drinks choose their own preparation area.
        return self.menu_item.preparation_area()

    def __len__(self):
        return len(self._participants)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}: {self.total_cents / 100:.2f} ({self.status})"

    def __repr__(self):
        return f"OrderItem(id={self.id}, menu_item_id={self.menu_item.id}, quantity={self.quantity})"


class Order:
    """Order lines can change until the order is submitted."""

    def __init__(self, order_id):
        self._id = _integer(order_id, "Order ID")
        self._items = {}
        self._session = None

    @classmethod
    def from_dict(cls, data):
        _record(data, ("id",))
        return cls(data["id"])

    @property
    def id(self):
        return self._id

    @property
    def items(self):
        return list(self._items.values())

    @property
    def total_cents(self):
        return sum(item.total_cents for item in self.items)

    @property
    def status(self):
        if self._session is None:
            return "draft"
        if all(item.status == "served" for item in self.items):
            return "served"
        if all(item.status == "ordered" for item in self.items):
            return "ordered"
        return "in_progress"

    def add_item(self, item):
        if self._session is not None:
            raise ValueError("Submitted orders cannot gain or lose items; place a new order.")
        if not isinstance(item, OrderItem) or item._order is not None:
            raise ValueError("The item must be an unassigned order item.")
        if item.id in self._items:
            raise ValueError("Order item ID already exists.")
        self._items[item.id] = item
        item._order = self

    def find_item(self, item_id):
        _integer(item_id, "Order item ID")
        item = self._items.get(item_id)
        if item is None:
            raise ValueError("Order item does not exist in this order.")
        return item

    def remove_item(self, item_id):
        if self._session is not None:
            raise ValueError("Items cannot be removed from a submitted order.")
        item = self.find_item(item_id)
        del self._items[item_id]
        item._order = None
        return item

    def preparation_requests(self):
        return [(item.id, item.preparation_area()) for item in self.items]

    def __len__(self):
        return len(self._items)

    def __str__(self):
        return f"Order {self.id}: {len(self)} items, {self.total_cents / 100:.2f} ({self.status})"

    def __repr__(self):
        return f"Order(id={self.id}, items={len(self)}, status={self.status!r})"


class MockPayment:
    """A mock receipt showing which item shares were paid.

    TableSession.pay records the payment. Creating a receipt on its own
    does not settle a session.
    """

    TIP_OPTIONS = (10, 12, 15, 20, "Other", "None")

    def __init__(self, payment_id, session_id, diner_id, method_id,
                 amount_cents, item_allocations, tip_cents=0):
        self._id = _integer(payment_id, "Mock payment ID")
        self._session_id = _integer(session_id, "Payment session ID")
        self._diner_id = _integer(diner_id, "Payment diner ID")
        self._method_id = _integer(method_id, "Mock payment method ID")
        self._amount_cents = _integer(amount_cents, "Payment amount")
        self._tip_cents = _integer(tip_cents, "Tip amount", 0)
        if not isinstance(item_allocations, dict) or not item_allocations:
            raise ValueError("A mock payment requires its paid item shares.")
        allocations = {}
        for item_id, share in item_allocations.items():
            _integer(item_id, "Paid order item ID")
            allocations[item_id] = _integer(share, "Paid item share")
        if sum(allocations.values()) != self.amount_cents:
            raise ValueError("Paid item shares must sum to the payment amount, excluding tip.")
        self._item_allocations = allocations

    @classmethod
    def from_dict(cls, data):
        _record(data, ("id", "session_id", "diner_id", "method_id", "amount_cents", "item_allocations"))
        return cls(data["id"], data["session_id"], data["diner_id"],
                   data["method_id"], data["amount_cents"], data["item_allocations"],
                   data.get("tip_cents", 0))

    @staticmethod
    def calculate_tip(amount_cents, option="None", manual_tip_cents=None):
        _integer(amount_cents, "Tip base", 0)
        if option == "Other":
            return _integer(manual_tip_cents, "Manual tip", 0)
        if manual_tip_cents is not None:
            raise ValueError("A manual amount is accepted only with Other.")
        if option == "None":
            return 0
        _integer(option, "Tip percentage")
        if option not in (10, 12, 15, 20):
            raise ValueError("Choose 10, 12, 15, 20, Other, or None.")
        # Round the tip to a cent, with halves rounded up.
        return (amount_cents * option + 50) // 100

    @property
    def id(self):
        return self._id

    @property
    def session_id(self):
        return self._session_id

    @property
    def diner_id(self):
        return self._diner_id

    @property
    def method_id(self):
        return self._method_id

    @property
    def item_allocations(self):
        return dict(self._item_allocations)

    @property
    def amount_cents(self):
        return self._amount_cents

    @property
    def tip_cents(self):
        return self._tip_cents

    @property
    def total_cents(self):
        return self.amount_cents + self.tip_cents

    @property
    def status(self):
        return "mock_paid"

    def __str__(self):
        return f"Mock payment {self.id}: {self.total_cents / 100:.2f}, including tip {self.tip_cents / 100:.2f}"

    def __repr__(self):
        return (f"MockPayment(id={self.id}, session_id={self.session_id}, "
                f"diner_id={self.diner_id}, amount_cents={self.amount_cents}, tip_cents={self.tip_cents})")


class TableSession:
    """One meal at a table, including diners, orders, and payments."""

    def __init__(self, session_id, table):
        session_id = _integer(session_id, "Session ID")
        if not isinstance(table, Table):
            raise ValueError("A session requires a restaurant table.")
        if table.restaurant.find_table(table.id) is not table:
            raise ValueError("The table must be registered with its restaurant.")
        if table.active_session is not None:
            raise ValueError("This table already has an active session.")
        self._id = session_id
        self._table = table
        self._diners = {}
        self._orders = {}
        self._payments = {}
        self._status = "open"
        table._active_session = self

    @classmethod
    def from_dict(cls, data, table):
        _record(data, ("id",))
        return cls(data["id"], table)

    @property
    def id(self):
        return self._id

    @property
    def table(self):
        return self._table

    @property
    def status(self):
        return self._status

    @property
    def menu(self):
        return self.table.restaurant.menu

    @property
    def diners(self):
        return list(self._diners.values())

    @property
    def orders(self):
        return list(self._orders.values())

    @property
    def items(self):
        return [item for order in self.orders for item in order.items]

    @property
    def payments(self):
        return list(self._payments.values())

    @property
    def total_cents(self):
        return sum(order.total_cents for order in self.orders)

    @property
    def paid_cents(self):
        # Tips are separate from the item bill.
        return sum(payment.amount_cents for payment in self.payments)

    @property
    def outstanding_cents(self):
        return self.total_cents - self.paid_cents

    @property
    def tips_cents(self):
        return sum(payment.tip_cents for payment in self.payments)

    def _require_open(self):
        if self.status != "open":
            raise ValueError("The table session is closed.")

    def _require_member(self, diner):
        if not isinstance(diner, Diner) or self._diners.get(diner.id) is not diner:
            raise ValueError("The diner must be a member of this table session.")

    def join(self, diner):
        self._require_open()
        if not isinstance(diner, Diner):
            raise ValueError("Only diners can join a table session.")
        if diner.id in self._diners:
            raise ValueError("Diner ID already exists in this session.")
        self._diners[diner.id] = diner

    def find_diner(self, diner_id):
        _integer(diner_id, "Diner ID")
        diner = self._diners.get(diner_id)
        if diner is None:
            raise ValueError("Diner does not exist in this session.")
        return diner

    def add_order(self, order):
        self._require_open()
        if not isinstance(order, Order) or order._session is not None:
            raise ValueError("Submit a draft order that is not assigned to a session.")
        if not len(order):
            raise ValueError("Cannot submit an empty order.")
        if order.id in self._orders:
            raise ValueError("Order ID already exists in this session.")
        existing_ids = {item.id for item in self.items}
        for item in order.items:
            menu_item = self.table.restaurant.find_menu_item(item.menu_item.id)
            if menu_item is not item.menu_item or not menu_item.available:
                raise ValueError("An order must use available items from this restaurant menu.")
            if item.id in existing_ids:
                raise ValueError("Order item ID already exists in this session.")
        # Check every line before adding the order.
        self._orders[order.id] = order
        order._session = self
        for item in order.items:
            item._session = self

    def find_item(self, item_id):
        _integer(item_id, "Order item ID")
        for item in self.items:
            if item.id == item_id:
                return item
        raise ValueError("Order item does not exist in this session.")

    def associate_diner(self, item_id, diner_id):
        self.find_item(item_id).associate_diner(self.find_diner(diner_id))

    def diner_subtotal_cents(self, diner_id):
        diner = self.find_diner(diner_id)
        return sum(item.share_cents(diner) for item in self.items)

    def diner_owed_cents(self, diner_id):
        subtotal = self.diner_subtotal_cents(diner_id)
        paid = sum(payment.amount_cents for payment in self.payments
                   if payment.diner_id == diner_id)
        return subtotal - paid

    def diner_item_owed_cents(self, item_id, diner_id):
        item = self.find_item(item_id)
        diner = self.find_diner(diner_id)
        paid = sum(payment.item_allocations.get(item_id, 0)
                   for payment in self.payments if payment.diner_id == diner_id)
        return item.share_cents(diner) - paid

    def item_paid_cents(self, item_id):
        self.find_item(item_id)
        return sum(payment.item_allocations.get(item_id, 0)
                   for payment in self.payments)

    def item_payment_status(self, item_id):
        item = self.find_item(item_id)
        if not item.participants:
            return "unallocated"
        paid = self.item_paid_cents(item_id)
        if paid == item.total_cents:
            return "mock_paid"
        if paid > 0:
            return "partially_mock_paid"
        return "unpaid"

    def pay(self, payment_id, diner_id, tip_option="None", manual_tip_cents=None):
        self._require_open()
        _integer(payment_id, "Mock payment ID")
        diner = self.find_diner(diner_id)
        if payment_id in self._payments:
            raise ValueError("Mock payment ID already exists in this session.")
        if any(not item.participants for item in self.items):
            raise ValueError("Allocate all ordered items before making a payment.")
        method = diner.payment_method
        if not diner.has_active_payment_method:
            raise ValueError("An active synthetic payment method is required.")
        amount = self.diner_owed_cents(diner_id)
        if amount <= 0:
            raise ValueError("This diner has no outstanding item balance.")
        tip = MockPayment.calculate_tip(amount, tip_option, manual_tip_cents)
        allocations = {}
        for item in self.items:
            owed = self.diner_item_owed_cents(item.id, diner.id)
            if owed > 0:
                allocations[item.id] = owed
        payment = MockPayment(payment_id, self.id, diner.id, method.id,
                              amount, allocations, tip)
        # Save the mock payment only after all checks pass.
        self._payments[payment.id] = payment
        for item in self.items:
            if diner in item.participants:
                item._locked = True
        return payment

    def close(self):
        self._require_open()
        if any(not item.participants for item in self.items):
            raise ValueError("Cannot close a session with unallocated items.")
        if self.outstanding_cents != 0:
            raise ValueError("Cannot close a session with an outstanding balance.")
        if any(item.status != "served" for item in self.items):
            raise ValueError("Cannot close a session before all items are served.")
        self._status = "closed"
        self.table._active_session = None

    def __len__(self):
        return len(self._diners)

    def __str__(self):
        return f"Session {self.id}, table {self.table.number}: {self.outstanding_cents / 100:.2f} outstanding ({self.status})"

    def __repr__(self):
        return f"TableSession(id={self.id}, table_id={self.table.id}, diners={len(self)}, status={self.status!r})"
