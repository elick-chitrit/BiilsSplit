import json

import pytest

from bills_split.models import FoodItem, DrinkItem
from bills_split.repository import load_menu_items


def test_loads_both_menu_types(tmp_path):
    # בודקת טעינת אוכל ומשקה מקובץ זמני.
    rows = [
        {"id": 1, "category": "food", "name": "Soup", "price_cents": 2000, "available": True},
        {"id": 2, "category": "drink", "name": "Water", "price_cents": 1000, "available": False},
    ]
    path = tmp_path / "menu.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    items = load_menu_items(path)
    assert isinstance(items[0], FoodItem)
    assert isinstance(items[1], DrinkItem)
    assert [item.price_cents for item in items] == [2000, 1000]
    assert not items[1].available


def test_rejects_duplicate_menu_id(tmp_path):
    # בודקת שמזהה כפול בקובץ נדחה.
    row = {"id": 1, "category": "food", "name": "Soup", "price_cents": 2000, "available": True}
    path = tmp_path / "menu.jsonl"
    path.write_text(json.dumps(row) + "\n" + json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        load_menu_items(path)
