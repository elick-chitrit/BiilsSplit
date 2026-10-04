"""Load the sample menu and find items by ID."""

import json

from .models import MenuItem, FoodItem, DrinkItem


MENU_TYPES = {"food": FoodItem, "drink": DrinkItem}
MENU_FIELDS = {"id", "category", "name", "price_cents", "available"}


def menu_item_from_dict(data):
    """Choose the menu class and use its normal validation."""
    if not isinstance(data, dict):
        raise ValueError("Each menu record must be a JSON object.")
    missing = MENU_FIELDS - set(data)
    if missing:
        raise ValueError(f"Missing menu fields: {', '.join(sorted(missing))}.")
    if set(data) - MENU_FIELDS:
        raise ValueError("Menu record contains unsupported fields.")
    category = data["category"]
    if not isinstance(category, str) or category not in MENU_TYPES:
        raise ValueError("Menu category must be food or drink.")
    return MENU_TYPES[category].from_dict(data)


def load_menu_items(path):
    """Load valid menu items one line at a time, keeping file order.

    The returned menu is stored in memory. with closes the file even if
    a line is invalid; a failed load does not return a partial menu.
    """
    items = []
    seen = set()
    with open(path, encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            try:
                data = json.loads(line)
                item = menu_item_from_dict(data)
                if item.id in seen:
                    raise ValueError(f"Duplicate menu item ID: {item.id}.")
            except ValueError as error:
                raise ValueError(f"Menu data line {line_number}: {error}")
            items.append(item)
            seen.add(item.id)
    return items


class MenuRepository:
    """Store menu items by ID and reject duplicates."""

    def __init__(self, items):
        self._items = {}
        for item in items:
            self.add(item)

    @classmethod
    def from_jsonl(cls, path):
        return cls(load_menu_items(path))

    @property
    def items(self):
        return list(self._items.values())

    def add(self, item):
        if not isinstance(item, MenuItem):
            raise ValueError("The menu repository accepts only menu items.")
        if item.id in self._items:
            raise ValueError("Menu item ID already exists in the repository.")
        self._items[item.id] = item

    def find(self, item_id):
        if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id <= 0:
            raise ValueError("Lookup requires a positive integer menu item ID.")
        # A missing ID returns None so the caller can handle it.
        return self._items.get(item_id)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return f"MenuRepository(items={len(self)})"
