"""Support for Solcast PV forecast sensors."""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from typing import Dict

from datetime import datetime as dt
from datetime import timedelta, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_CONFIGURATION_URL,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_ENTRY_TYPE, ATTRIBUTION
from .coordinator import SolcastUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


SENSORS: dict[str, SensorEntityDescription] = {
    "total_kwh_forecast_today": SensorEntityDescription(
        key="total_kwh_forecast_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast Today",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "peak_w_today": SensorEntityDescription(
        key="peak_w_today",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        name="Peak Forecast Today",
        icon="mdi:solar-power",
        suggested_display_precision=0,
    ),
    "peak_w_time_today": SensorEntityDescription(
        key="peak_w_time_today",
        name="Peak Time Today",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        suggested_display_precision=0,
    ),
    "forecast_this_hour": SensorEntityDescription(
        key="forecast_this_hour",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        name="Forecast This Hour",
        icon="mdi:solar-power",
        suggested_display_precision=0,
    ),
    "forecast_remaining_today": SensorEntityDescription(
        key="get_remaining_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast Remaining Today",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "forecast_next_hour": SensorEntityDescription(
        key="forecast_next_hour",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        name="Forecast Next Hour",
        icon="mdi:solar-power",
        suggested_display_precision=0,
    ),
    # "forecast_next_12hour": SensorEntityDescription(
    #     key="forecast_next_12hour",
    #     device_class=SensorDeviceClass.ENERGY,
    #     native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
    #     name="Energy Next 12 Hours",
    #     suggested_display_precision=0,
    # ),
    # "forecast_next_24hour": SensorEntityDescription(
    #     key="forecast_next_24hour",
    #     device_class=SensorDeviceClass.ENERGY,
    #     native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
    #     name="Energy Next 24 Hours",
    #     suggested_display_precision=0,
    # ),
    "total_kwh_forecast_tomorrow": SensorEntityDescription(
        key="total_kwh_forecast_tomorrow",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast Tomorrow",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "peak_w_tomorrow": SensorEntityDescription(
        key="peak_w_tomorrow",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        name="Peak Forecast Tomorrow",
        icon="mdi:solar-power",
        suggested_display_precision=0,
    ),
    "peak_w_time_tomorrow": SensorEntityDescription(
        key="peak_w_time_tomorrow",
        name="Peak Time Tomorrow",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        suggested_display_precision=0,
    ),
    "api_counter": SensorEntityDescription(
        key="api_counter",
        name="API Used",
        icon="mdi:web-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "api_limit": SensorEntityDescription(
        key="api_limit",
        name="API Limit",
        icon="mdi:web-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "lastupdated": SensorEntityDescription(
        key="lastupdated",
        device_class=SensorDeviceClass.TIMESTAMP,
        name="API Last Polled",
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "total_kwh_forecast_d3": SensorEntityDescription(
        key="total_kwh_forecast_d3",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast D3",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "total_kwh_forecast_d4": SensorEntityDescription(
        key="total_kwh_forecast_d4",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast D4",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "total_kwh_forecast_d5": SensorEntityDescription(
        key="total_kwh_forecast_d5",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast D5",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "total_kwh_forecast_d6": SensorEntityDescription(
        key="total_kwh_forecast_d6",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast D6",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    "total_kwh_forecast_d7": SensorEntityDescription(
        key="total_kwh_forecast_d7",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        name="Forecast D7",
        icon="mdi:solar-power",
        suggested_display_precision=2,
    ),
    # "power_now": SensorEntityDescription(
    #     key="power_now",
    #     device_class=SensorDeviceClass.POWER,
    #     native_unit_of_measurement=UnitOfPower.WATT,
    #     name="Power Now",
    #     suggested_display_precision=0,
    # ),
    # "power_now_30m": SensorEntityDescription(
    #     key="power_now_30m",
    #     device_class=SensorDeviceClass.POWER,
    #     native_unit_of_measurement=UnitOfPower.WATT,
    #     name="Power Next 30 Mins",
    #     suggested_display_precision=0,
    # ),
    # "power_now_1hr": SensorEntityDescription(
    #     key="power_now_1hr",
    #     device_class=SensorDeviceClass.POWER,
    #     native_unit_of_measurement=UnitOfPower.WATT,
    #     name="Power Next Hour",
    #     suggested_display_precision=0,
    # ),
    # "power_now_12hr": SensorEntityDescription(
    #     key="power_now_12hr",
    #     device_class=SensorDeviceClass.POWER,
    #     native_unit_of_measurement=UnitOfPower.WATT,
    #     name="Power Next 12 Hours",
    #     suggested_display_precision=0,
    # ),
    # "power_now_24hr": SensorEntityDescription(
    #     key="power_now_24hr",
    #     device_class=SensorDeviceClass.POWER,
    #     native_unit_of_measurement=UnitOfPower.WATT,
    #     name="Power Next 24 Hours",
    #     suggested_display_precision=0,
    # ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Solcast sensor."""

    coordinator: SolcastUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for sensor_types in SENSORS:
        sen = SolcastSensor(coordinator, SENSORS[sensor_types], entry)
        entities.append(sen)

    for site in coordinator.solcast._sites:
        k = RooftopSensorEntityDescription(
                key=site["resource_id"],
                name=site["name"],
                icon="mdi:home",
                device_class=SensorDeviceClass.ENERGY,
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                entity_category=EntityCategory.CONFIG,
                suggested_display_precision=2,
                rooftop_id=site["resource_id"],
            )
        
        #sen = RooftopSensor(coordinator, k,entry, coordinator._version)
        sen = RooftopSensor(
            key="site_data",
            coordinator=coordinator,
            entity_description=k,
            entry=entry,
        )
        
        entities.append(sen)
    
    async_add_entities(entities)

class SolcastSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Solcast Sensor device."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: SolcastUpdateCoordinator,
        entity_description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = entity_description
        self.coordinator = coordinator

        self._attributes = {}
        self._attr_extra_state_attributes = {}

        try:
            self._sensor_data = coordinator.get_sensor_value(entity_description.key)
        except Exception as ex:
            _LOGGER.error(
                f"SOLCAST - unable to get sensor value {ex} %s", traceback.format_exc()
            )
            self._sensor_data = None
        
        self._attr_device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
            ATTR_NAME: "Solcast PV Forecast", #entry.title,
            ATTR_MANUFACTURER: "Oziee",
            ATTR_MODEL: "Solcast PV Forecast",
            ATTR_ENTRY_TYPE: DeviceEntryType.SERVICE,
            ATTR_SW_VERSION: coordinator._version,
            ATTR_CONFIGURATION_URL: "https://toolkit.solcast.com.au/live-forecast",
        }

        self._unique_id = f"solcast_api_{entity_description.name}"

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self.entity_description.name}"

    @property
    def friendly_name(self):
        """Return the name of the device."""
        return self.entity_description.name

    @property
    def unique_id(self):
        """Return the unique ID of the binary sensor."""
        return f"solcast_{self._unique_id}"

    @property
    def extra_state_attributes(self):
        """Return the state extra attributes of the sensor."""
        try:
            return self.coordinator.get_sensor_extra_attributes(
                self.entity_description.key
            )
        except Exception as ex:
            _LOGGER.error(
                f"SOLCAST - unable to get sensor value {ex} %s", traceback.format_exc()
            )
            return None

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return self._sensor_data

    @property
    def should_poll(self) -> bool:
        """Return if the sensor should poll."""
        return False

    # async def async_added_to_hass(self) -> None:
    #     """When entity is added to hass."""
    #     await super().async_added_to_hass()
    #     self.async_on_remove(
    #         self.coordinator.async_add_listener(self._handle_coordinator_update)
    #     )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        try:
            self._sensor_data = self.coordinator.get_sensor_value(
                self.entity_description.key
            )
        except Exception as ex:
            _LOGGER.error(
                f"SOLCAST - unable to get sensor value {ex} %s", traceback.format_exc()
            )
            self._sensor_data = None
        self.async_write_ha_state()

@dataclass
class RooftopSensorEntityDescription(SensorEntityDescription):
    rooftop_id: str | None = None
    
class RooftopSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Seplos Sensor device."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        *,
        key: str,
        coordinator: SolcastUpdateCoordinator,
        entity_description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.key = key
        self.coordinator = coordinator
        self.entity_description = entity_description
        self.rooftop_id = entity_description.rooftop_id

        self._attributes = {}
        self._attr_extra_state_attributes = {}

        try:
            self._sensor_data = coordinator.get_site_sensor_value(self.rooftop_id, key)
        except Exception as ex:
            _LOGGER.error(
                f"SOLCAST - unable to get sensor value {ex} %s", traceback.format_exc()
            )
            self._sensor_data = None
        
        self._attr_device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
            ATTR_NAME: "Solcast PV Forecast", #entry.title,
            ATTR_MANUFACTURER: "Oziee",
            ATTR_MODEL: "Solcast PV Forecast",
            ATTR_ENTRY_TYPE: DeviceEntryType.SERVICE,
            ATTR_SW_VERSION: coordinator._version,
            ATTR_CONFIGURATION_URL: "https://toolkit.solcast.com.au/live-forecast",
        }

        self._unique_id = f"solcast_api_{entity_description.name}"

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self.entity_description.name}"

    @property
    def friendly_name(self):
        """Return the name of the device."""
        return self.entity_description.name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return f"solcast_{self._unique_id}"

    @property
    def extra_state_attributes(self):
        """Return the state extra attributes of the sensor."""
        try:
            return self.coordinator.get_site_sensor_extra_attributes(
                self.rooftop_id, 
                self.key,
            )
        except Exception as ex:
            _LOGGER.error(
                f"SOLCAST - unable to get sensor value {ex} %s", traceback.format_exc()
            )
            return None

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return self._sensor_data

    @property
    def should_poll(self) -> bool:
        """Return if the sensor should poll."""
        return False

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        try:
            self._sensor_data = self.coordinator.get_site_sensor_value(
                self.rooftop_id, 
                self.key,
            )
        except Exception as ex:
            _LOGGER.error(
                f"SOLCAST - unable to get sensor value {ex} %s", traceback.format_exc()
            )
            self._sensor_data = None
        self.async_write_ha_state()
        