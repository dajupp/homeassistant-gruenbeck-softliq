"""Diagnostics for the Gruenbeck softliQ integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the latest values and last successful poll time."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "host": coordinator.host,
        "last_successful_update": (
            coordinator.last_successful_update.isoformat()
            if coordinator.last_successful_update
            else None
        ),
        "last_update_success": coordinator.last_update_success,
        "values": coordinator.data,
    }