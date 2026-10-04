"""Gas Tank Monitor integration."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CARD_URL_PATH = f"/{DOMAIN}-card"
CARD_JS = "gas-tank-card.js"
CARD_VERSION = "2.2.5"
LOCAL_CARD_URL = f"/local/{CARD_JS}"
LOCAL_CARD_URL_V = f"{LOCAL_CARD_URL}?v={CARD_VERSION}"
STATIC_CARD_URL_V = f"{CARD_URL_PATH}/{CARD_JS}?v={CARD_VERSION}"


def _integration_www(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(f"custom_components/{DOMAIN}/www"))


def _ha_www_card_path(hass: HomeAssistant) -> Path:
    www = Path(hass.config.path("www"))
    www.mkdir(parents=True, exist_ok=True)
    return www / CARD_JS


def _copy_card_to_local(hass: HomeAssistant) -> Path | None:
    """Always overwrite config/www/gas-tank-card.js from the integration package."""
    src = _integration_www(hass) / CARD_JS
    if not src.exists():
        _LOGGER.error(
            "Card source missing at %s - reinstall the integration / HACS package",
            src,
        )
        return None
    dest = _ha_www_card_path(hass)
    try:
        shutil.copy2(src, dest)
        size = dest.stat().st_size
        _LOGGER.info(
            "Card copied to %s (%s bytes) -> browser URL %s",
            dest,
            size,
            LOCAL_CARD_URL_V,
        )
        if size < 1000:
            _LOGGER.error("Card file looks too small (%s bytes) - package may be corrupt", size)
        return dest
    except OSError:
        _LOGGER.exception("Failed to copy card to %s", dest)
        return None


async def _async_register_static(hass: HomeAssistant) -> None:
    www = _integration_www(hass)
    if not www.exists():
        _LOGGER.error("Integration www folder missing: %s", www)
        return
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL_PATH, str(www), False)]
        )
        _LOGGER.info("Static path registered: %s -> %s", CARD_URL_PATH, www)
    except RuntimeError:
        _LOGGER.debug("Static path %s already registered", CARD_URL_PATH)
    except Exception:  # noqa: BLE001
        _LOGGER.warning("StaticPathConfig failed, trying legacy", exc_info=True)
        try:
            hass.http.register_static_path(CARD_URL_PATH, str(www), cache_headers=False)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Legacy static path failed", exc_info=True)


def _inject_frontend_js(hass: HomeAssistant) -> None:
    """Load the card on every frontend page (classic + ESM attempts)."""
    for url in (LOCAL_CARD_URL_V, STATIC_CARD_URL_V):
        for esm in (True, False):
            try:
                add_extra_js_url(hass, url, esm=esm)
                _LOGGER.info("Frontend extra JS injected esm=%s url=%s", esm, url)
                return
            except TypeError:
                try:
                    add_extra_js_url(hass, url)
                    _LOGGER.info("Frontend extra JS injected (classic) url=%s", url)
                    return
                except Exception:  # noqa: BLE001
                    _LOGGER.debug("add_extra_js_url classic failed for %s", url, exc_info=True)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("add_extra_js_url esm=%s failed for %s", esm, url, exc_info=True)
    _LOGGER.warning(
        "Could not inject frontend JS - add a Lovelace resource manually: %s (JavaScript Module)",
        LOCAL_CARD_URL,
    )


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Create a storage-mode Lovelace module resource if possible."""
    try:
        lovelace_data = hass.data.get("lovelace")
        if not lovelace_data:
            _LOGGER.debug("Lovelace not ready - skip resource auto-add")
            return False

        resources = lovelace_data.get("resources")
        if resources is None:
            _LOGGER.debug("No lovelace resources collection (YAML mode?)")
            return False

        existing: list[str] = []
        if hasattr(resources, "async_items"):
            for item in resources.async_items():
                existing.append(str(item.get("url", "")).split("?", 1)[0])
        elif hasattr(resources, "data"):
            for item in resources.data or []:
                existing.append(str(item.get("url", "")).split("?", 1)[0])

        base = url.split("?", 1)[0]
        if base in existing or any(base in u for u in existing):
            _LOGGER.info("Lovelace resource already present for %s", base)
            return True

        if not hasattr(resources, "async_create_item"):
            return False

        versioned = f"{base}?v={CARD_VERSION}"
        for payload in (
            {"res_type": "module", "url": versioned},
            {"type": "module", "url": versioned},
            {"res_type": "module", "url": base},
            {"type": "module", "url": base},
        ):
            try:
                await resources.async_create_item(payload)
                _LOGGER.info("Lovelace module resource created: %s", payload)
                return True
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Resource create candidate failed %s: %s", payload, err)
        return False
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Could not auto-add Lovelace resource", exc_info=True)
        return False


async def _async_setup_card(hass: HomeAssistant) -> None:
    """Copy card, serve it, inject into frontend, register Lovelace resource."""
    await hass.async_add_executor_job(_copy_card_to_local, hass)
    await _async_register_static(hass)
    _inject_frontend_js(hass)

    ok = await _async_register_lovelace_resource(hass, LOCAL_CARD_URL)
    if not ok:
        await _async_register_lovelace_resource(hass, f"{CARD_URL_PATH}/{CARD_JS}")

    _LOGGER.info(
        "Gas Tank Card ready. Open %s in the browser - you must see JavaScript source. "
        "If the card is missing: Settings -> Dashboards -> Resources -> Add "
        "%s as JavaScript Module, then hard-refresh (Ctrl+Shift+R).",
        LOCAL_CARD_URL_V,
        LOCAL_CARD_URL,
    )


async def _async_handle_register_card(call: ServiceCall) -> None:
    """Service: gas_tank_monitor.register_card - re-copy + re-register resource."""
    await _async_setup_card(call.hass)
    _LOGGER.info("register_card service completed")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the component and card (also when no config entry yet)."""
    await _async_setup_card(hass)

    hass.services.async_register(DOMAIN, "register_card", _async_handle_register_card)

    @callback
    def _on_started(event) -> None:
        hass.async_create_task(_async_setup_card(hass))

    hass.bus.async_listen_once("homeassistant_started", _on_started)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    await _async_setup_card(hass)

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
