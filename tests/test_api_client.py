from unittest.mock import Mock

import pytest
import requests

from bills_split.api_client import ExchangeRateClient, InvalidJSONError, InvalidRateError
from bills_split.config import RATE_URL, REQUEST_TIMEOUT


@pytest.fixture
def response():
    # מכינה תשובת שירות חדשה לכל בדיקה.
    result = Mock(spec=requests.Response)
    result.json.return_value = [{"base": "ILS", "quote": "USD", "rate": 0.25, "date": "2026-10-28"}]
    return result


def test_success_validates_request_and_response(response):
    # בודקת את הבקשה ואת השער שהתקבל.
    get, sleep = Mock(return_value=response), Mock()
    actual = ExchangeRateClient(get, sleep).fetch_rate("USD")
    assert actual == {"base": "ILS", "quote": "USD", "rate": 0.25, "date": "2026-10-28"}
    get.assert_called_once_with(RATE_URL, params={"base": "ILS", "quotes": "USD"}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status.assert_called_once_with()
    sleep.assert_not_called()


@pytest.mark.parametrize("failure", [requests.Timeout, requests.ConnectionError])
def test_retry_stops_after_three_attempts(failure):
    # בודקת שעוצרים אחרי שלושה ניסיונות כושלים.
    get, sleep = Mock(side_effect=failure("offline")), Mock()
    with pytest.raises(failure):
        ExchangeRateClient(get, sleep).fetch_rate("USD")
    assert get.call_count == 3
    assert sleep.call_count == 2


def test_retry_recovers_after_connection_failure(response):
    # בודקת שחיבור שנכשל יכול להצליח בניסיון הבא.
    get = Mock(side_effect=[requests.ConnectionError("offline"), response])
    sleep = Mock()
    assert ExchangeRateClient(get, sleep).fetch_rate("USD")["rate"] == 0.25
    assert get.call_count == 2
    sleep.assert_called_once_with(1)


def test_http_error_is_not_retried(response):
    # בודקת ששגיאת הרשאה לא גוררת ניסיונות נוספים.
    response.status_code = 401
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    get, sleep = Mock(return_value=response), Mock()
    with pytest.raises(requests.HTTPError):
        ExchangeRateClient(get, sleep).fetch_rate("USD")
    assert get.call_count == 1
    sleep.assert_not_called()
    response.json.assert_not_called()


@pytest.mark.parametrize("data", [
    [{"base": "ILS", "quote": "USD", "date": "2026-10-28"}],
    [{"base": "ILS", "quote": "USD", "rate": -1, "date": "2026-10-28"}],
    [{"base": "ILS", "quote": "USD", "rate": True, "date": "2026-10-28"}],
    [{"base": "ILS", "quote": "USD", "rate": float("nan"), "date": "2026-10-28"}],
    [{"base": "EUR", "quote": "USD", "rate": 0.25, "date": "2026-10-28"}],
    [],
])
def test_invalid_data_is_not_retried(response, data):
    # בודקת שתגובה לא תקינה נדחית בלי ניסיון נוסף.
    response.json.return_value = data
    get, sleep = Mock(return_value=response), Mock()
    with pytest.raises(InvalidRateError):
        ExchangeRateClient(get, sleep).fetch_rate("USD")
    assert get.call_count == 1
    sleep.assert_not_called()


def test_invalid_json_is_distinct_from_invalid_fields(response):
    # בודקת שגיאת פענוח בנפרד משגיאת שדות.
    response.json.side_effect = requests.exceptions.JSONDecodeError("invalid", "x", 0)
    get, sleep = Mock(return_value=response), Mock()
    with pytest.raises(InvalidJSONError):
        ExchangeRateClient(get, sleep).fetch_rate("USD")
    assert get.call_count == 1
    sleep.assert_not_called()
