"""Constants for the InelNET integration."""
from typing import Final

DOMAIN: Final = "inelnet"

# Configuration
CONF_HOST: Final = "host"
CONF_DEVICES: Final = "devices"
CONF_CHANNEL: Final = "channel"
CONF_NAME: Final = "name"
CONF_TRAVEL_TIME: Final = "travel_time"
CONF_FACADE: Final = "facade"
CONF_FLOOR: Final = "floor"
CONF_SHADED: Final = "shaded"

# Defaults
DEFAULT_PORT: Final = 80
DEFAULT_TIMEOUT: Final = 5
DEFAULT_TRAVEL_TIME: Final = 20  # seconds
DEFAULT_RETRY_COUNT: Final = 2
DEFAULT_RETRY_DELAY: Final = 0.8  # seconds

# Action codes for InelNET protocol
ACTION_UP: Final = 160
ACTION_UP_SHORT: Final = 176
ACTION_STOP: Final = 144
ACTION_DOWN: Final = 192
ACTION_DOWN_SHORT: Final = 208
ACTION_PROGRAM: Final = 224

# Facade orientations
FACADES: Final = ["N", "NE", "E", "SE", "S", "SV", "V", "NV"]
FACADE_ANGLES: Final = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SV": 225,
    "V": 270,
    "NV": 315,
}

# Floor options
FLOORS: Final = ["parter", "etaj", "mansarda", "demisol"]
