"""Gas Tank Monitor integration."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Served both from integration static path AND /local/ for reliability
CARD_URL_PATH = f"/{DOMAIN}-card"
CARD_JS = "gas-tank-card.js"
CARD_VERSION = "2.2.4"
# /local/ is the HA www folder — most reliable for Lovelace modules
LOCAL_CARD_URL = f"/local/{CARD_JS}"


def _integration_www(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(f"custom_components/{DOMAIN}/www"))


def _ha_www_card_path(hass: HomeAssistant) -> Path:
    """config/www/gas-tank-card.js — served at /local/gas-tank-card.js."""
    www = Path(hass.config.path("www"))
    www.mkdir(parents=True, exist_ok=True)
    return www / CARD_JS


def _copy_card_to_local(hass: HomeAssistant) -> Path | None:
    """Copy card JS into config/www so /local/ always works."""
    src = _integration_www(hass) / CARD_JS
    if not src.exists():
        _LOGGER.error("Card source missing: %s", src)
        return None
    dest = _ha_www_card_path(hass)
    try:
        shutil.copy2(src, dest)
        _LOGGER.info("Card copied to %s (URL %s)", dest, LOCAL_CARD_URL)
        return dest
    except OSError:
        _LOGGER.exception("Failed to copy card to %s", dest)
        return None


async def _async_register_static(hass: HomeAssistant) -> None:
    """Serve custom_components/.../www at /gas_tank_monitor-card/."""
    www = _integration_www(hass)
    if not www.exists():
        return
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL_PATH, str(www), False)]
        )
    except RuntimeError:
        _LOGGER.debug("Static path %s already registered", CARD_URL_PATH)
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Static path registration failed", exc_info=True)
        try:
            hass.http.register_static_path(
                CARD_URL_PATH, str(www), cache_headers=False
            )
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Legacy static path failed", exc_info=True)


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Add a Lovelace dashboard resource if storage mode is available."""
    try:
        lovelace_data = hass.data.get("lovelace")
        if not lovelace_data:
            _LOGGER.debug("Lovelace not ready yet — skip resource auto-add")
            return False

        resources = lovelace_data.get("resources")
        if resources is None:
            return False

        # Already present?
        existing_urls: list[str] = []
        if hasattr(resources, "async_items"):
            for item in resources.async_items():
                existing_urls.append(str(item.get("url", "")).split("?", 1)[0])
        elif hasattr(resources, "data"):
            for item in resources.data or []:
                existing_urls.append(str(item.get("url", "")).split("?", 1)[0])

        base = url.split("?", 1)[0]
        if base in existing_urls or any(base in u for u in existing_urls):
            _LOGGER.debug("Lovelace resource already present: %s", base)
            return True

        # Storage collection API (HA storage-mode dashboards)
        if hasattr(resources, "async_create_item"):
            # Prefer versioned URL so browsers pick up updates after upgrade
            versioned = f"{base}?v={CARD_VERSION}"
            candidates = [
                {"res_type": "module", "url": versioned},
                {"type": "module", "url": versioned},
                {"res_type": "module", "url": base},
                {"type": "module", "url": base},
            ]
            last_err: Exception | None = None
            for payload in candidates:
                try:
                    await resources.async_create_item(payload)
                    _LOGGER.info("Lovelace resource created: %s", payload)
                    return True
                except Exception as err:  # noqa: BLE001
                    last_err = err
                    continue
            if last_err:
                _LOGGER.warning("Lovelace resource create failed: %s", last_err)
            return False

        _LOGGER.debug("Lovelace resources not writable (YAML mode?)")
        return False
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Could not auto-add Lovelace resource", exc_info=True)
        return False


async def _async_setup_card(hass: HomeAssistant) -> None:
    """Make the card loadable: /local copy + static path + inject + resource."""
    # 1) Always copy into config/www → /local/gas-tank-card.js
    await hass.async_add_executor_job(_copy_card_to_local, hass)

    # 2) Also serve from integration path
    await _async_register_static(hass)

    # 3) Inject on every frontend page (module preferred — required for picker)
    urls = (
        f"{LOCAL_CARD_URL}?v={CARD_VERSION}",
        f"{CARD_URL_PATH}/{CARD_JS}?v={CARD_VERSION}",
    )
    for url in urls:
        loaded = False
        # Prefer ESM so Lovelace treats it like a dashboard module resource
        for kwargs in ({"esm": True}, {}):
            try:
                add_extra_js_url(hass, url, **kwargs)
                _LOGGER.info("Frontend extra JS (%s): %s", kwargs or "classic", url)
                loaded = True
                break
            except TypeError:
                # Older HA: add_extra_js_url(hass, url) only
                continue
            except Exception:  # noqa: BLE001
                _LOGGER.debug("add_extra_js_url failed for %s %s", url, kwargs, exc_info=True)
        if not loaded:
            try:
                add_extra_js_url(hass, url)
                _LOGGER.info("Frontend extra JS (fallback): %s", url)
            except Exception:  # noqa: BLE001
                _LOGGER.warning("add_extra_js_url failed for %s", url, exc_info=True)

    # 4) Auto-register Lovelace resource (storage mode) — this is what
    #    makes the card appear under "By card" / Custom in the picker.
    for res_url in (LOCAL_CARD_URL, f"{CARD_URL_PATH}/{CARD_JS}"):
        if await _async_register_lovelace_resource(hass, res_url):
            break

    _LOGGER.info(
        "Gas Tank Card setup done. Prefer resource URL: %s "
        "(Settings → Dashboards → Resources if card still missing)",
        LOCAL_CARD_URL,
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the component and card."""
    await _async_setup_card(hass)

    # Retry lovelace resource once frontend/lovelace is fully up
    @callback
    def _on_started(event) -> None:
        hass.async_create_task(
            _async_register_lovelace_resource(hass, LOCAL_CARD_URL)
        )

    hass.bus.async_listen_once("homeassistant_started", _on_started)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    # Ensure card files are in place even if async_setup order differed
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
