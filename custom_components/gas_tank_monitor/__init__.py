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

# URL path used to serve the card
CARD_URL_PATH = f"/{DOMAIN}-card"
CARD_JS = "gas-tank-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Gas Tank Monitor component and register the Lovelace card."""
    www_path = Path(hass.config.path(f"custom_components/{DOMAIN}/www"))

    if not www_path.exists():
        _LOGGER.error("www folder not found at %s – card will not load", www_path)
        return True

    # Register static path so the browser can fetch the JS
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL_PATH,
                str(www_path),
                cache_headers=False,
            )
        ]
    )

    # Tell the frontend to load the card JS on every page
    add_extra_js_url(hass, f"{CARD_URL_PATH}/{CARD_JS}")

    _LOGGER.info(
        "Gas Tank Monitor card registered → %s/%s",
        CARD_URL_PATH,
        CARD_JS,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gas Tank Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
