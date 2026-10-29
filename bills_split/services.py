"""Coordinate billing with dependencies supplied by the caller."""


import logging

from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

from .api_client import InvalidJSONError, InvalidRateError

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, tip_strategy):
        # מקבלת מבחוץ את דרך חישוב הטיפ.
        self.tip_strategy = tip_strategy

    def pay(self, session, payment_id, diner_id):
        # משלמת את החלק האישי עם הטיפ שנבחר.
        return session.pay(payment_id, diner_id, tip_strategy=self.tip_strategy)


class CurrencyQuoteService:
    def __init__(self, client):
        # מקבלת את מקור שערי המטבע מבחוץ.
        self.client = client

    def quote(self, session, diner_id, currency):
        # מציגה אומדן של החלק האישי במטבע אחר.
        amount = session.diner_owed_cents(diner_id)
        try:
            rate = self.client.fetch_rate(currency)
        except (Timeout, ConnectionError):
            reason = "network"
        except HTTPError:
            reason = "http"
        except InvalidJSONError:
            reason = "json"
        except InvalidRateError:
            reason = "data"
        except RequestException:
            reason = "request"
        else:
            return build_currency_quote(amount, rate)
        logger.warning("Currency estimate unavailable: %s; keep ILS balance", reason)
        return {"available": False, "amount_ils_cents": amount, "currency": currency, "reason": reason}


def build_currency_quote(amount_cents, rate):
    # בונה אומדן לתצוגה בלי לגעת בתשלום.
    return {
        "available": True,
        "amount_ils_cents": amount_cents,
        "currency": rate["quote"],
        "estimate": f"{amount_cents / 100 * rate['rate']:.2f}",
        "rate_date": rate["date"],
    }
