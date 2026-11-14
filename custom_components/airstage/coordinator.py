"""Shared cloud polling for AIRSTAGE devices."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AirstageApi
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AirstageCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch all devices and parameters on one shared interval."""

    def __init__(self, hass: HomeAssistant, api: AirstageApi) -> None:
        self.api = api
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.devices()
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Unable to retrieve AIRSTAGE devices: {err}") from err
        return {
            str(device["deviceId"]): device
            for device in devices
            if "deviceId" in device
        }
