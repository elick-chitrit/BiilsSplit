"""Measure the time taken by a local restaurant operation."""

import time


class OperationTimer:
    """Time an operation, including failed runs.

    The original error is not hidden. Reuse is allowed after a run finishes.
    """

    def __init__(self, operation_name):
        # מכינה את הנתונים ההתחלתיים של מדידת זמן של פעולה.
        if not isinstance(operation_name, str) or not operation_name.strip():
            raise ValueError("An operation timer requires a nonempty name.")
        self._name = operation_name.strip()
        self._started_at = None
        self._duration_seconds = None
        self._active = False
        self._failed = False

    @property
    def name(self):
        # מחזירה את השם.
        return self._name

    @property
    def completed(self):
        # מחזירה אם מדידת הזמן כבר הסתיימה.
        return self._duration_seconds is not None

    @property
    def failed(self):
        # מחזירה אם התרחשה חריגה בזמן הפעולה שנמדדה.
        return self._failed

    @property
    def duration_seconds(self):
        # מחזירה את משך הפעולה שנמדד אחרי היציאה מהבלוק.
        return self._duration_seconds

    @property
    def elapsed_seconds(self):
        # מחזירה את הזמן שחלף, גם אם המדידה עדיין פועלת.
        if self._active:
            return time.perf_counter() - self._started_at
        return self.duration_seconds

    def __enter__(self):
        # מתחילה מדידה ומחזירה את הטיימר לשימוש בתוך הבלוק.
        if self._active:
            raise ValueError("This timer is already measuring an operation.")
        self._started_at = time.perf_counter()
        self._duration_seconds = None
        self._failed = False
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # מסיימת את המדידה גם בשגיאה ומשאירה את החריגה גלויה לקוד הקורא.
        self._duration_seconds = time.perf_counter() - self._started_at
        self._failed = exc_type is not None
        self._active = False
        return False

    def __repr__(self):
        # מחזירה פרטים על מדידת זמן של פעולה שעוזרים לבדוק את מצב האובייקט.
        return (f"OperationTimer(name={self.name!r}, completed={self.completed}, "
                f"failed={self.failed})")
