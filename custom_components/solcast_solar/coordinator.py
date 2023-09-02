"""The Solcast Solar integration."""
from __future__ import annotations

import logging
import traceback
from contextlib import suppress
from datetime import timedelta

import async_timeout
import homeassistant.util.dt as dt_util
from homeassistant.components.recorder import get_instance #, history
#from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_utc_time_change

from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .const import DOMAIN
from .solcastapi import SolcastApi

_LOGGER = logging.getLogger(__name__)

class SolcastUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Solcast Solar API."""

    def __init__(self, hass: HomeAssistant, solcast: SolcastApi, version: str) -> None:
        """Initialize."""
        self.solcast = solcast
        self._hass = hass
        self._previousenergy = None
        self._version = version

        #self._v = f"{MAJOR_VERSION}.{MINOR_VERSION}"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )


    async def _async_update_data(self):
        """Update data via library."""
        return self.solcast._data
            
    # async def reset_past_data(self, *args):
    #     try:
    #         _LOGGER.debug("SOLCAST - resetting past data")
    #         await get_instance(self._hass).async_add_executor_job(self.gethistory)
    #     except Exception as error:
    #         _LOGGER.error("SOLCAST - reset_past_data: Error resetting past data")

    async def setup(self):
        # try:
        #     _LOGGER.debug("SOLCAST - setting up the coordinator")
        #     await get_instance(self._hass).async_add_executor_job(self.gethistory)
        # except Exception:
        #     _LOGGER.error("SOLCAST - Error coordinator setup to get past history data")
        d={}
        self._previousenergy = d

        try:
            #async_track_utc_time_change(self._hass, self.reset_past_data, hour=0, minute=0, second=30, local=True)
            #async_track_utc_time_change(self._hass, self.update_integration_listeners, minute=0, second=15, local=True)
            async_track_utc_time_change(self._hass, self.update_integration_listeners, second=0)
        except Exception as error:
            _LOGGER.error("SOLCAST - Error coordinator setup: %s", traceback.format_exc())


    async def update_integration_listeners(self, *args):
        try:
            self.async_update_listeners()
        except Exception:
            _LOGGER.error("SOLCAST - update_integration_listeners: %s", traceback.format_exc())

    # async def update_forecast(self, *args):
    #     """Update forecast state."""

    #     try:
    #         #_LOGGER.info("SOLCAST: Update forcast data called. Is the time is right")
    #         last_update = self.solcast.get_last_updated_datetime() 
    #         date_now = dt_util.now() - timedelta(seconds=3500)
    #         if last_update < date_now:
    #             #been a long time since last update so update it
    #             date_now = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
    #             if last_update < date_now:
    #                 #more than a day since uopdate
    #                 _LOGGER.debug("SOLCAST - Longer than a day since last update. Updating forecast and actual data.")
    #                 await self.solcast.force_api_poll(True)
    #             else:
    #                 #sometime today.. 
    #                 _hournow = dt_util.now().hour
    #                 if _hournow == 0 or _hournow == self._starthour or _hournow == self._finishhour:
    #                     #if midnight, or sunrise hour or sunset set run it
    #                     if  _hournow == self._finishhour:
    #                         _LOGGER.debug("SOLCAST - its finish hour, update forecast and actual data")
    #                         await self.solcast.force_api_poll(True)
    #                     else:
    #                         _LOGGER.debug("SOLCAST - its midnight - update api data call")
    #                         await self.solcast.force_api_poll(False)
    #                 elif (_hournow > self._starthour and _hournow < self._finishhour):
    #                     #else its between sun rise and set
    #                     _LOGGER.debug("SOLCAST - between sun rise/set. Calling forcast_update")
    #                     if self.solcast._sites:
    #                         #if we have sites to even poll
    #                         #if _hournow % 3 == 0: 
    #                         if _hournow == 12: 
    #                             _LOGGER.debug("SOLCAST - The call for forecast and actual")
    #                             await self.solcast.force_api_poll(True) #also do the actual past values
    #                         else:
    #                             _LOGGER.debug("SOLCAST - The call for forecast only")
    #                             await self.solcast.force_api_poll(False) #just update forecast values
                                
    #         else:
    #             _LOGGER.debug("SOLCAST - API poll called, but did not happen as the last update is less than an hour old")
            
    #         await self.update_integration_listeners()

    #     except Exception:
    #         _LOGGER.error("SOLCAST - update_forecast: %s", traceback.format_exc())

    async def service_event_update(self, *args):
        _LOGGER.info("SOLCAST - Event called to force an update of data from Solcast API")
        await self.solcast.http_data(dopast=False)
        await self.update_integration_listeners()

    async def service_event_delete_old_solcast_json_file(self, *args):
        _LOGGER.info("SOLCAST - Event called to delete the solcast.json file. The data will poll the Solcast API refresh")
        await self.solcast.delete_solcast_file()

    async def service_get_forecasts(self, *args) -> str:
        _LOGGER.info("SOLCAST - Event called to get list of forecasts")
        return await self.solcast.get_forecast_list()

    def get_energy_tab_data(self):
        return self.solcast.get_energy_data()

    def get_sensor_value(self, key=""):
        if key == "total_kwh_forecast_today":
            return self.solcast.get_total_kwh_forecast_day(0)
        elif key == "peak_w_today":
            return self.solcast.get_peak_w_day(0)
        elif key == "peak_w_time_today":
            return self.solcast.get_peak_w_time_day(0)
        elif key == "forecast_this_hour":
            return self.solcast.get_forecast_n_hour(0)
        elif key == "forecast_next_hour":
            return self.solcast.get_forecast_n_hour(1)
        elif key == "forecast_next_12hour":
            return self.solcast.get_forecast_n_hour(12)
        elif key == "forecast_next_24hour":
            return self.solcast.get_forecast_n_hour(24)
        elif key == "total_kwh_forecast_tomorrow":
            return self.solcast.get_total_kwh_forecast_day(1) 
        elif key == "total_kwh_forecast_d3":
            return self.solcast.get_total_kwh_forecast_day(2)
        elif key == "total_kwh_forecast_d4":
            return self.solcast.get_total_kwh_forecast_day(3)
        elif key == "total_kwh_forecast_d5":
            return self.solcast.get_total_kwh_forecast_day(4)
        elif key == "total_kwh_forecast_d6":
            return self.solcast.get_total_kwh_forecast_day(5)
        elif key == "total_kwh_forecast_d7":
            return self.solcast.get_total_kwh_forecast_day(6)
        elif key == "power_now":
            return self.solcast.get_power_production_n_mins(0)
        elif key == "power_now_30m":
            return self.solcast.get_power_production_n_mins(30)
        elif key == "power_now_1hr":
            return self.solcast.get_power_production_n_mins(60)
        elif key == "power_now_12hr":
            return self.solcast.get_power_production_n_mins(60*12)
        elif key == "power_now_24hr":
            return self.solcast.get_power_production_n_mins(60*24)
        elif key == "peak_w_tomorrow":
            return self.solcast.get_peak_w_day(1)
        elif key == "peak_w_time_tomorrow":
            return self.solcast.get_peak_w_time_day(1)
        elif key == "get_remaining_today":
            return self.solcast.get_remaining_today()
        elif key == "api_counter":
            return self.solcast.get_api_used_count()
        elif key == "api_limit":
            return self.solcast.get_api_limit()
        elif key == "lastupdated":
            return self.solcast.get_last_updated_datetime()

        #just in case
        return None

    def get_sensor_extra_attributes(self, key=""):
        if key == "total_kwh_forecast_today":
            return self.solcast.get_forecast_day(0)
        elif key == "total_kwh_forecast_tomorrow":
            return self.solcast.get_forecast_day(1)
        elif key == "total_kwh_forecast_d3":
            return self.solcast.get_forecast_day(2)
        elif key == "total_kwh_forecast_d4":
            return self.solcast.get_forecast_day(3)
        elif key == "total_kwh_forecast_d5":
            return self.solcast.get_forecast_day(4)
        elif key == "total_kwh_forecast_d6":
            return self.solcast.get_forecast_day(5)
        elif key == "total_kwh_forecast_d7":
            return self.solcast.get_forecast_day(6)

        #just in case
        return None

    def get_site_sensor_value(self, roof_id, key):
        match key:
            case "site_data":
                return self.solcast.get_rooftop_site_total_today(roof_id)
            case _:
                return None

    def get_site_sensor_extra_attributes(self, roof_id, key):
        match key:
            case "site_data":
                return self.solcast.get_rooftop_site_extra_data(roof_id)
            case _:
                return None
        
    # def gethistory(self):
    #     try:
    #         start_date = dt_util.now().astimezone().replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=7)
    #         end_date = dt_util.now().astimezone().replace(hour=23,minute=59,second=59,microsecond=0) - timedelta(days=1)
    #         _LOGGER.debug(f"SOLCAST - gethistory: from- {start_date} to- {end_date}")

    #         lower_entity_id = "sensor.solcast_forecast_this_hour"
    #         history_list = history.state_changes_during_period(
    #             self._hass,
    #             start_time=dt_util.as_utc(start_date),
    #             end_time=dt_util.as_utc(end_date),
    #             entity_id=lower_entity_id,
    #             no_attributes=True,
    #             descending=True,
    #         )

    #         d={}
    #         for state in history_list.get(lower_entity_id, []):
    #             # filter out all None, NaN and "unknown" states
    #             # only keep real values
    #             with suppress(ValueError):
    #                 d[state.last_updated.replace(minute=0,second=0,microsecond=0).astimezone().isoformat()] = float(state.state)

    #         _LOGGER.debug(f"SOLCAST - gethistory got {len(d)} items")
    #         self._previousenergy = d
    #     except Exception:
    #         _LOGGER.error("SOLCAST - gethistory: %s", traceback.format_exc())