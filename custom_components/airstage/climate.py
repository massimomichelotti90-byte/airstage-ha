"""Climate entities for AIRSTAGE Cloud devices."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import InvalidAuth, parameter_map, target_celsius, temperature_celsius
from .const import DOMAIN, HA_MODES, OP_MODES
from .coordinator import AirstageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AIRSTAGE climate entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        AirstageClimate(coordinator, device)
        for device in coordinator.data.values()
    ])


class AirstageClimate(CoordinatorEntity[AirstageCoordinator], ClimateEntity):
    """Climate entity for one AIRSTAGE indoor unit."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [
        HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL, HVACMode.DRY,
        HVACMode.FAN_ONLY, HVACMode.HEAT,
    ]

    def __init__(self, coordinator: AirstageCoordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._device_id = str(device["deviceId"])
        self._api = coordinator.api
        self._attr_name = device.get("deviceName", "Fujitsu AIRSTAGE")
        self._attr_unique_id = self._device_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "manufacturer": "Fujitsu",
            "model": device.get("model"),
            "name": self._attr_name,
        }

    @property
    def _params(self) -> dict[str, str]:
        return parameter_map(self.coordinator.data.get(self._device_id, {}))

    @property
    def hvac_mode(self) -> HVACMode:
        if self._params.get("iu_onoff") == "0":
            return HVACMode.OFF
        mode = OP_MODES.get(self._params.get("iu_op_mode", ""))
        return HVACMode(mode) if mode else HVACMode.AUTO

    @property
    def current_temperature(self) -> float | None:
        return temperature_celsius(self._params.get("iu_indoor_tmp"))

    @property
    def target_temperature(self) -> float | None:
        return target_celsius(self._params.get("iu_set_tmp"))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._set({"iu_onoff": "0"})
            return
        code = HA_MODES.get(hvac_mode.value)
        if code is None:
            raise HomeAssistantError(f"Unsupported AIRSTAGE mode: {hvac_mode}")
        await self._set({"iu_op_mode": code, "iu_onoff": "1"})

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if ATTR_TEMPERATURE in kwargs:
            raw = str(round(float(kwargs[ATTR_TEMPERATURE]) * 10))
            await self._set({"iu_set_tmp": raw})

    async def _set(self, values: dict[str, str]) -> None:
        try:
            await self._api.set_parameters(self._device_id, [
                {"name": name, "desiredValue": value}
                for name, value in values.items()
            ])
            await self.coordinator.async_request_refresh()
        except InvalidAuth as err:
            raise HomeAssistantError(
                "AIRSTAGE account credentials are invalid. Reauthenticate the integration."
            ) from err
        except (ClientError, TimeoutError, ValueError) as err:
            raise HomeAssistantError("Could not send command to AIRSTAGE Cloud") from err
