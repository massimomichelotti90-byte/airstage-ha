"""Config flow for AIRSTAGE Cloud."""

from __future__ import annotations

import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AirstageApi, InvalidAuth
from .const import CONF_BASE_URL, CONF_COUNTRY, CONF_LANGUAGE, DEFAULT_COUNTRY, DEFAULT_LANGUAGE, DOMAIN, REGIONS


class AirstageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            region_url = REGIONS[user_input[CONF_BASE_URL]]
            api = AirstageApi(async_get_clientsession(self.hass), region_url,
                              user_input[CONF_USERNAME], user_input[CONF_PASSWORD],
                              user_input[CONF_COUNTRY], user_input[CONF_LANGUAGE])
            try:
                devices = await api.devices()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except (ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Fujitsu AIRSTAGE Cloud",
                        data={**user_input, CONF_BASE_URL: region_url},
                    )

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default="Europe"): vol.In(list(REGIONS)),
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): str,
            vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data):
        """Start a flow to reauthenticate an existing account."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for a new password and validate it against AIRSTAGE Cloud."""
        entry = self._get_reauth_entry()
        errors = {}

        if user_input is not None:
            data = entry.data
            api = AirstageApi(
                async_get_clientsession(self.hass),
                data[CONF_BASE_URL],
                data[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                data[CONF_COUNTRY],
                data[CONF_LANGUAGE],
            )
            try:
                await api.devices()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except (ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={"email": entry.data[CONF_USERNAME]},
        )
