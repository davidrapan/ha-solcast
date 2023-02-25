"""Support for Seplos LCD Connection."""

import logging
import traceback

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as device_registry

from .const import DOMAIN, CONST_USB_ADDRESS
from .coordinator import SeplosUpdateCoordinator
from .seplosapi import ConnectionOptions, SeplosApi


PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Seplos parameters."""

    try:

        _LOGGER.debug("Seplos starting")

        options = ConnectionOptions(
            entry.options[CONST_USB_ADDRESS]
        )

        _LOGGER.debug("Seplos starting 1")

        seplos = SeplosApi(options)
        #await seplos.sites_data()
        _LOGGER.debug("Seplos starting 2")
        
        coordinator = SeplosUpdateCoordinator(hass, seplos)
        #await coordinator.setup()
        _LOGGER.debug("Seplos starting 3")

        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("Seplos starting 4")

        entry.async_on_unload(entry.add_update_listener(update_listener))
        _LOGGER.debug("Seplos starting 5")

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        _LOGGER.debug("Seplos starting 6")
        

        #hass.config_entries.async_setup_platforms(entry, PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.debug("Seplos starting 7")

        return True

    except Exception as err:
        _LOGGER.error("async_setup_entry: %s",traceback.format_exc())
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_remove_config_entry_device(hass: HomeAssistant, entry: ConfigEntry, device) -> bool:
    device_registry(hass).async_remove_device(device.id)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)

# async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
#     """Migrate old entry."""
#     try:
#         _LOGGER.debug("Seplos Config Migrating from version %s", config_entry.version)

#         if config_entry.version == 2:
#             #new_data = {**config_entry.options}
#             new_data = {**config_entry.options, CONST_DISABLEAUTOPOLL: False}

#             config_entry.version = 3
#             hass.config_entries.async_update_entry(config_entry, options=new_data)

#         _LOGGER.info("Seplos Config Migration to version %s successful", config_entry.version)
#         return True
#     except Exception as err:
#         _LOGGER.error("Seplos - async_migrate_entry error: %s",traceback.format_exc())
#         return False