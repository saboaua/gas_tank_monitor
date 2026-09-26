"""Config flow for Gas Tank Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_ENTITY,
    CONF_CUSTOM_GALLONS,
    CONF_LEVEL_ENTITY,
    CONF_PRESSURE_ENTITY,
    CONF_SIGNAL_ENTITY,
    CONF_SWITCH_THRESHOLD,
    CONF_TANK_SIZE,
    CONF_TEMP_ENTITY,
    DEFAULT_SWITCH_THRESHOLD,
    DEFAULT_TANK_SIZE,
    DOMAIN,
    NAME,
    TANK_SIZES,
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input."""
    return {"title": data.get(CONF_NAME, NAME)}


class GasTankMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gas Tank Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Basic validation
            if not user_input.get(CONF_PRESSURE_ENTITY) and not user_input.get(
                CONF_LEVEL_ENTITY
            ):
                errors["base"] = "need_entity"
            else:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=NAME): str,
                vol.Optional(CONF_PRESSURE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_LEVEL_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_TEMP_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_BATTERY_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SIGNAL_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_TANK_SIZE, default=DEFAULT_TANK_SIZE): vol.In(
                    list(TANK_SIZES.keys()) + ["custom"]
                ),
                vol.Optional(CONF_CUSTOM_GALLONS): vol.Coerce(float),
                vol.Optional(
                    CONF_SWITCH_THRESHOLD, default=DEFAULT_SWITCH_THRESHOLD
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=50)),
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
        """Get the options flow for this handler."""
        return GasTankMonitorOptionsFlow(config_entry)


class GasTankMonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data
        options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TANK_SIZE,
                    default=options.get(CONF_TANK_SIZE, data.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE)),
                ): vol.In(list(TANK_SIZES.keys()) + ["custom"]),
                vol.Optional(
                    CONF_CUSTOM_GALLONS,
                    default=options.get(CONF_CUSTOM_GALLONS, data.get(CONF_CUSTOM_GALLONS)),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SWITCH_THRESHOLD,
                    default=options.get(
                        CONF_SWITCH_THRESHOLD,
                        data.get(CONF_SWITCH_THRESHOLD, DEFAULT_SWITCH_THRESHOLD),
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=50)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
