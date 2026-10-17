"""Sensors provided by the Gruenbeck softliQ integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    CONF_HOST,
    EntityCategory,
    PERCENTAGE,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class GruenbeckSensorDescription(SensorEntityDescription):
    """Describe a device value sensor."""

    value_key: str


class GruenbeckCoordinatorEntity(CoordinatorEntity[GruenbeckDataUpdateCoordinator]):
    """Keep coordinator entities available while cached data is still fresh."""

    @property
    def available(self) -> bool:
        """Stay available until cached values exceed their maximum age."""
        return self.coordinator.has_fresh_data


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
    entities = [
        GruenbeckSensor(coordinator, entry, description) for description in SENSORS
    ]
    entities.append(GruenbeckLastSuccessfulUpdateSensor(coordinator, entry))
    async_add_entities(entities)


class GruenbeckSensor(GruenbeckCoordinatorEntity, SensorEntity):
    """Represent one softliQ value as a Home Assistant sensor."""

    entity_description: GruenbeckSensorDescription

    def __init__(
        self,
        coordinator: GruenbeckDataUpdateCoordinator,
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


class GruenbeckLastSuccessfulUpdateSensor(GruenbeckCoordinatorEntity, SensorEntity):
    """Expose the last successful device request as a diagnostic timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-check-outline"
    _attr_name = "Letzter erfolgreicher Datenabruf"

    def __init__(
        self, coordinator: GruenbeckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_successful_update"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Gruenbeck softliQ",
            "manufacturer": "Grünbeck",
            "model": "softliQ",
            "configuration_url": f"http://{entry.options.get(CONF_HOST, entry.data[CONF_HOST])}",
        }

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the most recent successful poll."""
        return self.coordinator.last_successful_update