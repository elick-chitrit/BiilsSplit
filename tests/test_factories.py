import pytest

from bills_split.factories import menu_item_from_dict
from bills_split.models import FoodItem, DrinkItem


@pytest.mark.parametrize("category, expected_type, area", [("food", FoodItem, "kitchen"), ("drink", DrinkItem, "bar")])
def test_menu_factory(category, expected_type, area):
    # בודקת שנוצר סוג הפריט המתאים.
    item = menu_item_from_dict({"id": 1, "category": category, "name": "Demo", "price_cents": 1000, "available": True})
    assert isinstance(item, expected_type)
    assert item.preparation_area() == area
    assert item.price_cents == 1000


def test_factory_rejects_unknown_category():
    # בודקת שסוג לא מוכר נדחה.
    with pytest.raises(ValueError, match="category"):
        menu_item_from_dict({"id": 1, "category": "unknown", "name": "Demo", "price_cents": 1000, "available": True})
