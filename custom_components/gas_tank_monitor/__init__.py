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

CARD_URL_PATH = f"/{DOMAIN}-card"
CARD_JS = "gas-tank-card.js"
CARD_VERSION = "2.1.0"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration and register the Lovelace card."""
    www_path = Path(hass.config.path(f"custom_components/{DOMAIN}/www"))

    if not www_path.exists():
        _LOGGER.error("www folder not found at %s – card will not load", www_path)
        return True

    js_url = f"{CARD_URL_PATH}/{CARD_JS}?v={CARD_VERSION}"

    # Step 1: serve the www folder. Split into its own try/except so a
    # failure here (e.g. "static path already registered" on a reload)
    # can't silently prevent step 2 from running.
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
    except RuntimeError:
        # Already registered (e.g. integration reloaded without a full HA
        # restart) — harmless, the path is still serving the file.
        _LOGGER.debug("Static path %s already registered", CARD_URL_PATH)
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Gas Tank Card: failed to register static path %s — "
            "the card file will not be reachable at %s",
            CARD_URL_PATH,
            js_url,
            exc_info=True,
        )
        return True

    # Step 2: inject the card script on every frontend page (cache-busted).
    # This requires the `frontend` component's data structures to already
    # exist, which is why "frontend" must be listed in manifest.json
    # dependencies — without it this call can fail before frontend finishes
    # loading, and previously that failure was swallowed silently.
    try:
        add_extra_js_url(hass, js_url)
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Gas Tank Card: failed to auto-register the card script (%s). "
            "Add it manually instead: Settings → Dashboards → Resources → "
            "Add Resource → URL '%s' → Type 'JavaScript Module'.",
            js_url,
            js_url,
            exc_info=True,
        )
        return True

    _LOGGER.info(
        "Gas Tank Card registered → %s (open this URL in your browser to verify)",
        js_url,
    )
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
