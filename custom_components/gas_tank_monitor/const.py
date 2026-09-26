"""Constants for Gas Tank Monitor."""

DOMAIN = "gas_tank_monitor"
NAME = "Gas Tank Monitor"

# Default tank sizes in gallons (approximate usable capacity)
TANK_SIZES = {
    "20lb": 4.7,
    "30lb": 7.1,
    "40lb": 9.4,
    "100lb": 23.6,  # Caribbean standard ~100 lb cylinder
}

DEFAULT_TANK_SIZE = "100lb"
DEFAULT_SWITCH_THRESHOLD = 20  # % remaining to recommend switch
UPDATE_INTERVAL = 60  # seconds

# Attribute keys
ATTR_TANK_SIZE = "tank_size"
ATTR_CAPACITY_GALLONS = "capacity_gallons"
ATTR_VOLUME_REMAINING = "volume_remaining"
ATTR_BURN_RATE = "burn_rate"
ATTR_DAYS_SINCE_FULL = "days_since_full"
ATTR_DAYS_REMAINING = "days_remaining"
ATTR_STATUS = "status"
ATTR_PRESSURE = "pressure"
ATTR_LAST_FULL = "last_full"

CONF_PRESSURE_ENTITY = "pressure_entity"
CONF_LEVEL_ENTITY = "level_entity"
CONF_TEMP_ENTITY = "temp_entity"
CONF_BATTERY_ENTITY = "battery_entity"
CONF_SIGNAL_ENTITY = "signal_entity"
CONF_TANK_SIZE = "tank_size"
CONF_CUSTOM_GALLONS = "custom_gallons"
CONF_SWITCH_THRESHOLD = "switch_threshold"
