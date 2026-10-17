"""Sensors provided by the Gruenbeck softliQ integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import CONF_HOST, PERCENTAGE, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class GruenbeckSensorDescription(SensorEntityDescription):
    """Describe a device value sensor."""

    value_key: str


SENSORS = (
    GruenbeckSensorDescription(
        key="flow_rate",
        value_key="D_A_1_1",
        name="Aktueller Durchfluss",
        native_unit_of_measurement="m³/h",
        icon="mdi:water-pump",
    ),
    GruenbeckSensorDescription(
        key="remaining_capacity",
        value_key="D_A_1_2",
        name="Restkapazität",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        icon="mdi:water-outline",
    ),
    GruenbeckSensorDescription(
        key="maintenance_remaining",
        value_key="D_A_2_2",
        name="Restdauer Wartungsintervall",
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:wrench-clock",
    ),
    GruenbeckSensorDescription(
        key="hours_since_regeneration",
        value_key="D_A_3_1",
        name="Zeit seit letzter Regeneration",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer-outline",
    ),
    GruenbeckSensorDescription(
        key="regeneration_progress",
        value_key="D_A_3_2",
        name="Fortschritt Regeneration",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:progress-clock",
    ),
    GruenbeckSensorDescription(
        key="daily_water_consumption",
        value_key="D_Y_1",
        name="Wasserverbrauch pro Tag",
        native_unit_of_measurement="L/Tag",
        icon="mdi:water",
    ),
    GruenbeckSensorDescription(
        key="plant_capacity",
        value_key="D_A_1_3",
        name="Anlagenkapazität",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        icon="mdi:water-plus-outline",
    ),
    GruenbeckSensorDescription(
        key="salt_range",
        value_key="D_A_2_3",
        name="Salzreichweite",
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:shaker-outline",
    ),
    GruenbeckSensorDescription(
        key="regeneration_step",
        value_key="D_Y_5",
        name="Aktueller Regenerationsschritt",
        icon="mdi:stairs",
    ),
    GruenbeckSensorDescription(
        key="regeneration_step_remaining",
        value_key="D_A_2_1",
        name="Restdauer oder Restmenge Regenerationsschritt",
        icon="mdi:timer-sand",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up softliQ sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        GruenbeckSensor(coordinator, entry, description) for description in SENSORS
    )


class GruenbeckSensor(CoordinatorEntity[DataUpdateCoordinator[dict[str, Any]]], SensorEntity):
    """Represent one softliQ value as a Home Assistant sensor."""

    entity_description: GruenbeckSensorDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, Any]],
        entry: ConfigEntry,
        description: GruenbeckSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Gruenbeck softliQ",
            "manufacturer": "Grünbeck",
            "model": "softliQ",
            "configuration_url": f"http://{entry.options.get(CONF_HOST, entry.data[CONF_HOST])}",
        }

    @property
    def native_value(self) -> int | float | None:
        """Return the latest value, or None if the device did not provide it."""
        return self.coordinator.data.get(self.entity_description.value_key)