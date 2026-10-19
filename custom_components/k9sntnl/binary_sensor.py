"""Online-Status je Anhänger: Sensoren (ESP32/MQTT) und Anhänger selbst (LTE-Router im Tunnel)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import K9ConfigEntry, K9Coordinator
from .entity import K9Entity, trailer_device

# Feld in der Antwort → Übersetzungsschlüssel (translations/*.json)
STATUS_FIELDS = {"status": "sensors_online", "tunnel_status": "trailer_online"}


async def async_setup_entry(
    hass: HomeAssistant, entry: K9ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[tuple[int, str]] = set()

    @callback
    def add_new() -> None:
        new = []
        for trailer in coordinator.data.values():
            for field in STATUS_FIELDS:
                # „disabled“ = Überwachung aus bzw. kein Tunnel hinterlegt → keine Entität
                if trailer.get(field, "disabled") != "disabled" and (trailer["id"], field) not in known:
                    known.add((trailer["id"], field))
                    new.append(K9Online(coordinator, trailer["id"], field))
        async_add_entities(new)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class K9Online(K9Entity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: K9Coordinator, trailer_id: int, field: str) -> None:
        super().__init__(coordinator, trailer_id)
        self.field = field
        self._attr_translation_key = STATUS_FIELDS[field]
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{STATUS_FIELDS[field]}_{trailer_id}"
        self._attr_device_info = trailer_device(self.trailer)

    @property
    def is_on(self) -> bool | None:
        status = self.trailer.get(self.field) if self.trailer else None
        if status in ("online", "offline"):
            return status == "online"
        return None  # unknown: noch nie Daten empfangen
