from unittest.mock import Mock

import requests

from bills_split.api_client import ExchangeRateClient
from bills_split.services import CurrencyQuoteService, PaymentService
from bills_split.strategies import PercentageTip, NoTip


def test_quote_payment_serving_and_closure(meal):
    # בודקת תהליך מלא עם שער חיצוני מדומה.
    response = Mock(spec=requests.Response)
    response.json.return_value = [{"base": "ILS", "quote": "USD", "rate": 0.25, "date": "2026-10-28"}]
    client = ExchangeRateClient(Mock(return_value=response), Mock())
    quote = CurrencyQuoteService(client).quote(meal, 1, "USD")
    assert quote["estimate"] == "2.38"
    first = PaymentService(PercentageTip(12)).pay(meal, 1, 1)
    second = PaymentService(NoTip()).pay(meal, 2, 2)
    assert first.total_cents == 1065
    assert second.total_cents == 950
    assert meal.diner_owed_cents(3) == 0
    meal.find_item(1).advance_status()
    meal.find_item(1).advance_status()
    meal.close()
    assert meal.outstanding_cents == 0
    assert meal.tips_cents == 114
    assert meal.status == "closed"
    assert meal.item_payment_status(1) == "mock_paid"


def test_default_demo_runs_without_network(capsys):
    # בודקת שהדמו המלא עובד בלי רשת.
    from main import main
    main()
    output = capsys.readouterr().out
    assert "Rate source: SIMULATED local rate" in output
    assert "Include me: 2 participants share one dish" in output
    assert "STAGE 2 COMPLETE | table closed | outstanding: 0" in output
