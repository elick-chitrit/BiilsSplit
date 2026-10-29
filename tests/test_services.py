from unittest.mock import Mock

from bills_split.services import CurrencyQuoteService


def test_quote_converts_only_the_diners_unpaid_share(meal):
    # בודקת המרה של החלק האישי בלי לשנות חובות.
    client = Mock()
    client.fetch_rate.return_value = {"base": "ILS", "quote": "USD", "rate": 0.25, "date": "2026-10-28"}
    quote = CurrencyQuoteService(client).quote(meal, 1, "USD")
    assert quote == {"available": True, "amount_ils_cents": 951, "currency": "USD", "estimate": "2.38", "rate_date": "2026-10-28"}
    client.fetch_rate.assert_called_once_with("USD")
    assert meal.outstanding_cents == 1901
    assert meal.payments == []


import pytest
from requests.exceptions import Timeout, HTTPError
from bills_split.api_client import InvalidJSONError, InvalidRateError


@pytest.mark.parametrize("failure, reason", [(Timeout(), "network"), (HTTPError(), "http"), (InvalidJSONError(), "json"), (InvalidRateError(), "data")])
def test_quote_failure_keeps_original_bill(meal, failure, reason):
    # בודקת שכשל בשער לא משנה את החשבון.
    client = Mock()
    client.fetch_rate.side_effect = failure
    quote = CurrencyQuoteService(client).quote(meal, 1, "USD")
    assert quote == {"available": False, "amount_ils_cents": 951, "currency": "USD", "reason": reason}
    assert meal.outstanding_cents == 1901
    assert meal.payments == []
