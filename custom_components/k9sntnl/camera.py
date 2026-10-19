"""Kameras als Kamera-Entitäten: Live-Bild (HLS) über den K9SNTNL-Server.

Das Bild kommt aus dem Anhänger über LTE. Damit kein Datenvolumen verloren geht, holt Home Assistant
das Live-Bild nur, solange jemand zuschaut. Standbilder (Vorschau, Kacheln) kommen vom Server
(`GET /cameras/{id}/snapshot`): Er macht je Kamera höchstens alle 30–90 s ein neues – wie oft, stellt
der Eigentümer in der K9SNTNL-App ein – und nur, solange jemand fragt.

Die Video-Adresse enthält ein kurzlebiges Token (10 Minuten zum Öffnen). Ein laufendes Bild bleibt
danach offen; für den nächsten Start holt die Integration rechtzeitig eine neue Adresse.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import K9Error
from .coordinator import K9ConfigEntry, K9Coordinator
from .entity import K9Entity, box_device, trailer_device

_LOGGER = logging.getLogger(__name__)

# Vor Ablauf des Tokens (10 Minuten) eine neue Adresse holen
SOURCE_MAX_AGE = 8 * 60


async def async_setup_entry(
    hass: HomeAssistant, entry: K9ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[int] = set()

    @callback
    def add_new() -> None:
        new = []
        for trailer in coordinator.data.values():
            for camera in trailer["cameras"]:
                if camera["id"] not in known:
                    known.add(camera["id"])
                    new.append(K9Camera(coordinator, trailer["id"], camera["id"]))
        async_add_entities(new)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class K9Camera(K9Entity, Camera):
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, coordinator: K9Coordinator, trailer_id: int, camera_id: int) -> None:
        K9Entity.__init__(self, coordinator, trailer_id)
        Camera.__init__(self)
        self.camera_id = camera_id
        camera = self.camera
        trailer = self.trailer
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_camera_{camera_id}"
        box = next((b for b in trailer["boxes"] if b["id"] == camera["box_id"]), None)
        name = camera["name"]
        if box and name.startswith(f"{box['name']} ") and len(name) > len(box["name"]) + 1:
            name = name[len(box["name"]) + 1:]
        self._attr_name = name
        self._attr_device_info = box_device(trailer, box) if box else trailer_device(trailer)
        self._source_time = 0.0  # wann die aktuelle Video-Adresse geholt wurde

    @property
    def camera(self) -> dict[str, Any] | None:
        trailer = self.trailer
        if trailer is None:
            return None
        return next((c for c in trailer["cameras"] if c["id"] == self.camera_id), None)

    @property
    def available(self) -> bool:
        return super().available and self.camera is not None

    async def stream_source(self) -> str | None:
        """Frische Video-Adresse – oder None, wenn die Kamera noch nicht eingerichtet ist."""
        try:
            url = await self.coordinator.api.stream_url(self.camera_id)
        except K9Error as error:
            _LOGGER.debug("Keine Video-Adresse für Kamera %s: %s", self.camera_id, error)
            return None
        self._source_time = time.monotonic()
        return url

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Standbild vom Server (siehe oben); Home Assistant verkleinert es bei Bedarf selbst."""
        try:
            return await self.coordinator.api.snapshot(self.camera_id)
        except K9Error as error:
            _LOGGER.debug("Kein Standbild für Kamera %s: %s", self.camera_id, error)
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        super()._handle_coordinator_update()
        if self.stream is not None and needs_new_source(self.stream, self._source_time):
            self.hass.async_create_task(self._refresh_source())

    async def _refresh_source(self) -> None:
        url = await self.stream_source()
        if url is not None and self.stream is not None:
            self.stream.update_source(url)


def needs_new_source(stream: Any, source_time: float) -> bool:
    """Neue Adresse holen, wenn die alte bald abläuft und gerade niemand zuschaut – oder das Bild abgerissen ist.
    Ein laufendes Bild wird nicht unterbrochen: Der Server merkt sich die Sitzung nach dem Öffnen."""
    if time.monotonic() - source_time < SOURCE_MAX_AGE:
        return False
    return not stream.outputs() or not stream.available
