"""Messwerte der Fühler: Temperatur, Luftfeuchte, Spannung, Leistung."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import K9ConfigEntry, K9Coordinator
from .entity import K9Entity, box_device, trailer_device

DEVICE_CLASSES = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "humidity": SensorDeviceClass.HUMIDITY,
    "voltage": SensorDeviceClass.VOLTAGE,
    "power": SensorDeviceClass.POWER,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: K9ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[int] = set()

    @callback
    def add_new() -> None:
        """Neu angelegte Sensoren erscheinen ohne Neustart."""
        new = []
        for trailer in coordinator.data.values():
            for sensor in trailer["sensors"]:
                if sensor["id"] not in known:
                    known.add(sensor["id"])
                    new.append(K9Sensor(coordinator, trailer["id"], sensor["id"]))
        async_add_entities(new)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class K9Sensor(K9Entity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: K9Coordinator, trailer_id: int, sensor_id: int) -> None:
        super().__init__(coordinator, trailer_id)
        self.sensor_id = sensor_id
        sensor = self.sensor
        trailer = self.trailer
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_sensor_{sensor_id}"
        self._attr_device_class = DEVICE_CLASSES.get(sensor["kind"])
        self._attr_native_unit_of_measurement = sensor["unit"]
        box = next((b for b in trailer["boxes"] if b["id"] == sensor["box_id"]), None)
        name = sensor["name"]
        # „Box 1 Temperatur“ am Gerät „Unser Anhänger Box 1“ → nur „Temperatur“
        if box and name.startswith(f"{box['name']} ") and len(name) > len(box["name"]) + 1:
            name = name[len(box["name"]) + 1:]
        self._attr_name = name
        self._attr_device_info = box_device(trailer, box) if box else trailer_device(trailer)

    @property
    def sensor(self) -> dict[str, Any] | None:
        trailer = self.trailer
        if trailer is None:
            return None
        return next((s for s in trailer["sensors"] if s["id"] == self.sensor_id), None)

    @property
    def available(self) -> bool:
        return super().available and self.sensor is not None

    @property
    def native_value(self) -> float | None:
        sensor = self.sensor
        return sensor["last_value"] if sensor else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        sensor = self.sensor
        if sensor is None:
            return None
        return {
            "measured_at": sensor["last_time"],
            "alert": sensor["alert"],  # ok, high (über der Grenze) oder low (darunter)
            "min_value": sensor["min_value"],
            "max_value": sensor["max_value"],
        }
