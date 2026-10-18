"""Einrichten in Home Assistant: Kopplungs-Code aus der K9SNTNL-App eingeben.

Den Code gibt es in der App unter „Mein Konto → Home Assistant“. Er ist 10 Minuten gültig und nur einmal nutzbar.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import K9Api, K9AuthError, K9Error, K9PairingError, K9RateLimitError
from .const import CONF_CODE, CONF_TOKEN, CONF_URL, DEFAULT_URL, DOMAIN


class K9ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _pair(self, url: str, code: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
        """Gibt (Antwort des Servers, Fehler für das Formular) zurück."""
        name = f"Home Assistant {self.hass.config.location_name}".strip()
        api = K9Api(async_get_clientsession(self.hass), url)
        try:
            return await api.pair(code.strip(), name[:100]), {}
        except K9RateLimitError:
            return None, {"base": "too_many_attempts"}
        except K9PairingError:
            return None, {"base": "invalid_code"}
        except (K9AuthError, K9Error):
            return None, {"base": "cannot_connect"}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            result, errors = await self._pair(url, user_input[CONF_CODE])
            if result is not None:
                # Ein Eintrag je K9SNTNL-Konto
                await self.async_set_unique_id(result["email"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"K9SNTNL ({result['email']})", data={CONF_URL: url, CONF_TOKEN: result["token"]}
                )
        schema = vol.Schema({
            vol.Required(CONF_CODE): str,
            vol.Required(CONF_URL, default=(user_input or {}).get(CONF_URL, DEFAULT_URL)): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Zugang ungültig (in der App getrennt, „Überall abmelden“, neues Passwort) → neu koppeln."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            result, errors = await self._pair(entry.data[CONF_URL], user_input[CONF_CODE])
            if result is not None:
                await self.async_set_unique_id(result["email"])
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(entry, data_updates={CONF_TOKEN: result["token"]})
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=vol.Schema({vol.Required(CONF_CODE): str}), errors=errors
        )
