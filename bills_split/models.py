"""Restaurant, table, order, and mock payment models.

Money is stored in cents. State changes go through the model's methods.
The QR reference, POS state, and payments are local mock data.
"""


def _integer(value, field, minimum=1):
    # בודקת שהערך הוא מספר שלם בטווח המותר, ולא ערך בוליאני.
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{field} must be an integer of at least {minimum}.")
    return value


def _text(value, field):
    # בודקת שיש טקסט ומורידה רווחים מיותרים מהקצוות.
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text.")
    return value.strip()


def _record(data, fields):
    # בודקת שקיבלנו מילון ושכל השדות הנדרשים נמצאים בו.
    if not isinstance(data, dict):
        raise ValueError("An alternative constructor requires a dictionary.")
    for field in fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}.")


class MenuItem:
    """A menu item with a price and availability."""

    def __init__(self, item_id, name, price_cents, available=True):
        # מכינה את הנתונים ההתחלתיים של פריט בתפריט.
        self._id = _integer(item_id, "Menu item ID")
        self._name = _text(name, "Menu item name")
        self.price_cents = price_cents
        self.set_availability(available)

    @classmethod
    def from_dict(cls, data):
        # יוצרת פריט בתפריט מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "name", "price_cents"))
        return cls(data["id"], data["name"], data["price_cents"],
                   data.get("available", True))

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def name(self):
        # מחזירה את השם.
        return self._name

    @property
    def price_cents(self):
        # מחזירה את מחיר הפריט באגורות.
        return self._price_cents

    @price_cents.setter
    def price_cents(self, value):
        # מעדכנת את המחיר רק אחרי בדיקה שהוא מספר אגורות חיובי.
        self._price_cents = _integer(value, "Menu price")

    @property
    def display_price(self):
        # מחזירה את המחיר לתצוגה עם שתי ספרות אחרי הנקודה.
        return f"{self.price_cents / 100:.2f}"

    @property
    def available(self):
        # מחזירה אם הפריט זמין להזמנה.
        return self._available

    def set_availability(self, available):
        # מעדכנת אם אפשר להזמין את הפריט, אחרי בדיקת הערך.
        if not isinstance(available, bool):
            raise ValueError("Availability must be True or False.")
        self._available = available

    def preparation_area(self):
        # מחזירה את יעד השירות הכללי של פריט תפריט.
        return "service"

    def __str__(self):
        # מחזירה תיאור קצר וקריא של פריט בתפריט.
        return f"{self.name}: {self.display_price}"

    def __repr__(self):
        # מחזירה פרטים על פריט בתפריט שעוזרים לבדוק את מצב האובייקט.
        return (f"{type(self).__name__}(id={self.id}, name={self.name!r}, "
                f"price_cents={self.price_cents}, available={self.available})")


class FoodItem(MenuItem):
    """Food is prepared in the kitchen."""

    def preparation_area(self):
        # מחזירה שהמנה מיועדת להכנה במטבח.
        return "kitchen"


class DrinkItem(MenuItem):
    """Drinks are prepared at the bar."""

    def preparation_area(self):
        # מחזירה שהמשקה מיועד להכנה בבר.
        return "bar"


class Restaurant:
    """The restaurant menu and physical tables."""

    def __init__(self, restaurant_id, name):
        # מכינה את הנתונים ההתחלתיים של מסעדה.
        self._id = _integer(restaurant_id, "Restaurant ID")
        self._name = _text(name, "Restaurant name")
        self._menu = {}
        self._tables = {}

    @classmethod
    def from_dict(cls, data):
        # יוצרת מסעדה מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "name"))
        return cls(data["id"], data["name"])

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def name(self):
        # מחזירה את השם.
        return self._name

    @property
    def menu(self):
        # מחזירה עותק של רשימת פריטי התפריט.
        return list(self._menu.values())

    @property
    def tables(self):
        # מחזירה עותק של רשימת השולחנות במסעדה.
        return list(self._tables.values())

    def add_menu_item(self, item):
        # מוסיפה פריט לתפריט ובודקת שהמזהה שלו לא תפוס.
        if not isinstance(item, MenuItem):
            raise ValueError("The menu accepts only menu items.")
        if item.id in self._menu:
            raise ValueError("Menu item ID already exists.")
        self._menu[item.id] = item

    def find_menu_item(self, item_id):
        # מוצאת פריט בתפריט לפי מזהה תקין.
        _integer(item_id, "Menu item ID")
        item = self._menu.get(item_id)
        if item is None:
            raise ValueError("Menu item does not exist in this restaurant.")
        return item

    def add_table(self, table):
        # מוסיפה שולחן למסעדה בלי להכפיל מזהה או מספר שולחן.
        if not isinstance(table, Table) or table.restaurant is not self:
            raise ValueError("The table must belong to this restaurant.")
        if table.id in self._tables:
            raise ValueError("Table ID already exists.")
        for existing in self.tables:
            if existing.number == table.number:
                raise ValueError("Table number already exists.")
        self._tables[table.id] = table

    def find_table(self, table_id):
        # מוצאת שולחן במסעדה לפי מזהה תקין.
        _integer(table_id, "Table ID")
        table = self._tables.get(table_id)
        if table is None:
            raise ValueError("Table does not exist in this restaurant.")
        return table

    def __len__(self):
        # מחזירה את מספר פריטי התפריט.
        return len(self._menu)

    def __str__(self):
        # מחזירה תיאור קצר וקריא של מסעדה.
        return f"{self.name}: {len(self)} menu items, {len(self._tables)} tables"

    def __repr__(self):
        # מחזירה פרטים על מסעדה שעוזרים לבדוק את מצב האובייקט.
        return f"Restaurant(id={self.id}, name={self.name!r})"


class Table:
    """A physical table, separate from the meal taking place at it."""

    def __init__(self, table_id, number, restaurant):
        # מכינה את הנתונים ההתחלתיים של שולחן.
        if not isinstance(restaurant, Restaurant):
            raise ValueError("A table requires a restaurant.")
        self._id = _integer(table_id, "Table ID")
        self._number = _integer(number, "Table number")
        self._restaurant = restaurant
        self._active_session = None

    @classmethod
    def from_dict(cls, data, restaurant):
        # יוצרת שולחן מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "number"))
        return cls(data["id"], data["number"], restaurant)

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def number(self):
        # מחזירה את מספר השולחן במסעדה.
        return self._number

    @property
    def restaurant(self):
        # מחזירה את המסעדה שאליה השולחן שייך.
        return self._restaurant

    @property
    def qr_label(self):
        # מחזירה תווית פיקטיבית שמייצגת את קוד ההצטרפות לשולחן.
        return f"MOCK-TABLE-{self.restaurant.id}-{self.id}"

    @property
    def active_session(self):
        # מחזירה את הארוחה הפעילה בשולחן, אם יש כזאת.
        return self._active_session

    def open_session(self, session_id):
        # פותחת ארוחה חדשה בשולחן דרך הבדיקות של מחלקת הארוחה.
        return TableSession(session_id, self)

    def __str__(self):
        # מחזירה תיאור קצר וקריא של שולחן.
        return f"Table {self.number} at {self.restaurant.name}"

    def __repr__(self):
        # מחזירה פרטים על שולחן שעוזרים לבדוק את מצב האובייקט.
        return f"Table(id={self.id}, number={self.number}, restaurant_id={self.restaurant.id})"


class MockPaymentMethod:
    """A mock card label with no real card details."""

    def __init__(self, method_id, diner_id):
        # מכינה את הנתונים ההתחלתיים של אמצעי תשלום מוקאפ.
        self._id = _integer(method_id, "Mock payment method ID")
        self._diner_id = _integer(diner_id, "Payment method owner ID")
        self._active = True

    @classmethod
    def from_dict(cls, data):
        # יוצרת אמצעי תשלום מוקאפ מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "diner_id"))
        return cls(data["id"], data["diner_id"])

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def diner_id(self):
        # מחזירה את מזהה הסועד.
        return self._diner_id

    @property
    def active(self):
        # מחזירה אם אמצעי התשלום המוקאפ פעיל.
        return self._active

    @property
    def synthetic_card_label(self):
        # מחזירה שם פיקטיבי לכרטיס, בלי פרטי אשראי אמיתיים.
        return f"MOCK-CARD-{self.id}"

    def deactivate(self):
        # מסמנת את אמצעי התשלום המוקאפ כלא פעיל.
        self._active = False

    def __str__(self):
        # מחזירה תיאור קצר וקריא של אמצעי תשלום מוקאפ.
        return f"{self.synthetic_card_label} ({'active' if self.active else 'inactive'})"

    def __repr__(self):
        # מחזירה את פרטי אמצעי התשלום לצורך בדיקה.
        return f"MockPaymentMethod(id={self.id}, diner_id={self.diner_id}, active={self.active})"


class Diner:
    """A diner and their optional mock payment method."""

    def __init__(self, diner_id, name, payment_method=None):
        # מכינה את הנתונים ההתחלתיים של סועד.
        self._id = _integer(diner_id, "Diner ID")
        self._name = _text(name, "Diner name")
        self._payment_method = None
        if payment_method is not None:
            self.set_payment_method(payment_method)

    @classmethod
    def from_dict(cls, data, payment_method=None):
        # יוצרת סועד מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "name"))
        return cls(data["id"], data["name"], payment_method)

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def name(self):
        # מחזירה את השם.
        return self._name

    @property
    def payment_method(self):
        # מחזירה את אמצעי התשלום המוקאפ של הסועד, אם הוגדר.
        return self._payment_method

    @property
    def has_active_payment_method(self):
        # בודקת שלסועד יש אמצעי תשלום מוקאפ פעיל.
        return self.payment_method is not None and self.payment_method.active

    def set_payment_method(self, method):
        # משייכת לסועד אמצעי תשלום מוקאפ ששייך לו.
        if not isinstance(method, MockPaymentMethod) or method.diner_id != self.id:
            raise ValueError("The mock payment method must belong to this diner.")
        self._payment_method = method

    def __str__(self):
        # מחזירה תיאור קצר וקריא של סועד.
        return self.name

    def __repr__(self):
        # מחזירה פרטים על סועד שעוזרים לבדוק את מצב האובייקט.
        return f"Diner(id={self.id}, name={self.name!r})"


class OrderItem:
    """An ordered item and the diners who consumed it."""

    def __init__(self, item_id, menu_item, quantity=1):
        # מכינה את הנתונים ההתחלתיים של פריט בהזמנה.
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
        # יוצרת פריט בהזמנה מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "quantity"))
        return cls(data["id"], menu_item, data["quantity"])

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def menu_item(self):
        # מחזירה את פריט התפריט שעליו מבוססת שורת ההזמנה.
        return self._menu_item

    @property
    def quantity(self):
        # מחזירה כמה יחידות יש בשורת ההזמנה.
        return self._quantity

    @property
    def unit_price_cents(self):
        # מחזירה את מחיר היחידה שנשמר כשהפריט נוצר.
        return self._unit_price_cents

    @property
    def total_cents(self):
        # מחשבת את מחיר היחידה כפול הכמות שהוזמנה.
        return self.unit_price_cents * self.quantity

    @property
    def participants(self):
        # מחזירה עותק של רשימת הסועדים שמשתתפים בפריט.
        return list(self._participants)

    @property
    def locked(self):
        # מחזירה אם שיוך המשתתפים כבר נעול בעקבות תשלום.
        return self._locked

    @property
    def status(self):
        # מחזירה את מצב ההכנה וההגשה של הפריט.
        return self._status

    def _require_open_session(self):
        # בודקת שהפריט שייך לארוחה שעדיין פתוחה.
        if self._session is None or self._session.status != "open":
            raise ValueError("The item must belong to an open table session.")

    def associate_diner(self, diner):
        # משייכת משתתף מהארוחה לפריט שעדיין פתוח לשינויים.
        self._require_open_session()
        self._session._require_member(diner)
        if self.locked:
            raise ValueError("Participation cannot change after an item share is paid.")
        if diner in self._participants:
            raise ValueError("The diner is already associated with this item.")
        self._participants.append(diner)

    def remove_diner(self, diner):
        # מסירה משתתף מהפריט רק אם עדיין מותר לשנות את החלוקה.
        self._require_open_session()
        self._session._require_member(diner)
        if self.locked:
            raise ValueError("Participation cannot change after an item share is paid.")
        if diner not in self._participants:
            raise ValueError("The diner is not associated with this item.")
        self._participants.remove(diner)

    def share_cents(self, diner):
        # מחשבת את החלק של הסועד בפריט, כולל חלוקת האגורות שנשארו.
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
        # מקדמת את הפריט מהזמנה להכנה, ומהכנה להגשה.
        self._require_open_session()
        next_status = {"ordered": "preparing", "preparing": "served"}
        if self.status not in next_status:
            raise ValueError("A served item has no further fulfillment step.")
        self._status = next_status[self.status]

    def preparation_area(self):
        # Food and drinks choose their own preparation area.
        # מבקשת מפריט התפריט את יעד ההכנה שלו.
        return self.menu_item.preparation_area()

    def __len__(self):
        # מחזירה את מספר הסועדים שמשתתפים בפריט.
        return len(self._participants)

    def __str__(self):
        # מחזירה תיאור קצר וקריא של פריט בהזמנה.
        return f"{self.quantity} x {self.menu_item.name}: {self.total_cents / 100:.2f} ({self.status})"

    def __repr__(self):
        # מחזירה פרטים על פריט בהזמנה שעוזרים לבדוק את מצב האובייקט.
        return f"OrderItem(id={self.id}, menu_item_id={self.menu_item.id}, quantity={self.quantity})"


class Order:
    """Order lines can change until the order is submitted."""

    def __init__(self, order_id):
        # מכינה את הנתונים ההתחלתיים של הזמנה.
        self._id = _integer(order_id, "Order ID")
        self._items = {}
        self._session = None

    @classmethod
    def from_dict(cls, data):
        # יוצרת הזמנה מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id",))
        return cls(data["id"])

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def items(self):
        # מחזירה עותק של רשימת הפריטים בהזמנה.
        return list(self._items.values())

    @property
    def total_cents(self):
        # מסכמת את המחירים של כל פריטי ההזמנה.
        return sum(item.total_cents for item in self.items)

    @property
    def status(self):
        # קובעת את מצב ההזמנה לפי השיוך שלה ומצב הפריטים.
        if self._session is None:
            return "draft"
        if all(item.status == "served" for item in self.items):
            return "served"
        if all(item.status == "ordered" for item in self.items):
            return "ordered"
        return "in_progress"

    def add_item(self, item):
        # מוסיפה פריט פנוי להזמנה שעדיין לא נשלחה.
        if self._session is not None:
            raise ValueError("Submitted orders cannot gain or lose items; place a new order.")
        if not isinstance(item, OrderItem) or item._order is not None:
            raise ValueError("The item must be an unassigned order item.")
        if item.id in self._items:
            raise ValueError("Order item ID already exists.")
        self._items[item.id] = item
        item._order = self

    def find_item(self, item_id):
        # מוצאת פריט לפי מזהה תקין, או מודיעה שהוא לא קיים.
        _integer(item_id, "Order item ID")
        item = self._items.get(item_id)
        if item is None:
            raise ValueError("Order item does not exist in this order.")
        return item

    def remove_item(self, item_id):
        # מסירה פריט מהזמנה שעדיין לא נשלחה ומנתקת את השיוך שלו.
        if self._session is not None:
            raise ValueError("Items cannot be removed from a submitted order.")
        item = self.find_item(item_id)
        del self._items[item_id]
        item._order = None
        return item

    def preparation_requests(self):
        # מחזירה לכל פריט את יעד ההכנה שלו דרך המתודה המשותפת.
        return [(item.id, item.preparation_area()) for item in self.items]

    def __len__(self):
        # מחזירה את מספר פריטי ההזמנה.
        return len(self._items)

    def __str__(self):
        # מחזירה תיאור קצר וקריא של הזמנה.
        return f"Order {self.id}: {len(self)} items, {self.total_cents / 100:.2f} ({self.status})"

    def __repr__(self):
        # מחזירה פרטים על הזמנה שעוזרים לבדוק את מצב האובייקט.
        return f"Order(id={self.id}, items={len(self)}, status={self.status!r})"


class MockPayment:
    """A mock receipt showing which item shares were paid.

    TableSession.pay records the payment. Creating a receipt on its own
    does not settle a session.
    """

    TIP_OPTIONS = (10, 12, 15, 20, "Other", "None")

    def __init__(self, payment_id, session_id, diner_id, method_id,
                 amount_cents, item_allocations, tip_cents=0):
        # מכינה את הנתונים ההתחלתיים של תשלום מוקאפ.
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
        # יוצרת תשלום מוקאפ מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id", "session_id", "diner_id", "method_id", "amount_cents", "item_allocations"))
        return cls(data["id"], data["session_id"], data["diner_id"],
                   data["method_id"], data["amount_cents"], data["item_allocations"],
                   data.get("tip_cents", 0))

    @staticmethod
    def calculate_tip(amount_cents, option="None", manual_tip_cents=None):
        # מחשבת טיפ באחוזים או בסכום ידני, ומעגלת לאגורה כשצריך.
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
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def session_id(self):
        # מחזירה את מזהה הארוחה שעבורה נרשם התשלום.
        return self._session_id

    @property
    def diner_id(self):
        # מחזירה את מזהה הסועד.
        return self._diner_id

    @property
    def method_id(self):
        # מחזירה את מזהה אמצעי התשלום המוקאפ ששימש לתשלום.
        return self._method_id

    @property
    def item_allocations(self):
        # מחזירה עותק של הסכומים ששולמו על כל פריט בקבלה.
        return dict(self._item_allocations)

    @property
    def amount_cents(self):
        # מחזירה את הסכום ששולם על הפריטים, בלי הטיפ.
        return self._amount_cents

    @property
    def tip_cents(self):
        # מחזירה את סכום הטיפ בקבלה.
        return self._tip_cents

    @property
    def total_cents(self):
        # מחברת את התשלום על הפריטים ואת הטיפ לסכום הקבלה.
        return self.amount_cents + self.tip_cents

    @property
    def status(self):
        # מחזירה שהקבלה מייצגת תשלום מוקאפ שבוצע.
        return "mock_paid"

    def __str__(self):
        # מחזירה תיאור קצר וקריא של תשלום מוקאפ.
        return f"Mock payment {self.id}: {self.total_cents / 100:.2f}, including tip {self.tip_cents / 100:.2f}"

    def __repr__(self):
        # מחזירה פרטים על תשלום מוקאפ שעוזרים לבדוק את מצב האובייקט.
        return (f"MockPayment(id={self.id}, session_id={self.session_id}, "
                f"diner_id={self.diner_id}, amount_cents={self.amount_cents}, tip_cents={self.tip_cents})")


class TableSession:
    """One meal at a table, including diners, orders, and payments."""

    def __init__(self, session_id, table):
        # מכינה את הנתונים ההתחלתיים של ארוחה בשולחן.
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
        # יוצרת ארוחה בשולחן מתוך מילון דרך הבנאי והבדיקות שלו.
        _record(data, ("id",))
        return cls(data["id"], table)

    @property
    def id(self):
        # מחזירה את המזהה של האובייקט.
        return self._id

    @property
    def table(self):
        # מחזירה את השולחן שבו מתקיימת הארוחה.
        return self._table

    @property
    def status(self):
        # מחזירה אם הארוחה פתוחה או סגורה.
        return self._status

    @property
    def menu(self):
        # מחזירה עותק של רשימת פריטי התפריט.
        return self.table.restaurant.menu

    @property
    def diners(self):
        # מחזירה עותק של רשימת הסועדים שהצטרפו לארוחה.
        return list(self._diners.values())

    @property
    def orders(self):
        # מחזירה עותק של רשימת ההזמנות בארוחה.
        return list(self._orders.values())

    @property
    def items(self):
        # אוספת את כל הפריטים מכל ההזמנות לרשימה אחת.
        return [item for order in self.orders for item in order.items]

    @property
    def payments(self):
        # מחזירה עותק של רשימת תשלומי המוקאפ שנרשמו.
        return list(self._payments.values())

    @property
    def total_cents(self):
        # מסכמת את חשבון הפריטים מכל ההזמנות בארוחה.
        return sum(order.total_cents for order in self.orders)

    @property
    def paid_cents(self):
        # Tips are separate from the item bill.
        # מסכמת כמה שולם על הפריטים, בלי לכלול טיפים.
        return sum(payment.amount_cents for payment in self.payments)

    @property
    def outstanding_cents(self):
        # מחשבת כמה נשאר לשלם על הפריטים בשולחן.
        return self.total_cents - self.paid_cents

    @property
    def tips_cents(self):
        # מסכמת את הטיפים מכל תשלומי המוקאפ בארוחה.
        return sum(payment.tip_cents for payment in self.payments)

    def _require_open(self):
        # בודקת שהארוחה עדיין פתוחה לפני שינוי במצב שלה.
        if self.status != "open":
            raise ValueError("The table session is closed.")

    def _require_member(self, diner):
        # בודקת שזה אותו אובייקט סועד שנרשם לארוחה.
        if not isinstance(diner, Diner) or self._diners.get(diner.id) is not diner:
            raise ValueError("The diner must be a member of this table session.")

    def join(self, diner):
        # מצרפת סועד לארוחה פתוחה בלי להכפיל מזהים.
        self._require_open()
        if not isinstance(diner, Diner):
            raise ValueError("Only diners can join a table session.")
        if diner.id in self._diners:
            raise ValueError("Diner ID already exists in this session.")
        self._diners[diner.id] = diner

    def find_diner(self, diner_id):
        # מוצאת סועד בארוחה לפי מזהה תקין.
        _integer(diner_id, "Diner ID")
        diner = self._diners.get(diner_id)
        if diner is None:
            raise ValueError("Diner does not exist in this session.")
        return diner

    def add_order(self, order):
        # בודקת את כל פריטי ההזמנה ורק אז מצרפת אותה לארוחה.
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
        # מוצאת פריט לפי מזהה תקין, או מודיעה שהוא לא קיים.
        _integer(item_id, "Order item ID")
        for item in self.items:
            if item.id == item_id:
                return item
        raise ValueError("Order item does not exist in this session.")

    def associate_diner(self, item_id, diner_id):
        # מוצאת את הפריט והסועד ומפעילה את בדיקות השיוך של הפריט.
        self.find_item(item_id).associate_diner(self.find_diner(diner_id))

    def diner_subtotal_cents(self, diner_id):
        # מסכמת את חלקו של הסועד בכל הפריטים שבהם השתתף.
        diner = self.find_diner(diner_id)
        return sum(item.share_cents(diner) for item in self.items)

    def diner_owed_cents(self, diner_id):
        # מחשבת כמה הסועד עוד חייב אחרי התשלומים שכבר ביצע.
        subtotal = self.diner_subtotal_cents(diner_id)
        paid = sum(payment.amount_cents for payment in self.payments
                   if payment.diner_id == diner_id)
        return subtotal - paid

    def diner_item_owed_cents(self, item_id, diner_id):
        # מחשבת כמה הסועד עוד חייב על פריט מסוים.
        item = self.find_item(item_id)
        diner = self.find_diner(diner_id)
        paid = sum(payment.item_allocations.get(item_id, 0)
                   for payment in self.payments if payment.diner_id == diner_id)
        return item.share_cents(diner) - paid

    def item_paid_cents(self, item_id):
        # מסכמת כמה שולם על פריט מסוים מכל הקבלות.
        self.find_item(item_id)
        return sum(payment.item_allocations.get(item_id, 0)
                   for payment in self.payments)

    def item_payment_status(self, item_id):
        # מחזירה את מצב השיוך והתשלום של הפריט.
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
        # רושמת תשלום מוקאפ ליתרה ולטיפ, ונועלת את החלוקה.
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
        # סוגרת את הארוחה רק כשכל הפריטים שויכו, שולמו והוגשו.
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
        # מחזירה את מספר הסועדים בארוחה.
        return len(self._diners)

    def __str__(self):
        # מחזירה תיאור קצר וקריא של ארוחה בשולחן.
        return f"Session {self.id}, table {self.table.number}: {self.outstanding_cents / 100:.2f} outstanding ({self.status})"

    def __repr__(self):
        # מחזירה פרטים על ארוחה בשולחן שעוזרים לבדוק את מצב האובייקט.
        return f"TableSession(id={self.id}, table_id={self.table.id}, diners={len(self)}, status={self.status!r})"
