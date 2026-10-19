"""Gemeinsame Grundlage der Entitäten: Geräte für Anhänger und Boxen."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import K9Coordinator


def trailer_device(trailer: dict[str, Any]) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, trailer["identifier"])},
        name=trailer["name"],
        manufacturer="K9SNTNL",
        model="Anhänger",
        serial_number=trailer["identifier"],
    )


def box_device(trailer: dict[str, Any], box: dict[str, Any]) -> DeviceInfo:
    """Jede Box ist ein eigenes Gerät „am“ Anhänger (z. B. „Unser Anhänger Box 1“).

    Die Verbindung zum Anhänger setzt `register_devices` – nicht über `via_device` hier, denn das
    lehnen neuere Home-Assistant-Versionen ab („use via_device_id instead“)."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{trailer['identifier']}-box-{box['id']}")},
        name=f"{trailer['name']} {box['name']}",
        manufacturer="K9SNTNL",
        model="Box",
    )


@callback
def register_devices(hass: HomeAssistant, coordinator: K9Coordinator) -> None:
    """Anhänger und Boxen als Geräte anlegen, bevor Entitäten sie nennen; Boxen hängen am Anhänger."""
    registry = dr.async_get(hass)
    entry_id = coordinator.config_entry.entry_id
    for trailer in coordinator.data.values():
        parent = registry.async_get_or_create(config_entry_id=entry_id, **trailer_device(trailer))
        for box in trailer["boxes"]:
            device = registry.async_get_or_create(config_entry_id=entry_id, **box_device(trailer, box))
            if device.via_device_id != parent.id:
                registry.async_update_device(device.id, via_device_id=parent.id)


class K9Entity(CoordinatorEntity[K9Coordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: K9Coordinator, trailer_id: int) -> None:
        super().__init__(coordinator)
        self.trailer_id = trailer_id

    @property
    def trailer(self) -> dict[str, Any] | None:
        return self.coordinator.data.get(self.trailer_id)

    @property
    def available(self) -> bool:
        return super().available and self.trailer is not None
