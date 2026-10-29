import pytest

from bills_split.services import PaymentService
from bills_split.strategies import PercentageTip, ManualTip, NoTip


@pytest.mark.parametrize("strategy, expected", [(PercentageTip(10), 95), (ManualTip(300), 300), (NoTip(), 0)])
def test_strategy_used_by_payment_service(meal, strategy, expected):
    # בודקת שהטיפ שנבחר מגיע לקבלה.
    receipt = PaymentService(strategy).pay(meal, 1, 1)
    assert receipt.amount_cents == 951
    assert receipt.tip_cents == expected
    assert meal.outstanding_cents == 950


@pytest.mark.parametrize("percentage", [True, 12.0, 13, -10])
def test_rejects_invalid_percentage(percentage):
    # בודקת שאחוז לא תקין נדחה.
    with pytest.raises(ValueError):
        PercentageTip(percentage)


def test_percentage_rounds_half_up():
    # בודקת עיגול של חצי אגורה כלפי מעלה.
    assert PercentageTip(10).calculate(5) == 1
