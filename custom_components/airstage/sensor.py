"""Temperature sensors for AIRSTAGE Cloud devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import parameter_map, temperature_celsius
from .const import DOMAIN
from .coordinator import AirstageCoordinator

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="indoor_temperature",
        translation_key="indoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outdoor_temperature",
        translation_key="outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

PARAMETERS = {
    "indoor_temperature": "iu_indoor_tmp",
    "outdoor_temperature": "iu_outdoor_tmp",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AIRSTAGE temperature sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        AirstageTemperatureSensor(coordinator, device, description)
        for device in coordinator.data.values()
        for description in SENSORS
    ])


class AirstageTemperatureSensor(CoordinatorEntity[AirstageCoordinator], SensorEntity):
    """Expose one AIRSTAGE temperature parameter as a sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AirstageCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = str(device["deviceId"])
        self._attr_unique_id = f"{self._device_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "manufacturer": "Fujitsu",
            "model": device.get("model"),
            "name": device.get("deviceName", "Fujitsu AIRSTAGE"),
        }

    @property
    def native_value(self) -> float | None:
        params = parameter_map(self.coordinator.data.get(self._device_id, {}))
        raw = params.get(PARAMETERS[self.entity_description.key])
        return temperature_celsius(raw)
