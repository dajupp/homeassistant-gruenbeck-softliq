"""Gruenbeck softliQ integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .coordinator import GruenbeckDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured softliQ device."""
    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    coordinator = GruenbeckDataUpdateCoordinator(hass, host)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("gruenbeck_softliq", {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a softliQ config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    hass.data["gruenbeck_softliq"].pop(entry.entry_id)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)