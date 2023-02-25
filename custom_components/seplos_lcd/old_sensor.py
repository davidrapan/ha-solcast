"""Support for Seplos LCD Connection sensors."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ATTR_IDENTIFIERS, ATTR_MANUFACTURER,
                                 ATTR_MODEL, ATTR_NAME,ELECTRIC_POTENTIAL_MILLIVOLT,ELECTRIC_POTENTIAL_VOLT,
                                 TEMP_CELSIUS)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .const import ATTR_ENTRY_TYPE
from .coordinator import SeplosUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# {

#  
#  'system_status': 2, 'switch_status': 3, 
#  
#  'reserved_1': 1, 'reserved_2': 1, 


SENSORS: dict[str, SensorEntityDescription] = {
    "min_cell": SensorEntityDescription(
        key="min_cell",
        name="Lowest Cell",
        icon="mdi:battery-low",
    ),
    "max_cell": SensorEntityDescription(
        key="max_cell",
        name="Highest Cell",
        icon="mdi:battery-high",
    ),
    "cell_deviation": SensorEntityDescription(
        key="cell_deviation",
        name="Cell Deviation",
        icon="mdi:battery-alert-variant-outline",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_MILLIVOLT
    ),
    "total_volts": SensorEntityDescription(
        key="total_volts",
        name="Total Pack Voltage",
        icon="mdi:battery-charging-100",
    ),
    "battery_capacity": SensorEntityDescription(
        key="battery_capacity",
        name="Battery Pack Capacity",
        icon="mdi:battery",
    ),
    "remaing_capacity": SensorEntityDescription(
        key="remaing_capacity",
        name="Battery Pack Ramaining Capacity",
        icon="mdi:battery-50",
    ),
    "SOC": SensorEntityDescription(
        key="SOC",
        name="SOC",
        icon="mdi:battery-plus-variant",
    ),
    "amps": SensorEntityDescription(
        key="amp",
        name="Charge/Discharge Amps",
        icon="mdi:battery-sync",
    ),
    "life_cycle": SensorEntityDescription(
        key="life_cycle",
        name="Cycles",
        icon="mdi:counter",
    ),
    "port_voltage": SensorEntityDescription(
        key="port_voltage",
        name="Port Voltage",
        icon="mdi:battery-charging-outline",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "last_updated": SensorEntityDescription(
        key="last_updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        name="Last Updated",
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    )
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Seplos sensor."""

    coordinator: SeplosUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    k = SensorEntityDescription(
            key="total_cell_count",
            name="Total Number of Cells",
            icon="mdi:counter",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
    sen = SeplosSensor(coordinator, k,entry)
    entities.append(sen)

    for cell in range(1, coordinator.seplos._cellcount):
        k = SensorEntityDescription(
            key="cell" + cell,
            name="Cell " + cell,
            icon="mdi:battery-outline",
            native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        )
        sen = SeplosSensor(coordinator, k,entry)
        entities.append(sen)

    for warns in range(1, 6):
        k = SensorEntityDescription(
            key="warn" + warns,
            name="Warning " + warns,
            icon="mdi:car-brake-alert",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        sen = SeplosSensor(coordinator, k,entry)
        entities.append(sen)

    for celltemps in range(1, 4):
        k = SensorEntityDescription(
            key="temp" + celltemps,
            name="Cell Temp Sensor " + celltemps,
            icon="mdi:thermometer",
            native_unit_of_measurement=TEMP_CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        sen = SeplosSensor(coordinator, k,entry)
        entities.append(sen)

    k = SensorEntityDescription(
            key="temp5",
            name="BMS Temperature ",
            icon="mdi:thermometer",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
    sen = SeplosSensor(coordinator, k,entry)
    entities.append(sen)

    k = SensorEntityDescription(
            key="temp6",
            name="Total Number of Cells",
            icon="mdi:thermometer",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
    sen = SeplosSensor(coordinator, k,entry)
    entities.append(sen)

    for sensor_types in SENSORS:
        sen = SeplosSensor(coordinator, SENSORS[sensor_types],entry)
        entities.append(sen)
    
    async_add_entities(entities)

class SeplosSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Seplos Sensor device."""


    def __init__(
        self,
        coordinator: SeplosUpdateCoordinator,
        entity_description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = entity_description
    
        self.coordinator = coordinator

        ATTRIBUTION: Final = "Data from Seplos LCD rs485 port"
        _attr_attribution = ATTRIBUTION

        self._attributes = {}
        self._attr_extra_state_attributes = {}

        self._sensor_data = coordinator.get_sensor_value(entity_description.key)
        
        self._attr_device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
            ATTR_NAME: "Seplos LCD rs485", #entry.title,
            ATTR_MANUFACTURER: "Seplos",
            ATTR_MODEL: "Seplos LCD rs 485",
            ATTR_ENTRY_TYPE: DeviceEntryType.SERVICE,
            #"configuration_url": "https://toolkit.solcast.com.au/live-forecast",
            #"configuration_url": f"https://toolkit.solcast.com.au/rooftop-sites/{entry.options[CONF_RESOURCE_ID]}/detail",
            #"hw_version": entry.options[CONF_RESOURCE_ID],
        }

        self._unique_id = f"seplos_api_{entity_description.name}"

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
        return f"seplos_{self._unique_id}"

    @property
    def extra_state_attributes(self):
        """Return the state extra attributes of the binary sensor."""
        return self.coordinator.get_sensor_extra_attributes(self.entity_description.key)

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
        self._sensor_data = self.coordinator.get_sensor_value(self.entity_description.key)
        self.async_write_ha_state()


# class SeplosSensor(CoordinatorEntity, SensorEntity):
#     """Representation of a Seplos Sensor device."""


#     def __init__(
#         self,
#         coordinator: SeplosUpdateCoordinator,
#         entity_description: SensorEntityDescription,
#         entry: ConfigEntry,
#     ) -> None:
#         """Initialize the sensor."""
#         super().__init__(coordinator)

#         self.entity_description = entity_description
#         #self._id = f"solcast_{entity_description.key}"
#         self.coordinator = coordinator

#         ATTRIBUTION: Final = "Data provided by Solcast Solar"
#         _attr_attribution = ATTRIBUTION

#         self._attributes = {}
#         self._attr_extra_state_attributes = {}
        
#         self._sensor_data = coordinator.get_site_value(entity_description.key)
        
#         self._attr_device_info = {
#             ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
#             ATTR_NAME: "Seplos API Forecast", #entry.title,
#             ATTR_MANUFACTURER: "Solcast Solar",
#             ATTR_MODEL: "Seplos API",
#             ATTR_ENTRY_TYPE: DeviceEntryType.SERVICE,
#             "configuration_url": "https://toolkit.solcast.com.au/live-forecast",
#             #"configuration_url": f"https://toolkit.solcast.com.au/rooftop-sites/{entry.options[CONF_RESOURCE_ID]}/detail",
#             #"hw_version": entry.options[CONF_RESOURCE_ID],
#         }

#         self._unique_id = f"solcast_api_{entity_description.name}"

#     @property
#     def name(self):
#         """Return the name of the device."""
#         return f"Solcast {self.entity_description.name}"

#     @property
#     def friendly_name(self):
#         """Return the name of the device."""
#         return self.entity_description.name

#     @property
#     def unique_id(self):
#         """Return the unique ID of the binary sensor."""
#         return f"solcast_{self._unique_id}"

#     @property
#     def extra_state_attributes(self):
#         """Return the state extra attributes of the binary sensor."""
#         return self.coordinator.get_site_extra_attributes(self.entity_description.key)

#     @property
#     def native_value(self):
#         """Return the value reported by the sensor."""
#         return self._sensor_data

#     @property
#     def should_poll(self) -> bool:
#         """Return if the sensor should poll."""
#         return False

#     async def async_added_to_hass(self) -> None:
#         """When entity is added to hass."""
#         await super().async_added_to_hass()
#         self.async_on_remove(
#             self.coordinator.async_add_listener(self._handle_coordinator_update)
#         )

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Handle updated data from the coordinator."""
#         self._sensor_data = self.coordinator.get_site_value(self.entity_description.key)
#         self.async_write_ha_state()
