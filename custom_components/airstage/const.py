"""Constants for Fujitsu AIRSTAGE Cloud."""

from datetime import timedelta

DOMAIN = "airstage"
CONF_BASE_URL = "base_url"
CONF_COUNTRY = "country"
CONF_LANGUAGE = "language"
DEFAULT_COUNTRY = "Italy"
DEFAULT_LANGUAGE = "it"
SCAN_INTERVAL = timedelta(seconds=60)

REGIONS = {
    "Europe": "https://bke.euro.airstagelight.com/apiv1",
    "Australia": "https://bke.au.airstagelight.com/apiv1",
    "Japan": "https://bke.jp.airstagelight.com/apiv1",
    "United States": "https://bke.us.airstagelight.com/apiv1",
}

OP_MODES = {"0": "auto", "1": "cool", "2": "dry", "3": "fan_only", "4": "heat"}
HA_MODES = {value: key for key, value in OP_MODES.items()}
