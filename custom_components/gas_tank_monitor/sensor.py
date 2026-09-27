"""Sensor platform for Gas Tank Monitor."""

from __future__ import annotations

from collections import deque
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
    ATTR_BURN_RATE_7D,
    ATTR_BURN_RATE_CHANGE,
    ATTR_CAPACITY_GALLONS,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DAYS_REMAINING,
    ATTR_DAYS_SINCE_FULL,
    ATTR_LAST_FULL,
    ATTR_PRESSURE,
    ATTR_PRESSURE_RAW,
    ATTR_STATUS,
    ATTR_SUPPLIER_NAME,
    ATTR_SUPPLIER_PHONE,
    ATTR_TANK_SIZE,
    ATTR_TEMP_COMPENSATED,
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
    CONF_TEMP_COMPENSATION,
    CONF_TEMP_ENTITY,
    DEFAULT_SWITCH_THRESHOLD,
    DEFAULT_TANK_SIZE,
    DOMAIN,
    MAX_LEVEL_SAMPLES,
    REF_TEMP_F,
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
        self._pressure_raw: float | None = None
        self._temperature: float | None = None
        self._battery: float | None = None
        self._signal: float | None = None
        self._temp_compensated: bool = False
        self._last_full: datetime | None = None
        self._level_samples: deque[tuple[str, float]] = deque(maxlen=MAX_LEVEL_SAMPLES)
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks and restore state + sample history."""
        await super().async_added_to_hass()

        if (last_state := await self.async_get_last_state()) is not None:
            if last_full := last_state.attributes.get(ATTR_LAST_FULL):
                try:
                    self._last_full = dt_util.parse_datetime(last_full)
                except (ValueError, TypeError):
                    pass
            raw_samples = last_state.attributes.get("level_samples")
            if isinstance(raw_samples, list):
                for item in raw_samples[-MAX_LEVEL_SAMPLES:]:
                    try:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            self._level_samples.append((str(item[0]), float(item[1])))
                    except (TypeError, ValueError):
                        continue

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

        level_entity = data.get(CONF_LEVEL_ENTITY)
        pressure_entity = data.get(CONF_PRESSURE_ENTITY)

        temp_entity = data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            state = self.hass.states.get(temp_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._temperature = float(state.state)
                except (ValueError, TypeError):
                    pass

        if level_entity:
            state = self.hass.states.get(level_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    self._level = float(state.state)
                    self._temp_compensated = False
                except (ValueError, TypeError):
                    pass

        elif pressure_entity:
            state = self.hass.states.get(pressure_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    pressure = float(state.state)
                except (ValueError, TypeError):
                    pressure = None
                if pressure is not None:
                    if not 0 <= pressure <= 300:
                        _LOGGER.warning(
                            "%s reported implausible pressure %.1f psi — ignoring",
                            pressure_entity,
                            pressure,
                        )
                    else:
                        self._pressure_raw = pressure
                        use_comp = data.get(CONF_TEMP_COMPENSATION, True)
                        compensated = pressure
                        self._temp_compensated = False
                        if use_comp and self._temperature is not None:
                            compensated = self._compensate_pressure(
                                pressure, self._temperature
                            )
                            self._temp_compensated = compensated != pressure
                        self._pressure = compensated
                        self._level = self._pressure_to_level(compensated)

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

        if self._level is not None and self._level >= 95:
            now = dt_util.utcnow()
            if self._last_full is None or (now - self._last_full) > timedelta(hours=12):
                self._last_full = now

        if self._level is not None:
            self._record_level_sample(self._level)

    def _record_level_sample(self, level: float) -> None:
        """Append a level sample if enough time has passed since the last one."""
        now = dt_util.utcnow()
        if self._level_samples:
            try:
                last_ts = dt_util.parse_datetime(self._level_samples[-1][0])
                if last_ts and (now - last_ts) < timedelta(minutes=15):
                    self._level_samples[-1] = (self._level_samples[-1][0], level)
                    return
            except (TypeError, ValueError):
                pass
        self._level_samples.append((now.isoformat(), level))

    def _compensate_pressure(self, psi: float, temp: float) -> float:
        """Normalize LPG gauge pressure toward a 70°F reference.

        Saturated propane vapor pressure rises with temperature. A simple
        linear factor (~1.2% per °F around 70°F) keeps the pressure→level
        curve consistent across ambient swings.
        """
        temp_f = temp if temp > 45 else (temp * 9.0 / 5.0 + 32.0)
        temp_f = max(0.0, min(120.0, temp_f))
        factor = 1.0 + (temp_f - REF_TEMP_F) * 0.012
        if factor <= 0.3:
            return psi
        return round(psi / factor, 2)

    def _pressure_to_level(self, psi: float) -> float:
        """Map (optionally compensated) PSI to % full."""
        if psi >= 140:
            return 100.0
        if psi >= 120:
            return min(100.0, 70.0 + (psi - 120) * 1.5)
        if psi >= 100:
            return 40.0 + (psi - 100) * 1.5
        if psi >= 80:
            return 20.0 + (psi - 80) * 1.0
        if psi >= 50:
            return max(0.0, (psi - 50) * 0.66)
        return 0.0

    def _get_status(self) -> str:
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

    def _burn_rate_over_window(self, days: float) -> float | None:
        """Estimate gal/day from level samples over the given day window."""
        if self._level is None or not self._level_samples:
            return None

        now = dt_util.utcnow()
        cutoff = now - timedelta(days=days)
        window: list[tuple[datetime, float]] = []
        for ts_str, lvl in self._level_samples:
            ts = dt_util.parse_datetime(ts_str)
            if ts is None:
                continue
            if ts.tzinfo is None:
                ts = dt_util.as_utc(ts)
            if ts >= cutoff:
                window.append((ts, lvl))

        if len(window) < 2:
            return self._burn_rate_from_last_full()

        window.sort(key=lambda x: x[0])
        first_ts, first_lvl = window[0]
        last_ts, last_lvl = window[-1]
        elapsed_days = (last_ts - first_ts).total_seconds() / 86400
        if elapsed_days < 0.25:
            return self._burn_rate_from_last_full()

        used_gal = self._capacity * max(0.0, (first_lvl - last_lvl) / 100.0)
        if used_gal <= 0:
            return 0.0
        rate = used_gal / elapsed_days
        # QC: ignore impossible spikes (sensor noise / refill gaps)
        max_rate = max(self._capacity * 0.35, 2.0)
        if rate > max_rate:
            return None
        return round(rate, 2)

    def _burn_rate_from_last_full(self) -> float | None:
        days = self._days_since_full()
        if days is None or days < 0.5 or self._level is None:
            return None
        used = self._capacity * (1 - self._level / 100)
        if used <= 0:
            return 0.0
        rate = used / days
        max_rate = max(self._capacity * 0.35, 2.0)
        if rate > max_rate:
            return None
        return round(rate, 2)

    def _estimate_burn_rate(self) -> float | None:
        rate = self._burn_rate_over_window(3.0)
        if rate is not None:
            return rate
        return self._burn_rate_from_last_full()

    def _estimate_burn_rate_7d(self) -> float | None:
        return self._burn_rate_over_window(7.0)

    def _burn_rate_change_label(self) -> str | None:
        recent = self._estimate_burn_rate()
        week = self._estimate_burn_rate_7d()
        if recent is None or week is None or week <= 0:
            return None
        pct = ((recent - week) / week) * 100
        if abs(pct) < 3:
            return "Stable vs 7-day avg"
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.0f}% vs 7-day avg"

    def _days_remaining(self) -> float | None:
        rate = self._estimate_burn_rate()
        if rate is None or rate <= 0 or self._level is None:
            return None
        remaining_vol = self._capacity * (self._level / 100)
        target_vol = self._capacity * (self._threshold / 100)
        usable = remaining_vol - target_vol
        if usable <= 0:
            return 0.0
        return round(usable / rate, 1)

    def _last_full_label(self) -> str | None:
        if self._last_full is None:
            return None
        local = dt_util.as_local(self._last_full)
        return f"Last: {local.strftime('%b %d')} ({self._capacity:.1f} Gal)"

    def _shared_attrs(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            ATTR_TANK_SIZE: self._entry.data.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE),
            ATTR_CAPACITY_GALLONS: self._capacity,
            ATTR_STATUS: self._get_status(),
            ATTR_VOLUME_REMAINING: round(self._capacity * (self._level or 0) / 100, 1),
            ATTR_BURN_RATE: self._estimate_burn_rate(),
            ATTR_BURN_RATE_7D: self._estimate_burn_rate_7d(),
            ATTR_BURN_RATE_CHANGE: self._burn_rate_change_label(),
            ATTR_DAYS_SINCE_FULL: self._days_since_full(),
            ATTR_DAYS_REMAINING: self._days_remaining(),
            ATTR_LAST_FULL: self._last_full.isoformat() if self._last_full else None,
            "last_full_info": self._last_full_label(),
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
            ATTR_TEMP_COMPENSATED: self._temp_compensated,
            "connection": "Sensor",
            "level_samples": list(self._level_samples),
        }
        if self._pressure is not None:
            attrs[ATTR_PRESSURE] = self._pressure
        if self._pressure_raw is not None:
            attrs[ATTR_PRESSURE_RAW] = self._pressure_raw
        if self._temperature is not None:
            attrs["temperature"] = self._temperature
        if self._battery is not None:
            attrs["battery"] = self._battery
            attrs["battery_level"] = self._battery
        if self._signal is not None:
            attrs["signal"] = self._signal
        cfg = {**self._entry.data, **self._entry.options}
        if phone := cfg.get(CONF_SUPPLIER_PHONE):
            attrs[ATTR_SUPPLIER_PHONE] = phone
        if sname := cfg.get(CONF_SUPPLIER_NAME):
            attrs[ATTR_SUPPLIER_NAME] = sname
        return attrs


class GasTankLevelSensor(GasTankBaseSensor):
    """Main level sensor (%)."""

    _attr_name = "Level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
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
        return self._shared_attrs()


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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = self._shared_attrs()
        attrs.pop("level_samples", None)
        return attrs


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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_BURN_RATE_7D: self._estimate_burn_rate_7d(),
            ATTR_BURN_RATE_CHANGE: self._burn_rate_change_label(),
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
        }


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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_BURN_RATE: self._estimate_burn_rate(),
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
        }
