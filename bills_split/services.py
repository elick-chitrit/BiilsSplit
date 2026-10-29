"""Coordinate billing with dependencies supplied by the caller."""


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
        rate = self.client.fetch_rate(currency)
        return {
            "available": True,
            "amount_ils_cents": amount,
            "currency": currency,
            "estimate": f"{amount / 100 * rate['rate']:.2f}",
            "rate_date": rate["date"],
        }
