"""Fetch and validate reference rates; never send diner or payment data."""

import json
import logging
import time

import requests

from .config import RATE_URL, REQUEST_TIMEOUT, MAX_ATTEMPTS, RETRY_DELAY, QUOTE_CURRENCIES

logger = logging.getLogger(__name__)


class InvalidJSONError(ValueError):
    pass


class InvalidRateError(ValueError):
    pass


def validate_currency(currency):
    # בודקת שהמטבע נתמך בדמו.
    if currency not in QUOTE_CURRENCIES:
        raise ValueError("Choose USD, EUR, or GBP.")


def extract_rate(data, currency):
    # בודקת את השער לפני שמשתמשים בו.
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise InvalidRateError("Expected exactly one exchange-rate record.")
    row = data[0]
    if row.get("base") != "ILS" or row.get("quote") != currency:
        raise InvalidRateError("Exchange-rate currencies do not match the request.")
    rate = row.get("rate")
    if type(rate) not in (int, float) or not 0 < rate < float("inf"):
        raise InvalidRateError("Exchange rate must be a positive finite number.")
    date = row.get("date")
    if not isinstance(date, str) or not date.strip():
        raise InvalidRateError("Exchange-rate date is missing.")
    return {"base": "ILS", "quote": currency, "rate": rate, "date": date}


class ExchangeRateClient:
    def __init__(self, get=None, sleep=None):
        # מקבלת את בקשת הרשת וההמתנה מבחוץ.
        self.get = requests.get if get is None else get
        self.sleep = time.sleep if sleep is None else sleep

    def fetch_rate(self, currency):
        # מביאה שער אמיתי ובודקת את התגובה.
        validate_currency(currency)
        response = self._request(currency)
        response.raise_for_status()
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as error:
            logger.error("Rate response is not valid JSON")
            raise InvalidJSONError("Rate service returned invalid JSON.") from error
        return extract_rate(data, currency)

    def _request(self, currency):
        # מנסה שוב רק כשיש תקלה זמנית בחיבור.
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                logger.info("Fetching ILS/%s rate, attempt %s", currency, attempt)
                return self.get(RATE_URL, params={"base": "ILS", "quotes": currency}, timeout=REQUEST_TIMEOUT)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt == MAX_ATTEMPTS:
                    logger.error("Rate request failed after %s attempts", attempt)
                    raise
                logger.warning("Temporary connection failure; retrying")
                self.sleep(RETRY_DELAY)


class DemoRateClient:
    def __init__(self, path):
        # שומרת את מיקום השערים המדומים.
        self.path = path

    def fetch_rate(self, currency):
        # קוראת שער מדומה מקובץ מקומי.
        validate_currency(currency)
        with open(self.path, encoding="utf-8") as source:
            rows = json.load(source)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise InvalidRateError("Demo rates must be a list of records.")
        return extract_rate([row for row in rows if row.get("quote") == currency], currency)
