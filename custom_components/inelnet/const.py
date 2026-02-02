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

# Services
SERVICE_OPEN_FACADE: Final = "open_facade"
SERVICE_CLOSE_FACADE: Final = "close_facade"
SERVICE_OPEN_FLOOR: Final = "open_floor"
SERVICE_CLOSE_FLOOR: Final = "close_floor"
SERVICE_SET_SCENE: Final = "set_scene"

# Automation configuration
CONF_ENABLE_SOLAR_AUTOMATION: Final = "enable_solar_automation"
CONF_SOLAR_THRESHOLD: Final = "solar_threshold"
CONF_WEATHER_ENTITY: Final = "weather_entity"
CONF_ENABLE_WEATHER_PROTECTION: Final = "enable_weather_protection"
CONF_MAX_TEMPERATURE: Final = "max_temperature"
CONF_MAX_WIND_SPEED: Final = "max_wind_speed"
CONF_ENABLE_SENSORS: Final = "enable_sensors"

# Sensor defaults
DEFAULT_SOLAR_THRESHOLD: Final = 60
DEFAULT_MAX_TEMPERATURE: Final = 32
DEFAULT_MAX_WIND_SPEED: Final = 40

# Statistics tracking
ATTR_COMMANDS_TODAY: Final = "commands_today"
ATTR_RUNTIME_TODAY: Final = "runtime_today"
ATTR_LAST_COMMAND_TIME: Final = "last_command_time"

# Data keys
DATA_COORDINATOR: Final = "coordinator"
DATA_STATISTICS: Final = "statistics"
DATA_CONNECTION_STATUS: Final = "connection_status"
