"""Tests: Kameras – Live-Bild mit kurzlebiger Adresse, kein Datenverbrauch ohne Zuschauer."""

import secrets
import time

from homeassistant.components.camera import async_get_image
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest

from custom_components.k9sntnl import camera as camera_module
from custom_components.k9sntnl.const import DOMAIN

from .conftest import URL
from .test_sensors import setup


def camera_entity(hass, entry, camera_id):
    entity_id = er.async_get(hass).async_get_entity_id("camera", DOMAIN, f"{entry.unique_id}_camera_{camera_id}")
    return entity_id, hass.data["camera"].get_entity(entity_id)


async def test_kameras_als_entitaeten(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry)
    box_cam, _ = camera_entity(hass, entry, 50)
    rear, _ = camera_entity(hass, entry, 51)
    assert hass.states.get(box_cam).attributes["friendly_name"] == "Unser Anhänger Box 1 Kamera"
    assert hass.states.get(rear).attributes["friendly_name"] == "Unser Anhänger Rückfahrkamera"
    registry, devices = er.async_get(hass), dr.async_get(hass)
    assert registry.async_get(box_cam).device_id == devices.async_get_device({(DOMAIN, "k9-0001-box-10")}).id
    assert registry.async_get(rear).device_id == devices.async_get_device({(DOMAIN, "k9-0001")}).id


async def test_video_adresse_mit_token(hass: HomeAssistant, aioclient_mock, entry, token):
    await setup(hass, aioclient_mock, entry)
    stream_token = secrets.token_urlsafe(8)
    aioclient_mock.get(f"{URL}/cameras/50/stream",
                       json={"url": f"/video/k9-0001/cam1/index.m3u8?token={stream_token}", "expires_in": 600})
    _, entity = camera_entity(hass, entry, 50)
    assert await entity.stream_source() == f"{URL}/video/k9-0001/cam1/index.m3u8?token={stream_token}"
    call = aioclient_mock.mock_calls[-1]
    assert str(call[1]).endswith("/cameras/50/stream") and call[3]["Authorization"] == f"Bearer {token}"


async def test_kamera_noch_nicht_eingerichtet(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry)
    aioclient_mock.get(f"{URL}/cameras/51/stream", status=409, json={"detail": "noch nicht eingerichtet"})
    _, entity = camera_entity(hass, entry, 51)
    assert await entity.stream_source() is None


async def test_kein_standbild_ohne_zuschauer(hass: HomeAssistant, aioclient_mock, entry):
    """Vorschaubilder dürfen das Live-Bild nicht starten (LTE-Datenvolumen)."""
    await setup(hass, aioclient_mock, entry)
    entity_id, _ = camera_entity(hass, entry, 50)
    calls_before = len(aioclient_mock.mock_calls)
    with pytest.raises(HomeAssistantError):
        await async_get_image(hass, entity_id)
    assert len(aioclient_mock.mock_calls) == calls_before  # keine Video-Adresse geholt


class FakeStream:
    def __init__(self, watching: bool, available: bool = True):
        self._outputs = {"hls": object()} if watching else {}
        self.available = available

    def outputs(self):
        return self._outputs


@pytest.mark.parametrize("age, watching, available, expected", [
    (60, False, True, False),  # Adresse noch frisch
    (9 * 60, False, True, True),  # niemand schaut zu → für den nächsten Start erneuern
    (9 * 60, True, True, False),  # läuft gerade → nicht unterbrechen
    (9 * 60, True, False, True),  # abgerissen → mit neuer Adresse neu verbinden
])
def test_wann_neue_adresse(age, watching, available, expected):
    stream = FakeStream(watching, available)
    assert camera_module.needs_new_source(stream, time.monotonic() - age) is expected


async def test_zwei_boxen_mit_kamera_ohne_via_device(hass: HomeAssistant, aioclient_mock, entry, caplog):
    """Rückmeldung aus dem Test: In neueren Home-Assistant-Versionen schlug die zweite Kamera wegen
    `via_device` fehl. Die Boxen hängen jetzt per `via_device_id` am Anhänger."""
    from .conftest import trailer_detail

    detail = trailer_detail(
        boxes=[{"id": 10, "name": "Box 1", "position": 1}, {"id": 11, "name": "Box 2", "position": 2}],
        cameras=[{"id": 50, "name": "Kamera", "box_id": 10, "stream_path": "k9-0001/cam1"},
                 {"id": 52, "name": "Kamera", "box_id": 11, "stream_path": "k9-0001/cam2"}],
    )
    await setup(hass, aioclient_mock, entry, detail)
    assert sorted(s.entity_id for s in hass.states.async_all("camera")) == [
        "camera.unser_anhanger_box_1_kamera", "camera.unser_anhanger_box_2_kamera"]
    devices = dr.async_get(hass)
    trailer = devices.async_get_device({(DOMAIN, "k9-0001")})
    for box_id in (10, 11):
        assert devices.async_get_device({(DOMAIN, f"k9-0001-box-{box_id}")}).via_device_id == trailer.id
    assert "via_device" not in caplog.text
