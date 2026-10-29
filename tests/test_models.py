import pytest

from bills_split.models import FoodItem, MockPayment, Order, OrderItem


def test_only_consumers_share_the_item(meal):
    # בודקת שרק מי שהשתתף במנה משלם עליה.
    assert [meal.diner_owed_cents(i) for i in (1, 2, 3)] == [951, 950, 0]
    assert meal.total_cents == 1901


@pytest.mark.parametrize("price", [0, -1, True, 1.5])
def test_invalid_menu_price(price):
    # בודקת שמחיר לא תקין נדחה.
    with pytest.raises(ValueError):
        FoodItem(2, "Soup", price)


@pytest.mark.parametrize("option, manual, expected", [(10, None, 190), ("Other", 500, 500), ("None", None, 0)])
def test_existing_tip_choices(option, manual, expected):
    # בודקת את אפשרויות הטיפ הקיימות.
    assert MockPayment.calculate_tip(1901, option, manual) == expected


def test_paid_participation_cannot_change(meal):
    # בודקת שלא משנים חלוקה שכבר שולמה.
    meal.pay(1, 1)
    with pytest.raises(ValueError):
        meal.associate_diner(1, 3)
    assert meal.diner_owed_cents(3) == 0
    assert meal.outstanding_cents == 950


def test_paid_table_waits_for_serving(meal):
    # בודקת שתשלום לבד לא מספיק לסגירת שולחן.
    meal.pay(1, 1)
    meal.pay(2, 2)
    with pytest.raises(ValueError, match="served"):
        meal.close()
    assert meal.status == "open"
    assert meal.table.active_session is meal
    meal.find_item(1).advance_status()
    meal.find_item(1).advance_status()
    meal.close()
    assert meal.status == "closed"
    assert meal.table.active_session is None


def test_served_unpaid_table_stays_open(meal):
    # בודקת שהגשה לא מוחקת חוב.
    meal.find_item(1).advance_status()
    meal.find_item(1).advance_status()
    with pytest.raises(ValueError, match="outstanding"):
        meal.close()
    assert meal.outstanding_cents == 1901
    assert meal.status == "open"


def test_later_order_keeps_previous_receipt(meal):
    # בודקת שהזמנה נוספת לא משנה תשלום קודם.
    receipt = meal.pay(1, 1)
    later = Order(2)
    later.add_item(OrderItem(2, meal.menu[0]))
    meal.add_order(later)
    meal.associate_diner(2, 1)
    assert receipt.item_allocations == {1: 951}
    assert meal.diner_owed_cents(1) == 1901
    assert meal.diner_item_owed_cents(1, 1) == 0


def test_invalid_tip_does_not_record_payment(meal):
    # בודקת שטיפ שגוי לא משנה את החשבון.
    with pytest.raises(ValueError):
        meal.pay(1, 1, "Other", -1)
    assert meal.payments == []
    assert meal.outstanding_cents == 1901
    assert not meal.find_item(1).locked


def test_user_defined_shared_fries_rule(meal):
    # בודקת שרק מי שהצטרף מתחלק במנה.
    fries = FoodItem(2, "Fries", 3000)
    meal.table.restaurant.add_menu_item(fries)
    order = Order(2)
    order.add_item(OrderItem(2, fries))
    meal.add_order(order)
    meal.associate_diner(2, 1)
    meal.associate_diner(2, 2)
    assert len(meal.find_item(2).participants) == 2
    assert [meal.diner_item_owed_cents(2, i) for i in (1, 2, 3)] == [1500, 1500, 0]


def test_user_defined_personal_tip_rule():
    # בודקת את הדוגמה שנבחרה לטיפ אישי.
    tip = MockPayment.calculate_tip(10000, 12)
    assert tip == 1200
    assert 10000 + tip == 11200
