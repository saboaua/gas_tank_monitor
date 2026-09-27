"""Constants for Gas Tank Monitor."""

DOMAIN = "gas_tank_monitor"
NAME = "Gas Tank Monitor"

TANK_SIZES = {
    "20lb": 4.7,
    "30lb": 7.1,
    "40lb": 9.4,
    "100lb": 23.6,
}

DEFAULT_TANK_SIZE = "100lb"
DEFAULT_SWITCH_THRESHOLD = 20
UPDATE_INTERVAL = 60
REF_TEMP_F = 70.0

ATTR_TANK_SIZE = "tank_size"
ATTR_CAPACITY_GALLONS = "capacity_gallons"
ATTR_VOLUME_REMAINING = "volume_remaining"
ATTR_BURN_RATE = "burn_rate"
ATTR_BURN_RATE_7D = "burn_rate_7d"
ATTR_BURN_RATE_CHANGE = "burn_rate_change"
ATTR_DAYS_SINCE_FULL = "days_since_full"
ATTR_DAYS_REMAINING = "days_remaining"
ATTR_STATUS = "status"
ATTR_PRESSURE = "pressure"
ATTR_PRESSURE_RAW = "pressure_raw"
ATTR_LAST_FULL = "last_full"
ATTR_SUPPLIER_PHONE = "supplier_phone"
ATTR_SUPPLIER_NAME = "supplier_name"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_TEMP_COMPENSATED = "temp_compensated"

CONF_PRESSURE_ENTITY = "pressure_entity"
CONF_LEVEL_ENTITY = "level_entity"
CONF_TEMP_ENTITY = "temp_entity"
CONF_BATTERY_ENTITY = "battery_entity"
CONF_SIGNAL_ENTITY = "signal_entity"
CONF_TANK_SIZE = "tank_size"
CONF_CUSTOM_GALLONS = "custom_gallons"
CONF_SWITCH_THRESHOLD = "switch_threshold"
CONF_SUPPLIER_PHONE = "supplier_phone"
CONF_SUPPLIER_NAME = "supplier_name"
CONF_TEMP_COMPENSATION = "temp_compensation"

MAX_LEVEL_SAMPLES = 400
