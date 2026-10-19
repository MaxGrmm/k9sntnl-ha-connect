"""Feste Werte der Integration."""

from datetime import timedelta

DOMAIN = "k9sntnl"
DEFAULT_URL = "https://app.k9sntnl.de"
CONF_URL = "url"
CONF_TOKEN = "token"
CONF_CODE = "code"
# Wie oft die Werte abgefragt werden. Die Sensoren am Anhänger melden etwa jede Minute.
UPDATE_INTERVAL = timedelta(seconds=30)
