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


class K9NotReady(K9Error):
    """Kamera ist am Server noch nicht fertig eingerichtet (z. B. Pfad am NVR fehlt)."""


class K9Api:
    def __init__(self, session: aiohttp.ClientSession, url: str, token: str | None = None) -> None:
        self._session = session
        self._url = url.rstrip("/")
        self._token = token

    async def _request(self, method: str, path: str, raw: bool = False, **kwargs: Any) -> Any:
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
                if response.status == 409:
                    raise K9NotReady(f"HTTP 409 bei {path}")
                if response.status >= 400:
                    raise K9Error(f"HTTP {response.status} bei {path}")
                return await response.read() if raw else await response.json()
        except (aiohttp.ClientError, TimeoutError) as error:
            raise K9Error(f"Server nicht erreichbar: {error}") from error

    async def pair(self, code: str, name: str) -> dict[str, Any]:
        """Code aus der App gegen einen dauerhaften Zugang tauschen: {"token", "email", "name"}."""
        return await self._request("POST", "/integrations/pair", json={"code": code, "name": name})

    async def trailers(self) -> list[dict[str, Any]]:
        """Alle Anhänger mit Boxen, Kameras und Sensoren (inkl. letztem Messwert)."""
        summaries = await self._request("GET", "/trailers")
        return [await self._request("GET", f"/trailers/{summary['id']}") for summary in summaries]


    async def stream_url(self, camera_id: int) -> str:
        """Adresse des Live-Bilds (HLS) mit kurzlebigem Token – innerhalb weniger Minuten öffnen."""
        data = await self._request("GET", f"/cameras/{camera_id}/stream")
        url = data["url"]
        return url if url.startswith("http") else f"{self._url}{url}"  # der Server liefert sie relativ

    async def snapshot(self, camera_id: int) -> bytes | None:
        """Standbild (JPEG) vom Server – höchstens alle 30–90 s ein neues, das stellt der Eigentümer in der App ein.
        None, wenn es gerade keins gibt (Anhänger offline ohne früheres Bild, Kamera nicht eingerichtet)."""
        try:
            return await self._request("GET", f"/cameras/{camera_id}/snapshot", raw=True)
        except K9NotReady:
            return None
        except K9Error as error:
            if "HTTP 503" in str(error):
                return None
            raise
