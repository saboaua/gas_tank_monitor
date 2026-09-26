"""Gas Tank Monitor integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Consistent path used for the card
CARD_URL_PATH = f"/{DOMAIN}-card"
CARD_JS = "gas-tank-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration and register the Lovelace card."""
    www_path = Path(hass.config.path(f"custom_components/{DOMAIN}/www"))

    if not www_path.exists():
        _LOGGER.error("www folder not found at %s – card will not load", www_path)
        return True

    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    CARD_URL_PATH,
                    str(www_path),
                    cache_headers=False,
                )
            ]
        )
        add_extra_js_url(hass, f"{CARD_URL_PATH}/{CARD_JS}")
        _LOGGER.info("Gas Tank Card registered at %s/%s", CARD_URL_PATH, CARD_JS)
    except Exception as err:
        _LOGGER.error("Failed to register Gas Tank Card: %s", err)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
