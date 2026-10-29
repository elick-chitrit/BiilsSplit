"""Tip choices share one calculation contract."""

from abc import ABC, abstractmethod


def validate_cents(value):
    # בודקת שקיבלנו סכום שלם ולא שלילי.
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("Tip amount must be a nonnegative integer.")
    return value


class TipStrategy(ABC):
    @abstractmethod
    def calculate(self, amount_cents):
        # מגדירה את הפעולה המשותפת לכל אפשרויות הטיפ.
        pass


class PercentageTip(TipStrategy):
    def __init__(self, percentage):
        # שומרת אחוז טיפ מתוך האפשרויות הקיימות.
        if type(percentage) is not int or percentage not in (10, 12, 15, 20):
            raise ValueError("Choose 10, 12, 15, or 20 percent.")
        self.percentage = percentage

    def calculate(self, amount_cents):
        # מחשבת טיפ באחוזים ומעגלת לאגורה.
        validate_cents(amount_cents)
        return (amount_cents * self.percentage + 50) // 100


class ManualTip(TipStrategy):
    def __init__(self, amount_cents):
        # שומרת את סכום הטיפ שנבחר ידנית.
        self.amount_cents = validate_cents(amount_cents)

    def calculate(self, amount_cents):
        # מחזירה את הטיפ הידני בלי לשנות את החשבון.
        validate_cents(amount_cents)
        return self.amount_cents


class NoTip(TipStrategy):
    def calculate(self, amount_cents):
        # מחזירה אפס כשלא רוצים להוסיף טיפ.
        validate_cents(amount_cents)
        return 0


def select_tip_strategy(option="None", manual_tip_cents=None):
    # מתאימה את בחירת הסועד לחישוב הטיפ.
    if option == "Other":
        return ManualTip(manual_tip_cents)
    if manual_tip_cents is not None:
        raise ValueError("A manual amount is accepted only with Other.")
    if option == "None":
        return NoTip()
    return PercentageTip(option)
