"""K9SNTNL: Anhänger mit Sensoren (und später Kameras) in Home Assistant."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import K9Api
from .const import CONF_TOKEN, CONF_URL
from .coordinator import K9ConfigEntry, K9Coordinator
from .entity import register_devices

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CAMERA, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: K9ConfigEntry) -> bool:
    api = K9Api(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_TOKEN])
    coordinator = K9Coordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    register_devices(hass, coordinator)
    # Neue Anhänger und Boxen zuerst als Gerät anlegen (dieser Listener läuft vor denen der Plattformen)
    entry.async_on_unload(coordinator.async_add_listener(lambda: register_devices(hass, coordinator)))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: K9ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
