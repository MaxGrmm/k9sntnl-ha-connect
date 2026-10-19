"""Fragt alle 30 Sekunden die Anhänger ab und verteilt die Werte an die Entitäten."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import K9Api, K9AuthError, K9Error
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type K9ConfigEntry = ConfigEntry[K9Coordinator]


class K9Coordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Daten: Anhänger-ID → Anhänger (wie GET /trailers/{id})."""

    config_entry: K9ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: K9ConfigEntry, api: K9Api) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            trailers = await self.api.trailers()
        except K9AuthError as error:
            # Home Assistant bittet dann darum, mit einem neuen Code erneut zu koppeln
            raise ConfigEntryAuthFailed("Verbindung in der K9SNTNL-App getrennt oder abgelaufen") from error
        except K9Error as error:
            raise UpdateFailed(str(error)) from error
        return {trailer["id"]: trailer for trailer in trailers}
