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
CARD_VERSION = "2.2.11"
LOCAL_CARD_URL = f"/local/{CARD_JS}"
# Versioned URL used for resources / cache bust
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
            "Card source missing at %s — reinstall the integration / HACS package",
            src,
        )
        return None
    dest = _ha_www_card_path(hass)
    try:
        shutil.copy2(src, dest)
        size = dest.stat().st_size
        _LOGGER.info(
            "Card copied to %s (%s bytes) → browser URL %s",
            dest,
            size,
            LOCAL_CARD_URL_V,
        )
        if size < 1000:
            _LOGGER.error("Card file looks too small (%s bytes) — package may be corrupt", size)
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
        _LOGGER.info("Static path registered: %s → %s", CARD_URL_PATH, www)
    except RuntimeError:
        _LOGGER.debug("Static path %s already registered", CARD_URL_PATH)
    except Exception:  # noqa: BLE001
        _LOGGER.warning("StaticPathConfig failed, trying legacy", exc_info=True)
        try:
            hass.http.register_static_path(CARD_URL_PATH, str(www), cache_headers=False)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Legacy static path failed", exc_info=True)


def _inject_frontend_js(hass: HomeAssistant) -> None:
    """Load the card on every frontend page.

    Prefer classic script (esm=False) first — our card is not an ES module.
    ESM-first can leave customElements undefined on some HA/browser combos.
    """
    for url in (LOCAL_CARD_URL_V, STATIC_CARD_URL_V, LOCAL_CARD_URL, f"{CARD_URL_PATH}/{CARD_JS}"):
        # Classic first, then ESM
        for esm in (False, True):
            try:
                add_extra_js_url(hass, url, esm=esm)
                _LOGGER.info("Frontend extra JS injected esm=%s url=%s", esm, url)
                return
            except TypeError:
                # HA without esm kwarg — classic only
                try:
                    add_extra_js_url(hass, url)
                    _LOGGER.info("Frontend extra JS injected (classic) url=%s", url)
                    return
                except Exception:  # noqa: BLE001
                    _LOGGER.debug("add_extra_js_url classic failed for %s", url, exc_info=True)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("add_extra_js_url esm=%s failed for %s", esm, url, exc_info=True)
    _LOGGER.warning(
        "Could not inject frontend JS — add a Lovelace resource manually: %s (JavaScript Module)",
        LOCAL_CARD_URL,
    )


def _is_our_card_resource(url: str) -> bool:
    """True if this Lovelace resource URL is our gas-tank-card.js (any version/path)."""
    u = str(url or "").split("?", 1)[0].lower()
    return "gas-tank-card.js" in u


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Ensure exactly ONE storage-mode Lovelace module resource for the card.

    Deletes duplicate / old ?v= entries so only the current CARD_VERSION remains.
    The file on disk is always a single www/gas-tank-card.js (overwritten on copy).
    """
    try:
        lovelace_data = hass.data.get("lovelace")
        if not lovelace_data:
            _LOGGER.debug("Lovelace not ready — skip resource auto-add")
            return False

        # lovelace_data can be a dict (older HA) OR a LovelaceData dataclass
        if isinstance(lovelace_data, dict):
            resources = lovelace_data.get("resources")
        else:
            resources = getattr(lovelace_data, "resources", None)
        if resources is None:
            _LOGGER.debug("No lovelace resources collection (YAML mode?)")
            return False

        base = url.split("?", 1)[0]
        versioned = f"{base}?v={CARD_VERSION}"

        # Collect matching items: {id, url, raw}
        matches: list[dict] = []
        items_iter = []
        if hasattr(resources, "async_items"):
            items_iter = list(resources.async_items())
        elif hasattr(resources, "data") and resources.data is not None:
            items_iter = list(resources.data)

        for item in items_iter:
            if not isinstance(item, dict):
                continue
            item_url = str(item.get("url", ""))
            if _is_our_card_resource(item_url):
                matches.append(item)

        # Prefer item whose base path matches the requested URL; else any ours
        preferred = [m for m in matches if m.get("url", "").split("?", 1)[0] == base]
        others = [m for m in matches if m not in preferred]
        ordered = preferred + others

        # Delete duplicates (keep at most one)
        keep = ordered[0] if ordered else None
        for extra in ordered[1:]:
            item_id = extra.get("id")
            if item_id is not None and hasattr(resources, "async_delete_item"):
                try:
                    await resources.async_delete_item(item_id)
                    _LOGGER.info("Removed duplicate Lovelace resource %s", extra.get("url"))
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Could not delete resource %s: %s", item_id, err)

        # Update kept item to current versioned URL
        if keep is not None:
            item_id = keep.get("id")
            current = str(keep.get("url", ""))
            if current == versioned or current == base:
                _LOGGER.info("Lovelace resource already current: %s", current)
                return True
            if item_id is not None and hasattr(resources, "async_update_item"):
                for payload in (
                    {"res_type": "module", "url": versioned},
                    {"type": "module", "url": versioned},
                    {"url": versioned},
                ):
                    try:
                        await resources.async_update_item(item_id, payload)
                        _LOGGER.info(
                            "Updated Lovelace resource %s → %s", current, versioned
                        )
                        return True
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug("Resource update failed %s: %s", payload, err)
            # Could not update — still counts as present (user may edit manually)
            _LOGGER.info(
                "Card resource present as %s (wanted %s) — edit Resources if stale",
                current,
                versioned,
            )
            return True

        # No existing entry — create one
        if not hasattr(resources, "async_create_item"):
            return False

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
    """Copy card, serve it, register ONE load path (resource preferred).

    Dual load (add_extra_js_url + module resource) causes the browser to
    execute the script twice → customElements.define races → intermittent
    "Custom element doesn't exist" / config errors. Prefer a single path.
    """
    await hass.async_add_executor_job(_copy_card_to_local, hass)
    await _async_register_static(hass)

    # Prefer Lovelace resource (stable, one load). Only inject if that fails.
    ok = await _async_register_lovelace_resource(hass, LOCAL_CARD_URL)
    if not ok:
        ok = await _async_register_lovelace_resource(hass, f"{CARD_URL_PATH}/{CARD_JS}")
    if not ok:
        _inject_frontend_js(hass)
        _LOGGER.warning(
            "No Lovelace resource registered — fell back to frontend inject. "
            "Prefer adding %s as JavaScript Module under Dashboards → Resources.",
            LOCAL_CARD_URL,
        )
    else:
        _LOGGER.info(
            "Lovelace resource OK for %s — skipping frontend inject (avoids double-load).",
            LOCAL_CARD_URL_V,
        )

    _LOGGER.info(
        "Gas Tank Card ready. Open %s in the browser — you must see JavaScript source. "
        "Keep exactly ONE resource for this URL. If unstable: Dashboards → Resources "
        "and remove duplicates, then hard-refresh (Ctrl+Shift+R).",
        LOCAL_CARD_URL_V,
    )


async def _async_handle_register_card(call: ServiceCall) -> None:
    """Service: gas_tank_monitor.register_card — re-copy + re-register resource."""
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
