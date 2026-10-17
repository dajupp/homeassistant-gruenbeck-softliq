"""Config and options flows for Gruenbeck softliQ."""

from __future__ import annotations

import ipaddress

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import DOMAIN


def _validated_host(value: str) -> str:
    """Normalize and validate an IPv4 or IPv6 address."""
    return ipaddress.ip_address(value.strip()).compressed


class GruenbeckConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial setup of a softliQ device."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask for the device IP address."""
        errors = {}
        if user_input is not None:
            try:
                host = _validated_host(user_input[CONF_HOST])
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Gruenbeck softliQ ({host})",
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create an options flow for changing the device IP address."""
        return GruenbeckOptionsFlow(config_entry)


class GruenbeckOptionsFlow(config_entries.OptionsFlow):
    """Allow changing the IP address after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Update the device IP address."""
        errors = {}
        current_host = self.config_entry.options.get(
            CONF_HOST, self.config_entry.data[CONF_HOST]
        )
        if user_input is not None:
            try:
                host = _validated_host(user_input[CONF_HOST])
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            else:
                return self.async_create_entry(title="", data={CONF_HOST: host})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_HOST, default=current_host): str}
            ),
            errors=errors,
        )