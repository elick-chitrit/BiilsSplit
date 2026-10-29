import asyncio
from unittest.mock import patch

from bills_split.async_processing import collect_sequential, collect_concurrent, check_availability
from bills_split.models import FoodItem


def test_same_results_even_when_completion_order_differs():
    # בודקת שסדר הסיום לא משנה את סדר התוצאות.
    jobs = [(FoodItem(1, "Soup", 1000), 0.03), (FoodItem(2, "Fries", 1000, False), 0.01), (FoodItem(3, "Salad", 1000), 0.02)]
    completed = []

    async def tracked(item, delay):
        # רושמת איזה פריט סיים את הבדיקה.
        result = await check_availability(item, delay)
        completed.append(item.id)
        return result

    sequential = asyncio.run(collect_sequential(jobs))
    with patch("bills_split.async_processing.check_availability", tracked):
        concurrent = asyncio.run(collect_concurrent(jobs))
    assert concurrent == sequential == [
        {"item_id": 1, "available": True},
        {"item_id": 2, "available": False},
        {"item_id": 3, "available": True},
    ]
    assert completed == [2, 3, 1]


def test_empty_availability_request():
    # בודקת שרשימה ריקה מחזירה רשימה ריקה.
    assert asyncio.run(collect_concurrent([])) == []
    assert asyncio.run(collect_sequential([])) == []
