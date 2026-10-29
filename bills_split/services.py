"""Coordinate billing with dependencies supplied by the caller."""


class PaymentService:
    def __init__(self, tip_strategy):
        # מקבלת מבחוץ את דרך חישוב הטיפ.
        self.tip_strategy = tip_strategy

    def pay(self, session, payment_id, diner_id):
        # משלמת את החלק האישי עם הטיפ שנבחר.
        return session.pay(payment_id, diner_id, tip_strategy=self.tip_strategy)
