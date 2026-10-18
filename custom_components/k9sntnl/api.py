"""Verbindung zum K9SNTNL-Server (Backend: MaxGrmm/k9sntnl-backend).

Der Zugang („k9ha_…“) entsteht beim Koppeln mit einem Code aus der App und gilt nur zum Lesen.
"""

from __future__ import annotations

from typing import Any

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=20)


class K9Error(Exception):
    """Server nicht erreichbar oder unerwartete Antwort."""


class K9AuthError(K9Error):
    """Zugang ungültig – z. B. in der App getrennt oder „Überall abmelden“."""


class K9PairingError(K9Error):
    """Kopplungs-Code falsch oder abgelaufen."""


class K9RateLimitError(K9PairingError):
    """Zu viele falsche Codes – der Server sperrt diese Adresse für 15 Minuten."""


class K9Api:
    def __init__(self, session: aiohttp.ClientSession, url: str, token: str | None = None) -> None:
        self._session = session
        self._url = url.rstrip("/")
        self._token = token

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        try:
            async with self._session.request(
                method, f"{self._url}{path}", headers=headers, timeout=TIMEOUT, **kwargs
            ) as response:
                if response.status == 401:
                    raise K9AuthError("Zugang ungültig")
                if response.status == 429:
                    raise K9RateLimitError("Zu viele Fehlversuche")
                if response.status == 400 and path == "/integrations/pair":
                    raise K9PairingError("Code ungültig oder abgelaufen")
                if response.status >= 400:
                    raise K9Error(f"HTTP {response.status} bei {path}")
                return await response.json()
        except (aiohttp.ClientError, TimeoutError) as error:
            raise K9Error(f"Server nicht erreichbar: {error}") from error

    async def pair(self, code: str, name: str) -> dict[str, Any]:
        """Code aus der App gegen einen dauerhaften Zugang tauschen: {"token", "email", "name"}."""
        return await self._request("POST", "/integrations/pair", json={"code": code, "name": name})

    async def trailers(self) -> list[dict[str, Any]]:
        """Alle Anhänger mit Boxen, Kameras und Sensoren (inkl. letztem Messwert)."""
        summaries = await self._request("GET", "/trailers")
        return [await self._request("GET", f"/trailers/{summary['id']}") for summary in summaries]

