import pytest

from bills_split.models import Restaurant, Table, FoodItem, Diner, MockPaymentMethod, Order, OrderItem


@pytest.fixture
def meal():
    # מכינה ארוחה חדשה לכל בדיקה.
    restaurant = Restaurant(1, "Demo Bistro")
    dish = FoodItem(1, "Shared starter", 1901)
    restaurant.add_menu_item(dish)
    table = Table(1, 1, restaurant)
    restaurant.add_table(table)
    session = table.open_session(1)
    for diner_id in (1, 2, 3):
        session.join(Diner(diner_id, f"Diner {diner_id}", MockPaymentMethod(diner_id, diner_id)))
    order = Order(1)
    order.add_item(OrderItem(1, dish))
    session.add_order(order)
    session.associate_diner(1, 1)
    session.associate_diner(1, 2)
    return session


@pytest.fixture(autouse=True)
def block_real_network():
    # מונעת מהבדיקות לפנות לרשת בטעות.
    from unittest.mock import patch
    with patch("requests.sessions.Session.request", side_effect=AssertionError("Tests must stay offline.")):
        yield
