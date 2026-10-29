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
