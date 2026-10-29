"""Create menu items from validated input records."""

from .models import FoodItem, DrinkItem


MENU_TYPES = {"food": FoodItem, "drink": DrinkItem}
MENU_FIELDS = {"id", "category", "name", "price_cents", "available"}


def menu_item_from_dict(data):
    # בודקת את שדות הרשומה ויוצרת ממנה מנה או משקה.
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


