"""Tests: Anhänger und Boxen als Geräte, Messwerte als Sensoren, Online-Status, Zugang ungültig."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.k9sntnl.const import DOMAIN

from .conftest import URL, trailer_detail


async def setup(hass, aioclient_mock, entry, detail=None):
    aioclient_mock.get(f"{URL}/trailers", json=[{"id": 1}])
    aioclient_mock.get(f"{URL}/trailers/1", json=detail or trailer_detail())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def entity_id(hass, unique_id: str, platform: str = "sensor") -> str:
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)


async def test_sensoren_und_geraete(hass: HomeAssistant, aioclient_mock, entry, token):
    await setup(hass, aioclient_mock, entry)
    assert all(call[3]["Authorization"] == f"Bearer {token}" for call in aioclient_mock.mock_calls)

    temperature = hass.states.get(entity_id(hass, f"{entry.unique_id}_sensor_100"))
    assert temperature.state == "21.5"
    assert temperature.attributes["friendly_name"] == "Unser Anhänger Box 1 Temperatur"  # ohne doppeltes „Box 1“
    assert temperature.attributes["unit_of_measurement"] == "°C"
    assert temperature.attributes["device_class"] == "temperature"
    assert temperature.attributes["alert"] == "ok" and temperature.attributes["max_value"] == 28.0
    battery = hass.states.get(entity_id(hass, f"{entry.unique_id}_sensor_101"))
    assert battery.state == "12.6" and battery.attributes["device_class"] == "voltage"

    devices = dr.async_get(hass)
    trailer = devices.async_get_device({(DOMAIN, "k9-0001")})
    box = devices.async_get_device({(DOMAIN, "k9-0001-box-10")})
    assert trailer.name == "Unser Anhänger" and box.name == "Unser Anhänger Box 1" and box.via_device_id == trailer.id
    registry = er.async_get(hass)
    assert registry.async_get(entity_id(hass, f"{entry.unique_id}_sensor_100")).device_id == box.id
    assert registry.async_get(entity_id(hass, f"{entry.unique_id}_sensor_101")).device_id == trailer.id


async def test_online_status(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry)
    sensors = hass.states.get(entity_id(hass, f"{entry.unique_id}_sensors_online_1", "binary_sensor"))
    tunnel = hass.states.get(entity_id(hass, f"{entry.unique_id}_trailer_online_1", "binary_sensor"))
    assert sensors.state == "on" and tunnel.state == "off"
    assert sensors.attributes["device_class"] == "connectivity"


async def test_ohne_tunnel_keine_entitaet(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry, trailer_detail(tunnel_status="disabled", status="unknown"))
    assert entity_id(hass, f"{entry.unique_id}_trailer_online_1", "binary_sensor") is None
    sensors = hass.states.get(entity_id(hass, f"{entry.unique_id}_sensors_online_1", "binary_sensor"))
    assert sensors.state == "unknown"


async def test_aktualisierung_und_neuer_sensor(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry)
    detail = trailer_detail()
    detail["sensors"][0]["last_value"] = 30.1
    detail["sensors"].append({"id": 102, "name": "Box 1 Feuchte", "box_id": 10, "kind": "humidity", "unit": "%",
                              "key": "h1", "last_value": 55.0, "last_time": None, "min_value": None,
                              "max_value": None, "alert": "ok"})
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{URL}/trailers", json=[{"id": 1}])
    aioclient_mock.get(f"{URL}/trailers/1", json=detail)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, f"{entry.unique_id}_sensor_100")).state == "30.1"
    assert hass.states.get(entity_id(hass, f"{entry.unique_id}_sensor_102")).state == "55.0"


async def test_server_weg_dann_nicht_verfuegbar(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry)
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{URL}/trailers", status=502)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, f"{entry.unique_id}_sensor_100")).state == "unavailable"


async def test_zugang_ungueltig_startet_neu_verbinden(hass: HomeAssistant, aioclient_mock, entry):
    aioclient_mock.get(f"{URL}/trailers", status=401)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == ["reauth"]


async def test_entfernen(hass: HomeAssistant, aioclient_mock, entry):
    await setup(hass, aioclient_mock, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
