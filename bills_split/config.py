"""Settings for the reference-rate demo. No API key is required."""

RATE_URL = "https://api.frankfurter.dev/v2/rates"
REQUEST_TIMEOUT = (3, 10)
MAX_ATTEMPTS = 3
RETRY_DELAY = 1
QUOTE_CURRENCIES = ("USD", "EUR", "GBP")
