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
        raise NotImplementedError("Currency quote is not implemented yet.")
