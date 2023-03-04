"""The Seplos integration."""
from __future__ import annotations

import logging
import traceback


#from homeassistant.exceptions import HomeAssistantError

from homeassistant.core import HomeAssistant

from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator, UpdateFailed)

from .const import DOMAIN
from .seplosapi import SeplosApi


_LOGGER = logging.getLogger(__name__)


class SeplosUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Seplos LCD device."""

    def __init__(self, hass: HomeAssistant, seplos: SeplosApi) -> None:
        """Initialize."""
        self.seplos = seplos
        self._hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )


    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.update_seplos_data()
        except Exception as error:
            _LOGGER.debug("SEPLOS: _async_update_data error!")
        return self.seplos._data


#await get_instance(self._hass).async_add_executor_job(self.gethistory)
    

    async def update_seplos_data(self,*args):
        """Update seplos state."""

        try:
            _LOGGER.debug("SEPLOS: begin code for updating")
            await self.seplos.update_seplos_data()
                
            _LOGGER.debug("SEPLOS: updating listerners")
            self.async_update_listeners()

        except Exception:
            _LOGGER.error("update_seplos_data: %s", traceback.format_exc())



    def get_sensor_value(self, key=""):
        # if key == "total_kwh_forecast_today":
        #     return self.seplos.get_total_kwh_forecast_today()
        # elif key == "peak_w_today":
        #     return self.seplos.get_peak_w_today()
        # elif key == "peak_w_time_today":
        #     return self.seplos.get_peak_w_time_today()
        # elif key == "forecast_this_hour":
        #     return self.seplos.get_forecast_this_hour()
        # elif key == "forecast_next_hour":
        #     return self.seplos.get_forecast_next_hour()
        # elif key == "total_kwh_forecast_tomorrow":
        #     return self.seplos.get_total_kwh_forecast_furture_for_day(1) 
        # elif key == "total_kwh_forecast_d3":
        #     return self.seplos.get_total_kwh_forecast_furture_for_day(2)
        # elif key == "total_kwh_forecast_d4":
        #     return self.seplos.get_total_kwh_forecast_furture_for_day(3)
        # elif key == "total_kwh_forecast_d5":
        #     return self.seplos.get_total_kwh_forecast_furture_for_day(4)
        # elif key == "total_kwh_forecast_d6":
        #     return self.seplos.get_total_kwh_forecast_furture_for_day(5)
        # elif key == "total_kwh_forecast_d7":
        #     return self.seplos.get_total_kwh_forecast_furture_for_day(6)
        # elif key == "peak_w_tomorrow":
        #     return self.seplos.get_peak_w_tomorrow()
        # elif key == "peak_w_time_tomorrow":
        #     return self.seplos.get_peak_w_time_tomorrow()
        # elif key == "get_remaining_today":
        #     return self.seplos.get_remaining_today()
        # elif key == "api_counter":
        #     return self.seplos.get_api_used_count()
        # elif key == "lastupdated":
        #     return self.seplos.get_last_updated_datetime()
        try:
            if not key == "":
                return self.seplos._data[key]
            
            #just in case
            return None
        except Exception:
            _LOGGER.error("get_sensor_value: %s", traceback.format_exc())
            return None

    # def get_sensor_extra_attributes(self, key=""):
    #     if key == "total_kwh_forecast_today":
    #         return self.seplos.get_forecast_today()
    #     elif key == "total_kwh_forecast_tomorrow":
    #         return self.seplos.get_forecast_future_day(1)
    #     elif key == "total_kwh_forecast_d3":
    #         return self.seplos.get_forecast_future_day(2)
    #     elif key == "total_kwh_forecast_d4":
    #         return self.seplos.get_forecast_future_day(3)
    #     elif key == "total_kwh_forecast_d5":
    #         return self.seplos.get_forecast_future_day(4)
    #     elif key == "total_kwh_forecast_d6":
    #         return self.seplos.get_forecast_future_day(5)
    #     elif key == "total_kwh_forecast_d7":
    #         return self.seplos.get_forecast_future_day(6)

    #     #just in case
    #     return None

    # def get_site_value(self, key=""):
    #     return self.seplos.get_rooftop_site_total_today(key)

