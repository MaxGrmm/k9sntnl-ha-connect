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
    """Jede Box ist ein eigenes Gerät „am“ Anhänger (z. B. „Unser Anhänger Box 1“)."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{trailer['identifier']}-box-{box['id']}")},
        name=f"{trailer['name']} {box['name']}",
        manufacturer="K9SNTNL",
        model="Box",
        via_device=(DOMAIN, trailer["identifier"]),
    )


@callback
def register_trailers(hass: HomeAssistant, coordinator: K9Coordinator) -> None:
    """Anhänger als Geräte anlegen, bevor die Boxen sie als übergeordnetes Gerät nennen."""
    registry = dr.async_get(hass)
    for trailer in coordinator.data.values():
        registry.async_get_or_create(config_entry_id=coordinator.config_entry.entry_id, **trailer_device(trailer))


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
