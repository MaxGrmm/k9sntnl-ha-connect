"""Tests: Einrichten mit Kopplungs-Code und neu verbinden."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.k9sntnl.const import CONF_CODE, CONF_TOKEN, CONF_URL, DOMAIN

from .conftest import EMAIL, URL, trailer_detail


def mock_server(aioclient_mock, token, pair_status=200, email=EMAIL):
    aioclient_mock.post(f"{URL}/integrations/pair", status=pair_status,
                        json={"token": token, "email": email, "name": "Max"} if pair_status == 200 else {"detail": "x"})
    aioclient_mock.get(f"{URL}/trailers", json=[{"id": 1}])
    aioclient_mock.get(f"{URL}/trailers/1", json=trailer_detail())


async def start(hass: HomeAssistant, code="k7qp-4mzx"):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CODE: code, CONF_URL: URL + "/"})


async def test_einrichten(hass: HomeAssistant, aioclient_mock, token):
    mock_server(aioclient_mock, token)
    result = await start(hass)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_URL: URL, CONF_TOKEN: token}
    assert result["result"].unique_id == EMAIL
    pair_call = next(call for call in aioclient_mock.mock_calls if str(call[1]).endswith("/integrations/pair"))
    assert pair_call[2]["code"] == "k7qp-4mzx" and pair_call[2]["name"].startswith("Home Assistant")


async def test_falscher_code(hass: HomeAssistant, aioclient_mock, token):
    mock_server(aioclient_mock, token, pair_status=400)
    result = await start(hass)
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "invalid_code"}


async def test_zu_viele_versuche(hass: HomeAssistant, aioclient_mock, token):
    mock_server(aioclient_mock, token, pair_status=429)
    result = await start(hass)
    assert result["errors"] == {"base": "too_many_attempts"}


async def test_server_nicht_erreichbar(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(f"{URL}/integrations/pair", exc=TimeoutError())
    result = await start(hass)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_konto_schon_verbunden(hass: HomeAssistant, aioclient_mock, entry, token):
    entry.add_to_hass(hass)
    mock_server(aioclient_mock, token)
    result = await start(hass)
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"


async def test_neu_verbinden(hass: HomeAssistant, aioclient_mock, entry, token):
    entry.add_to_hass(hass)
    new_token = token + "neu"
    mock_server(aioclient_mock, new_token)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CODE: "ABCD-EFGH"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reauth_successful"
    assert entry.data[CONF_TOKEN] == new_token


async def test_neu_verbinden_anderes_konto(hass: HomeAssistant, aioclient_mock, entry, token):
    entry.add_to_hass(hass)
    mock_server(aioclient_mock, token, email="jemand@example.com")
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CODE: "ABCD-EFGH"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "wrong_account"
