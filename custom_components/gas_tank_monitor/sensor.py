"""Sensor platform for Gas Tank Monitor."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_BURN_RATE,
    ATTR_CAPACITY_GALLONS,
    ATTR_DAYS_REMAINING,
    ATTR_DAYS_SINCE_FULL,
    ATTR_LAST_FULL,
    ATTR_PRESSURE,
    ATTR_STATUS,
    ATTR_SUPPLIER_NAME,
    ATTR_SUPPLIER_PHONE,
    ATTR_TANK_SIZE,
    ATTR_VOLUME_REMAINING,
    CONF_BATTERY_ENTITY,
    CONF_CUSTOM_GALLONS,
    CONF_LEVEL_ENTITY,
    CONF_PRESSURE_ENTITY,
    CONF_SIGNAL_ENTITY,
    CONF_SUPPLIER_NAME,
    CONF_SUPPLIER_PHONE,
    CONF_SWITCH_THRESHOLD,
    CONF_TANK_SIZE,
    CONF_TEMP_ENTITY,
    DEFAULT_SWITCH_THRESHOLD,
    DEFAULT_TANK_SIZE,
    DOMAIN,
    TANK_SIZES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    data = {**entry.data, **entry.options}

    tank_size_key = data.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE)
    if tank_size_key == "custom":
        capacity = float(data.get(CONF_CUSTOM_GALLONS, 23.6))
    else:
        capacity = TANK_SIZES.get(tank_size_key, 23.6)

    threshold = int(data.get(CONF_SWITCH_THRESHOLD, DEFAULT_SWITCH_THRESHOLD))

    sensors = [
        GasTankLevelSensor(hass, entry, capacity, threshold),
        GasTankVolumeSensor(hass, entry, capacity),
        GasTankBurnRateSensor(hass, entry),
        GasTankDaysRemainingSensor(hass, entry, threshold),
    ]

    async_add_entities(sensors)


class GasTankBaseSensor(SensorEntity, RestoreEntity):
    """Base class for Gas Tank sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        capacity: float,
        threshold: int = DEFAULT_SWITCH_THRESHOLD,
    ) -> None:
        """Initialize the base sensor."""
        self.hass = hass
        self._entry = entry
        self._capacity = capacity
        self._threshold = threshold
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or "Gas Tank",
            manufacturer="Gas Tank Monitor",
            model="LPG Cylinder Monitor",
        )
        self._level: float | None = None
        self._pressure: float | None = None
        self._temperature: float | None = None
        self._battery: float | None = None
        self._signal: float | None = None
        self._last_full: datetime | None = None
        self._burn_rate: float | None = None
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks and restore state."""
        await super().async_added_to_hass()

        # Restore last full timestamp if available
        if (last_state := await self.async_get_last_state()) is not None:
            if last_full := last_state.attributes.get(ATTR_LAST_FULL):
                try:
                    self._last_full = dt_util.parse_datetime(last_full)
                except (ValueError, TypeError):
                    pass

        data = {**self._entry.data, **self._entry.options}
        entities_to_track = []
        for key in (
            CONF_PRESSURE_ENTITY,
            CONF_LEVEL_ENTITY,
            CONF_TEMP_ENTITY,
            CONF_BATTERY_ENTITY,
            CONF_SIGNAL_ENTITY,
        ):
            if entity_id := data.get(key):
                entities_to_track.append(entity_id)

        if entities_to_track:
            self._unsub = async_track_state_change_event(
                self.hass, entities_to_track, self._async_state_changed
            )

        # Initial update
        self._update_from_source()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up."""
        if self._unsub:
            self._unsub()

    @callback
    def _async_state_changed(self, event) -> None:
        """Handle source entity state changes."""
        self._update_from_source()
        self.async_write_ha_state()

    def _update_from_source(self) -> None:
        """Read source entities and compute level."""
        data = {**self._entry.data, **self._entry.options}

        # Prefer explicit level entity if provided
        level_entity = data.get(CONF_LEVEL_ENTITY)
        pressure_entity = data.get(CONF_PRESSURE_ENTITY)

        if level_entity:
            state = self.hass.states.get(level_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._level = float(state.state)
                except (ValueError, TypeError):
                    pass

        elif pressure_entity:
            state = self.hass.states.get(pressure_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._pressure = float(state.state)
                    # Simplified pressure → level approximation for LPG
                    # Real tanks hold pressure until low; this is a placeholder curve
                    self._level = self._pressure_to_level(self._pressure)
                except (ValueError, TypeError):
                    pass

        # Optional telemetry entities
        temp_entity = data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            state = self.hass.states.get(temp_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._temperature = float(state.state)
                except (ValueError, TypeError):
                    pass

        battery_entity = data.get(CONF_BATTERY_ENTITY)
        if battery_entity:
            state = self.hass.states.get(battery_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._battery = float(state.state)
                except (ValueError, TypeError):
                    pass

        signal_entity = data.get(CONF_SIGNAL_ENTITY)
        if signal_entity:
            state = self.hass.states.get(signal_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._signal = float(state.state)
                except (ValueError, TypeError):
                    pass

        # Detect "full" event (level crossed 95%)
        if self._level is not None and self._level >= 95:
            now = dt_util.utcnow()
            if self._last_full is None or (now - self._last_full) > timedelta(hours=12):
                self._last_full = now

    def _pressure_to_level(self, psi: float) -> float:
        """Rough conversion from PSI to % full for typical LPG cylinder.
        
        Note: LPG pressure is strongly temperature dependent.
        This is a simplified model for demonstration.
        Best results come from using a true level sensor (ultrasonic).
        """
        # Very rough piecewise approximation
        if psi >= 140:
            return 100.0
        if psi >= 120:
            return 70.0 + (psi - 120) * 1.5
        if psi >= 100:
            return 40.0 + (psi - 100) * 1.5
        if psi >= 80:
            return 20.0 + (psi - 80) * 1.0
        if psi >= 50:
            return max(0.0, (psi - 50) * 0.66)
        return 0.0

    def _get_status(self) -> str:
        """Return status string based on level."""
        if self._level is None:
            return "unknown"
        if self._level >= 40:
            return "Optimal"
        if self._level >= self._threshold:
            return "Low"
        return "Critical"

    def _days_since_full(self) -> float | None:
        if self._last_full is None:
            return None
        delta = dt_util.utcnow() - self._last_full
        return round(delta.total_seconds() / 86400, 1)

    def _estimate_burn_rate(self) -> float | None:
        """Very simple burn rate estimate from days since full and current level."""
        days = self._days_since_full()
        if days is None or days < 0.5 or self._level is None:
            return None
        used = self._capacity * (1 - self._level / 100)
        if used <= 0:
            return 0.0
        return round(used / days, 2)

    def _days_remaining(self) -> float | None:
        rate = self._estimate_burn_rate()
        if rate is None or rate <= 0 or self._level is None:
            return None
        remaining_vol = self._capacity * (self._level / 100)
        # Days until threshold
        target_vol = self._capacity * (self._threshold / 100)
        usable = remaining_vol - target_vol
        if usable <= 0:
            return 0.0
        return round(usable / rate, 0)


class GasTankLevelSensor(GasTankBaseSensor):
    """Main level sensor (%)."""

    _attr_name = "Level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY  # closest semantic
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:propane-tank"

    def __init__(self, hass, entry, capacity, threshold):
        super().__init__(hass, entry, capacity, threshold)
        self._attr_unique_id = f"{entry.entry_id}_level"

    @property
    def native_value(self) -> float | None:
        return round(self._level, 1) if self._level is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {
            ATTR_TANK_SIZE: self._entry.data.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE),
            ATTR_CAPACITY_GALLONS: self._capacity,
            ATTR_STATUS: self._get_status(),
            ATTR_VOLUME_REMAINING: round(self._capacity * (self._level or 0) / 100, 1),
            ATTR_BURN_RATE: self._estimate_burn_rate(),
            ATTR_DAYS_SINCE_FULL: self._days_since_full(),
            ATTR_DAYS_REMAINING: self._days_remaining(),
            ATTR_LAST_FULL: self._last_full.isoformat() if self._last_full else None,
            "connection": "Sensor",
        }
        if self._pressure is not None:
            attrs[ATTR_PRESSURE] = self._pressure
        if self._temperature is not None:
            attrs["temperature"] = self._temperature
        if self._battery is not None:
            attrs["battery"] = self._battery
            attrs["battery_level"] = self._battery
        if self._signal is not None:
            attrs["signal"] = self._signal
        # Supplier contact from config entry
        cfg = {**self._entry.data, **self._entry.options}
        if phone := cfg.get(CONF_SUPPLIER_PHONE):
            attrs["supplier_phone"] = phone
        if sname := cfg.get(CONF_SUPPLIER_NAME):
            attrs["supplier_name"] = sname
        return attrs


class GasTankVolumeSensor(GasTankBaseSensor):
    """Volume remaining sensor."""

    _attr_name = "Volume Remaining"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gauge"

    def __init__(self, hass, entry, capacity):
        super().__init__(hass, entry, capacity)
        self._attr_unique_id = f"{entry.entry_id}_volume"

    @property
    def native_value(self) -> float | None:
        if self._level is None:
            return None
        return round(self._capacity * self._level / 100, 1)


class GasTankBurnRateSensor(GasTankBaseSensor):
    """Burn rate sensor."""

    _attr_name = "Burn Rate"
    _attr_native_unit_of_measurement = "gal/day"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fire"

    def __init__(self, hass, entry):
        super().__init__(hass, entry, 0)
        self._attr_unique_id = f"{entry.entry_id}_burn_rate"

    @property
    def native_value(self) -> float | None:
        return self._estimate_burn_rate()


class GasTankDaysRemainingSensor(GasTankBaseSensor):
    """Forecast days remaining until switch threshold."""

    _attr_name = "Days Remaining"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, hass, entry, threshold):
        super().__init__(hass, entry, 0, threshold)
        self._attr_unique_id = f"{entry.entry_id}_days_remaining"

    @property
    def native_value(self) -> float | None:
        return self._days_remaining()
