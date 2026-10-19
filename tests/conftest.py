"""Gemeinsame Test-Vorbereitung: Home Assistant im Testmodus (pytest-homeassistant-custom-component)."""

import secrets

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.k9sntnl.const import CONF_TOKEN, CONF_URL, DOMAIN

URL = "https://k9.example.invalid"
EMAIL = "max@example.com"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def token() -> str:
    # Zufällig – keine Schlüssel als Text im Code
    return "k9ha_" + secrets.token_urlsafe(16)


@pytest.fixture
def entry(token) -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, unique_id=EMAIL, title=f"K9SNTNL ({EMAIL})",
                           data={CONF_URL: URL, CONF_TOKEN: token})


def trailer_detail(**changes) -> dict:
    """Antwort wie GET /trailers/{id} im Backend."""
    data = {
        "id": 1, "identifier": "k9-0001", "name": "Unser Anhänger", "license_plate": None, "my_access": "owner",
        "status": "online", "tunnel_status": "offline", "last_seen": "2026-10-18T20:00:00Z",
        "tunnel_checked_at": None, "air_conditioner_count": 0, "license": "standard",
        "boxes": [{"id": 10, "name": "Box 1", "position": 1}],
        "cameras": [],
        "sensors": [
            {"id": 100, "name": "Box 1 Temperatur", "box_id": 10, "kind": "temperature", "unit": "°C", "key": "t1",
             "last_value": 21.5, "last_time": "2026-10-18T20:00:00Z", "min_value": 5.0, "max_value": 28.0,
             "alert": "ok"},
            {"id": 101, "name": "Batterie", "box_id": None, "kind": "voltage", "unit": "V", "key": "bat",
             "last_value": 12.6, "last_time": "2026-10-18T20:00:00Z", "min_value": None, "max_value": None,
             "alert": "ok"},
        ],
        "air_conditioners": [],
    }
    data.update(changes)
    return data
