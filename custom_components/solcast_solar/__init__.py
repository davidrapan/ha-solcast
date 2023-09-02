"""Support for Solcast PV forecast."""

import logging

from homeassistant import loader
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import (HomeAssistant,
                                ServiceResponse,
                                SupportsResponse,)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.device_registry import async_get as device_registry
from homeassistant.util import dt as dt_util


from .const import (DOMAIN,
                    SERVICE_CLEAR_DATA, SERVICE_UPDATE, SERVICE_GET_FORECAST, SOLCAST_URL)
from .coordinator import SolcastUpdateCoordinator
from .solcastapi import ConnectionOptions, SolcastApi

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up solcast parameters."""
    options = ConnectionOptions(
        entry.options[CONF_API_KEY],
        SOLCAST_URL,
        hass.config.path('solcast.json'),
        dt_util.get_time_zone(hass.config.time_zone),
    )

    solcast = SolcastApi(aiohttp_client.async_get_clientsession(hass), options)
    
    try:
        await solcast.sites_data()
        await solcast.sites_usage()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Getting sites data failed: {ex}") from ex

    await solcast.load_saved_data()
    
    _VERSION = ""
    try:
        integration = await loader.async_get_integration(hass, DOMAIN)
        _VERSION = str(integration.version)
        _LOGGER.info(f"Solcast Integration version number: {_VERSION}")
    except loader.IntegrationNotFound:
        pass
    
    coordinator = SolcastUpdateCoordinator(hass, solcast, _VERSION)
    
    await coordinator.setup()

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    

    _LOGGER.info(f"SOLCAST - Solcast API data UTC times are converted to {hass.config.time_zone}")

    async def handle_service_update_forecast(call):
        """Handle service call"""
        _LOGGER.info(f"SOLCAST - Service call: {SERVICE_UPDATE}")
        await coordinator.service_event_update()

    async def handle_service_clear_solcast_data(call):
        """Handle service call"""
        _LOGGER.info(f"SOLCAST - Service call: {SERVICE_CLEAR_DATA}")
        await coordinator.service_event_delete_old_solcast_json_file()

    async def handle_service_get_solcast_data(call) -> ServiceResponse:
        """Handle service call"""
        _LOGGER.info(f"SOLCAST - Service call: {SERVICE_GET_FORECAST}")
        d = await coordinator.service_get_forecasts()
        return {"data": [d]}

    hass.services.async_register(DOMAIN, SERVICE_UPDATE, handle_service_update_forecast)

    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_DATA, handle_service_clear_solcast_data
    )

    hass.services.async_register(
        DOMAIN, SERVICE_GET_FORECAST, handle_service_get_solcast_data, None, SupportsResponse.ONLY,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    hass.services.async_remove(DOMAIN, SERVICE_UPDATE)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_DATA)
    hass.services.async_remove(DOMAIN, SERVICE_GET_FORECAST)

    return unload_ok

async def async_remove_config_entry_device(hass: HomeAssistant, entry: ConfigEntry, device) -> bool:
    device_registry(hass).async_remove_device(device.id)
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Reload entry if options change."""
    _LOGGER.debug("Reloading entry %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Solcast Migrating from version %s", config_entry.version)

    if config_entry.version < 4:
        new_options = {**config_entry.options}
        new_options.pop("const_disableautopoll", None)

        config_entry.version = 4
        hass.config_entries.async_update_entry(config_entry, options=new_options)

    _LOGGER.debug("Solcast Migration to version %s successful", config_entry.version)

    return True