import pytest

from bills_split.models import FoodItem
from bills_split.threaded_processing import MenuStock, reserve_for_diners


@pytest.mark.parametrize("quantity, diners, approvals, remaining", [(1, [1, 2], 1, 0), (0, [1, 2], 0, 0), (3, [1, 2], 2, 1), (2, [1, 1], 1, 1)])
def test_stock_is_not_oversold(quantity, diners, approvals, remaining):
    # בודקת אישורים ומלאי בלי להניח מי יזכה.
    stock = MenuStock(FoodItem(1, "Fries", 3000), quantity)
    results = reserve_for_diners(stock, diners)
    assert len(results) == len(diners)
    assert sum(row["approved"] for row in results) == approvals
    assert stock.remaining == remaining


def test_unavailable_item_is_not_reserved():
    # בודקת שפריט לא זמין לא מקבל אישור.
    stock = MenuStock(FoodItem(1, "Fries", 3000, False), 1)
    results = reserve_for_diners(stock, [1, 2])
    assert all(row["approved"] is False for row in results)
    assert stock.remaining == 1


def test_invalid_diner_is_rejected_before_threads_start():
    # בודקת שקלט שגוי לא צורך מלאי.
    stock = MenuStock(FoodItem(1, "Fries", 3000), 1)
    with pytest.raises(ValueError):
        reserve_for_diners(stock, [1, True])
    assert stock.remaining == 1
