"""Config flow for Gas Tank Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
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
    NAME,
    TANK_SIZES,
)

_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)


def _merged(entry: config_entries.ConfigEntry) -> dict[str, Any]:
    """Options override data."""
    return {**entry.data, **entry.options}


class GasTankMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gas Tank Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_PRESSURE_ENTITY) and not user_input.get(
                CONF_LEVEL_ENTITY
            ):
                errors["base"] = "need_entity"
            else:
                title = user_input.get(CONF_NAME) or NAME
                return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=NAME): str,
                vol.Optional(CONF_PRESSURE_ENTITY): _SENSOR_SELECTOR,
                vol.Optional(CONF_LEVEL_ENTITY): _SENSOR_SELECTOR,
                vol.Optional(CONF_TEMP_ENTITY): _SENSOR_SELECTOR,
                vol.Optional(CONF_BATTERY_ENTITY): _SENSOR_SELECTOR,
                vol.Optional(CONF_SIGNAL_ENTITY): _SENSOR_SELECTOR,
                vol.Required(CONF_TANK_SIZE, default=DEFAULT_TANK_SIZE): vol.In(
                    list(TANK_SIZES.keys()) + ["custom"]
                ),
                vol.Optional(CONF_CUSTOM_GALLONS): vol.Coerce(float),
                vol.Optional(
                    CONF_SWITCH_THRESHOLD, default=DEFAULT_SWITCH_THRESHOLD
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=50)),
                vol.Optional(CONF_TEMP_COMPENSATION, default=True): bool,
                vol.Optional(CONF_SUPPLIER_NAME): str,
                vol.Optional(CONF_SUPPLIER_PHONE): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow."""
        return GasTankMonitorOptionsFlow()


class GasTankMonitorOptionsFlow(config_entries.OptionsFlow):
    """Full options — change sensors without reinstalling."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show and save all settings including linked sensors."""
        errors: dict[str, str] = {}
        current = _merged(self.config_entry)

        if user_input is not None:
            if not user_input.get(CONF_PRESSURE_ENTITY) and not user_input.get(
                CONF_LEVEL_ENTITY
            ):
                errors["base"] = "need_entity"
            else:
                # Persist full options (sensors + tank + supplier)
                return self.async_create_entry(title="", data=user_input)

        def _opt(key: str, fallback: Any = vol.UNDEFINED):
            val = current.get(key, fallback)
            if val is None or val == "":
                return vol.Optional(key)
            return vol.Optional(key, default=val)

        data_schema = vol.Schema(
            {
                # --- Sensors (always visible) ---
                _opt(CONF_PRESSURE_ENTITY): _SENSOR_SELECTOR,
                _opt(CONF_LEVEL_ENTITY): _SENSOR_SELECTOR,
                _opt(CONF_TEMP_ENTITY): _SENSOR_SELECTOR,
                _opt(CONF_BATTERY_ENTITY): _SENSOR_SELECTOR,
                _opt(CONF_SIGNAL_ENTITY): _SENSOR_SELECTOR,
                # --- Tank ---
                vol.Optional(
                    CONF_TANK_SIZE,
                    default=current.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE),
                ): vol.In(list(TANK_SIZES.keys()) + ["custom"]),
                _opt(CONF_CUSTOM_GALLONS): vol.Coerce(float),
                vol.Optional(
                    CONF_SWITCH_THRESHOLD,
                    default=current.get(
                        CONF_SWITCH_THRESHOLD, DEFAULT_SWITCH_THRESHOLD
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=50)),
                vol.Optional(
                    CONF_TEMP_COMPENSATION,
                    default=current.get(CONF_TEMP_COMPENSATION, True),
                ): bool,
                # --- Supplier ---
                vol.Optional(
                    CONF_SUPPLIER_NAME,
                    default=current.get(CONF_SUPPLIER_NAME, ""),
                ): str,
                vol.Optional(
                    CONF_SUPPLIER_PHONE,
                    default=current.get(CONF_SUPPLIER_PHONE, ""),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
