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


def _entity_schema_optional(default: str | None = None):
    """Build an optional entity selector field, with default when known."""
    if default:
        return vol.Optional(
            # placeholder key filled by caller
        )
    return vol.Optional


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
    """Handle options — full reconfiguration without reinstall."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options including linked sensors."""
        errors: dict[str, str] = {}

        data = self.config_entry.data
        options = self.config_entry.options

        def _get(key, default=None):
            return options.get(key, data.get(key, default))

        if user_input is not None:
            if not user_input.get(CONF_PRESSURE_ENTITY) and not user_input.get(
                CONF_LEVEL_ENTITY
            ):
                errors["base"] = "need_entity"
            else:
                # Options fully replace previous options; sensors read
                # {**entry.data, **entry.options} so these take precedence.
                return self.async_create_entry(title="", data=user_input)

        schema: dict[Any, Any] = {}

        # --- Linked sensors (editable without reinstall) ---
        for key in (
            CONF_PRESSURE_ENTITY,
            CONF_LEVEL_ENTITY,
            CONF_TEMP_ENTITY,
            CONF_BATTERY_ENTITY,
            CONF_SIGNAL_ENTITY,
        ):
            current = _get(key)
            field = (
                vol.Optional(key, default=current)
                if current
                else vol.Optional(key)
            )
            schema[field] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )

        # --- Tank / thresholds / supplier ---
        schema[
            vol.Optional(
                CONF_TANK_SIZE,
                default=_get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE),
            )
        ] = vol.In(list(TANK_SIZES.keys()) + ["custom"])

        custom_gal = _get(CONF_CUSTOM_GALLONS)
        if custom_gal is not None:
            schema[vol.Optional(CONF_CUSTOM_GALLONS, default=custom_gal)] = (
                vol.Coerce(float)
            )
        else:
            schema[vol.Optional(CONF_CUSTOM_GALLONS)] = vol.Coerce(float)

        schema[
            vol.Optional(
                CONF_SWITCH_THRESHOLD,
                default=_get(CONF_SWITCH_THRESHOLD, DEFAULT_SWITCH_THRESHOLD),
            )
        ] = vol.All(vol.Coerce(int), vol.Range(min=5, max=50))

        schema[
            vol.Optional(
                CONF_TEMP_COMPENSATION,
                default=_get(CONF_TEMP_COMPENSATION, True),
            )
        ] = bool

        schema[
            vol.Optional(
                CONF_SUPPLIER_NAME,
                default=_get(CONF_SUPPLIER_NAME, ""),
            )
        ] = str

        schema[
            vol.Optional(
                CONF_SUPPLIER_PHONE,
                default=_get(CONF_SUPPLIER_PHONE, ""),
            )
        ] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
        )
