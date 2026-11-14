"""Async client for the undocumented AIRSTAGE cloud API."""

from __future__ import annotations

import logging
import secrets
import uuid
from typing import Any

from aiohttp import ClientResponseError, ClientSession

_LOGGER = logging.getLogger(__name__)
_APP_ID = "com.fujitsu_general.ACL_O_App"
_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
)


class AirstageApi:
    def __init__(self, session: ClientSession, base_url: str, email: str, password: str,
                 country: str, language: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._password = password
        self._country = country
        self._language = language
        self._auth: dict[str, Any] | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
            "X-Requested-With": _APP_ID,
            "Origin": "file://",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {self._auth.get('accessToken', 'undefined') if self._auth else 'undefined'}",
        }

    async def login(self) -> None:
        payload = {"user": {
            "email": self._email,
            "password": self._password,
            "country": self._country,
            "language": self._language,
            # The cloud expects the same token shape the mobile app generates.
            "deviceToken": f"{secrets.token_hex(11)}:{secrets.token_hex(70)}",
            "ssid": str(uuid.uuid4()),
            "osVersion": "iOS 17.4.1",
        }}
        async with self._session.post(f"{self._base_url}/users/sign_in", json=payload,
                                      headers=self._headers()) as response:
            if response.status in (401, 403):
                raise InvalidAuth from None
            response.raise_for_status()
            self._auth = await response.json()

    async def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> Any:
        if self._auth is None:
            await self.login()
        async with self._session.request(method, f"{self._base_url}{path}", json=json,
                                        headers=self._headers()) as response:
            if response.status in (401, 403):
                await self._refresh_or_login()
                async with self._session.request(method, f"{self._base_url}{path}", json=json,
                                                headers=self._headers()) as retry:
                    retry.raise_for_status()
                    return await retry.json()
            response.raise_for_status()
            return await response.json()

    async def _refresh_or_login(self) -> None:
        refresh = (self._auth or {}).get("refreshToken")
        if refresh:
            async with self._session.post(
                f"{self._base_url}/users/me/refresh_token",
                json={"user": {"refreshToken": refresh}}, headers=self._headers(),
            ) as response:
                if response.ok:
                    self._auth = await response.json()
                    return
        self._auth = None
        await self.login()

    async def devices(self) -> list[dict[str, Any]]:
        result = await self._request("GET", "/devices/all?limit=100")
        return result.get("devices", [])

    async def device(self, device_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/devices/{device_id}")

    async def set_parameters(self, device_id: str, parameters: list[dict[str, str]]) -> None:
        await self._request("POST", f"/devices/{device_id}/set_parameters_request",
                            json={"deviceSubId": 0, "parameters": parameters})


class InvalidAuth(Exception):
    """Invalid AIRSTAGE account credentials."""


def parameter_map(device: dict[str, Any]) -> dict[str, str]:
    return {item["name"]: item["value"] for item in device.get("parameters", [])
            if "name" in item and "value" in item}


def temperature_celsius(raw: str | None) -> float | None:
    if raw is None:
        return None
    # AIRSTAGE room and outdoor temperatures use a 5000 offset and 0.01 C steps.
    value = float(raw)
    if value == 65535:
        return None
    return round((value - 5000) / 100, 2)


def target_celsius(raw: str | None) -> float | None:
    if raw is None or float(raw) == 65535:
        return None
    return float(raw) / 10
