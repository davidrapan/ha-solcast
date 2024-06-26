"""Solcast API."""
from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import traceback
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta, timezone
from operator import itemgetter
from os.path import exists as file_exists
from typing import Any, Dict, cast

import async_timeout
from aiohttp import ClientConnectionError, ClientSession
from aiohttp.client_reqrep import ClientResponse
from isodate import parse_datetime

_JSON_VERSION = 4
_LOGGER = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, dt):
            return o.isoformat()

class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            if key in {'period_start'}:
                ret[key] = dt.fromisoformat(value) 
            else:
                ret[key] = value
        return ret

@dataclass
class ConnectionOptions:
    """Solcast API options for connection."""

    api_key: str 
    host: str
    file_path: str
    tz: timezone
    dampening: dict
    customhoursensor: int
    key_estimate: str
    hard_limit: int


class SolcastApi:
    """Solcast API rooftop."""

    def __init__(
        self,
        aiohttp_session: ClientSession,
        options: ConnectionOptions,
        apiCacheEnabled: bool = False
    ):
        """Device init."""
        self.aiohttp_session = aiohttp_session
        self.options = options
        self.apiCacheEnabled = apiCacheEnabled
        self._sites = []
        self._data = {'siteinfo': {}, 'last_updated': None}
        self._api_used = None
        self._api_limit = None
        self._filename = options.file_path
        self._tz = options.tz
        self._dataenergy = {}
        self._data_forecasts = []
        self._detailedForecasts = []
        self._loaded_data = False
        self._serialize_lock = asyncio.Lock()
        self._damp =options.dampening
        self._customhoursensor = options.customhoursensor
        self._use_data_field = f"pv_{options.key_estimate}"
        self._hardlimit = options.hard_limit
        #self._weather = ""
        
    async def serialize_data(self):
        """Serialize data to file."""
        if not self._loaded_data:
            _LOGGER.debug(
                f"SOLCAST - serialize_data not saving data as it has not been loaded yet"
            )
            return

        async with self._serialize_lock:
            with open(self._filename, "w") as f:
                json.dump(self._data, f, ensure_ascii=False, cls=DateTimeEncoder)

    async def sites_data(self):
        """Request data via the Solcast API."""
        
        try:
            sp = self.options.api_key.split(",")
            for spl in sp:
                #params = {"format": "json", "api_key": self.options.api_key}
                params = {"format": "json", "api_key": spl.strip()}
                _LOGGER.debug(f"SOLCAST - trying to connect to - {self.options.host}/rooftop_sites?format=json&api_key=REDACTED")
                async with async_timeout.timeout(60):
                    if file_exists(self._filename.replace('solcast','sites')):
                        status = 404
                        with open(self._filename.replace('solcast','sites')) as f:
                            resp_json = json.load(f, cls=JSONDecoder)
                            status = 200
                    else:
                        resp: ClientResponse = await self.aiohttp_session.get(
                            url=f"{self.options.host}/rooftop_sites", params=params, ssl=False
                        )
        
                        resp_json = await resp.json(content_type=None)
                        status = resp.status
                        if status == 200:
                            async with self._serialize_lock:
                                with open(self._filename.replace('solcast','sites'), "w") as f:
                                    json.dump(resp_json, f, ensure_ascii=False, cls=DateTimeEncoder)
                            
                if status == 200:
                    d = cast(dict, resp_json)
                    _LOGGER.debug(f"SOLCAST - Status 200 OK - sites_data returned data: {d}")
                    for i in d['sites']:
                        i['apikey'] = spl.strip()
                        #v4.0.14 to stop HA adding a pin to the map
                        i.pop('longitude', None)
                        i.pop('latitude', None)

                    self._sites = self._sites + d['sites']
                else:
                    _LOGGER.info(
                        f"SOLCAST - Status {status} - A problem occurred getting data from Solcast about the rooftop sites."
                    )
                    #raise Exception(f"SOLCAST - HTTP sites_data error: Solcast Error gathering rooftop sites data.")
        except json.decoder.JSONDecodeError:
            _LOGGER.error("SOLCAST - sites_data JSONDecodeError.. The data returned from Solcast is unknown, Solcast site could be having problems")
        except ConnectionRefusedError as err:
            _LOGGER.error("SOLCAST - sites_data ConnectionRefusedError Error.. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('SOLCAST - sites_data Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("SOLCAST - sites_data TimeoutError Error - Timed out connection to solcast server")
        except Exception as e:
            _LOGGER.error("SOLCAST - sites_data Exception error: %s", traceback.format_exc())
            
    async def sites_usage(self):
        """Request api usage via the Solcast API."""
        
        try:
            sp = self.options.api_key.split(",")

            params = {"api_key": sp[0]}
    
            async with async_timeout.timeout(60):
                resp: ClientResponse = await self.aiohttp_session.get(
                    url=f"https://api.solcast.com.au/json/reply/GetUserUsageAllowance", params=params, ssl=False
                )
                resp_json = await resp.json(content_type=None)
                status = resp.status

            if status == 200:
                d = cast(dict, resp_json)
                _LOGGER.debug(f"SOLCAST - Status {status} - sites_usage returned data: {d}")
                self._api_limit = d.get("daily_limit", None)
                self._api_used = d.get("daily_limit_consumed", None)
            else:
                self._api_limit = None
                self._api_used = None
                _LOGGER.debug(f"SOLCAST - Status {status} - sites_usage: gathering site data failed. Responce: {resp_json}.")
            
        except json.decoder.JSONDecodeError:
            _LOGGER.error("SOLCAST - sites_usage JSONDecodeError.. The data returned from Solcast is unknown, Solcast site could be having problems")
        except ConnectionRefusedError as err:
            _LOGGER.error("SOLCAST - sites_usage Error.. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('SOLCAST - sites_usage Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("SOLCAST - sites_usage Connection Error - Timed out connection to solcast server")
        except Exception as e:
            _LOGGER.error("SOLCAST - sites_usage error: %s", traceback.format_exc())

    # async def sites_weather(self):
    #     """Request rooftop site weather byline via the Solcast API."""
        
    #     try:
    #         if len(self._sites) > 0:
    #             sp = self.options.api_key.split(",")
    #             rid = self._sites[0].get("resource_id", None)

    #             params = {"resourceId": rid, "api_key": sp[0]}
    #             _LOGGER.debug(f"SOLCAST - get rooftop weather byline from solcast")
    #             async with async_timeout.timeout(60):
    #                 resp: ClientResponse = await self.aiohttp_session.get(
    #                     url=f"https://api.solcast.com.au/json/reply/GetRooftopSiteSparklines", params=params, ssl=False
    #                 )
    #                 resp_json = await resp.json(content_type=None)
    #                 status = resp.status

    #             if status == 200:
    #                 d = cast(dict, resp_json)
    #                 _LOGGER.debug(f"SOLCAST - sites_weather returned data: {d}")
    #                 self._weather = d.get("forecast_descriptor", None).get("description", None)
    #                 _LOGGER.debug(f"SOLCAST - rooftop weather description: {self._weather}")
    #             else:
    #                 raise Exception(f"SOLCAST - sites_weather: gathering rooftop weather description failed. request returned Status code: {status} - Responce: {resp_json}.")
                
    #     except json.decoder.JSONDecodeError:
    #         _LOGGER.error("SOLCAST - sites_weather JSONDecodeError.. The rooftop weather description from Solcast is unknown, Solcast site could be having problems")
    #     except ConnectionRefusedError as err:
    #         _LOGGER.error("SOLCAST - sites_weather Error.. %s",err)
    #     except ClientConnectionError as e:
    #         _LOGGER.error('SOLCAST - sites_weather Connection Error', str(e))
    #     except asyncio.TimeoutError:
    #         _LOGGER.error("SOLCAST - sites_weather Connection Error - Timed out connection to solcast server")
    #     except Exception as e:
    #         _LOGGER.error("SOLCAST - sites_weather error: %s", traceback.format_exc())

    async def load_saved_data(self):
        try:
            if len(self._sites) > 0:
                if file_exists(self._filename):
                    with open(self._filename) as data_file:
                        jsonData = json.load(data_file, cls=JSONDecoder)
                        json_version = jsonData.get("version", 1)
                        #self._weather = jsonData.get("weather", "unknown")
                        _LOGGER.debug(f"SOLCAST - load_saved_data file exists.. file type is {type(jsonData)}")
                        if json_version == _JSON_VERSION:
                            self._loaded_data = True
                            self._data = jsonData

                            #any new API keys so no sites data yet for those
                            ks = {}
                            for d in self._sites:
                                if not any(s == d.get('resource_id', '') for s in jsonData['siteinfo']):
                                    ks[d.get('resource_id')] = d.get('apikey')

                            if len(ks.keys()) > 0:
                                #some api keys rooftop data does not exist yet so go and get it
                                _LOGGER.debug("SOLCAST - Must be new API jey added so go and get the data for it")
                                for a in ks:
                                    await self.http_data_call(r_id=a, api=ks[a], dopast=True)
                                await self.serialize_data()

                            #any site changes that need to be removed
                            l = []
                            for s in jsonData['siteinfo']:
                                if not any(d.get('resource_id', '') == s for d in self._sites):
                                    _LOGGER.info(f"Solcast rooftop resource id {s} no longer part of your system.. removing saved data from cached file")
                                    l.append(s)

                            for ll in l:
                                del jsonData['siteinfo'][ll]

                            #create an up to date forecast and make sure the TZ fits just in case its changed                
                            await self.buildforcastdata()
                                    
                if not self._loaded_data:
                    #no file to load
                    _LOGGER.debug(f"SOLCAST - load_saved_data there is no existing file with saved data to load")
                    #could be a brand new install of the integation so this is poll once now automatically
                    await self.http_data(dopast=True)
            else:
                _LOGGER.debug(f"SOLCAST - load_saved_data site count is zero! ")
        except json.decoder.JSONDecodeError:
            _LOGGER.error("SOLCAST - load_saved_data error: The cached data is corrupt")
        except Exception as e:
            _LOGGER.error("SOLCAST - load_saved_data error: %s", traceback.format_exc())

    async def delete_solcast_file(self, *args):
        _LOGGER.debug(f"SOLCAST - service event to delete old solcast.json file")
        try:
            if file_exists(self._filename):
                os.remove(self._filename)
                await self.sites_data()
                await self.load_saved_data()
        except Exception:
            _LOGGER.error(f"SOLCAST - service event to delete old solcast.json file failed")
            
    async def get_forecast_list(self, *args):
        try:
            tz = self._tz
            
            return tuple(
                {
                    **d,
                    "period_start": d["period_start"].astimezone(tz),
                }
                for d in self._data_forecasts
                if d["period_start"] >= args[0] and d["period_start"] < args[1]
            )

        except Exception:
            _LOGGER.error(f"SOLCAST - service event to get list of forecasts failed")
            return None

    def get_api_used_count(self):
        """Return API polling count for this UTC 24hr period"""
        return self._api_used

    def get_api_limit(self):
        """Return API polling limit for this account"""
        try:
            return self._api_limit
        except Exception:
            return None

    # def get_weather(self):
    #     """Return weather description"""
    #     return self._weather
    
    def get_last_updated_datetime(self) -> dt:
        """Return date time with the data was last updated"""
        try:
            return dt.fromisoformat(self._data["last_updated"])
        except Exception as ex:
            return None

    def get_rooftop_site_total_today(self, rooftopid) -> float:
        """Return a rooftop sites total kw for today"""
        return self._data["siteinfo"][rooftopid]["tally"]

    def get_rooftop_site_extra_data(self, rooftopid = ""):
        """Return a rooftop sites information"""
        g = tuple(d for d in self._sites if d["resource_id"] == rooftopid)
        if len(g) != 1:
            raise ValueError(f"Unable to find rooftop site {rooftopid}")
        site: Dict[str, Any] = g[0]
        ret = {}

        ret["name"] = site.get("name", None)
        ret["resource_id"] = site.get("resource_id", None)
        ret["capacity"] = site.get("capacity", None)
        ret["capacity_dc"] = site.get("capacity_dc", None)
        ret["longitude"] = site.get("longitude", None)
        ret["latitude"] = site.get("latitude", None)
        ret["azimuth"] = site.get("azimuth", None)
        ret["tilt"] = site.get("tilt", None)
        ret["install_date"] = site.get("install_date", None)
        ret["loss_factor"] = site.get("loss_factor", None)
        for key in tuple(ret.keys()):
            if ret[key] is None:
                ret.pop(key, None)

        return ret
        
    def get_forecast_day(self, futureday) -> Dict[str, Any]:
        """Return Solcast Forecasts data for N days ahead"""
        noDataError = True

        tz = self._tz
        da = dt.now(tz).date() + timedelta(days=futureday)
        h = tuple(
            d
            for d in self._data_forecasts
            if d["period_start"].astimezone(tz).date() == da
        )
        
        tup = tuple(
                {**d, "period_start": d["period_start"].astimezone(tz)} for d in h
            )

        if len(tup) < 48:
            noDataError = False

        hourlyturp = []
        for index in range(0,len(tup),2):
            if len(tup)>0:
                try:
                    x1 = round((tup[index]["pv_estimate"] + tup[index+1]["pv_estimate"]) /2, 4)
                    x2 = round((tup[index]["pv_estimate10"] + tup[index+1]["pv_estimate10"]) /2, 4)
                    x3 = round((tup[index]["pv_estimate90"] + tup[index+1]["pv_estimate90"]) /2, 4)
                    hourlyturp.append({"period_start":tup[index]["period_start"], "pv_estimate":x1, "pv_estimate10":x2, "pv_estimate90":x3})
                except IndexError:
                    x1 = round((tup[index]["pv_estimate"]), 4)
                    x2 = round((tup[index]["pv_estimate10"]), 4)
                    x3 = round((tup[index]["pv_estimate90"]), 4)
                    hourlyturp.append({"period_start":tup[index]["period_start"], "pv_estimate":x1, "pv_estimate10":x2, "pv_estimate90":x3})  
            

        return {
            "detailedForecast": tup,
            "detailedHourly": hourlyturp,
            "dayname": da.strftime("%A"),
            "dataCorrect": noDataError,
        }

    def get_forecast_n_hour(self, hourincrement) -> int:
        # This technically is for the given hour in UTC time, not local time;
        # this is because the Solcast API doesn't provide the local time zone
        # and returns 30min intervals that doesn't necessarily align with the
        # local time zone. This is a limitation of the Solcast API and not
        # this code, so we'll just have to live with it.
        try:
            da = dt.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(hours=hourincrement)
            g = tuple(
                d
                for d in self._data_forecasts
                if d["period_start"] >= da and d["period_start"] < da + timedelta(hours=1)
            )
            m = sum(z[self._use_data_field] for z in g) / len(g)

            return int(m * 1000)
        except Exception as ex:
            return None
        
    def get_forecast_custom_hour(self, hourincrement) -> int:
        """Return Custom Sensor Hours forecast for N hours ahead"""
        try:
            danow = dt.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            )
            da = dt.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(hours=hourincrement)
            g=[]
            for d in self._data_forecasts:
                if d["period_start"] >= danow and d["period_start"] < da:
                    g.append(d)
            
            m = sum(z[self._use_data_field] for z in g)

            return int(m * 500)
        except Exception as ex:
            return None

    def get_power_production_n_mins(self, minuteincrement) -> float:
        """Return Solcast Power Now data for N minutes ahead"""
        try:
            da = dt.now(timezone.utc) + timedelta(minutes=minuteincrement)
            m = min(
                (z for z in self._data_forecasts), key=lambda x: abs(x["period_start"] - da)
            )
            return int(m[self._use_data_field] * 1000)
        except Exception as ex:
            return None

    def get_peak_w_day(self, dayincrement) -> int:
        """Return hour of max kw for rooftop site N days ahead"""
        try:
            tz = self._tz
            da = dt.now(tz).date() + timedelta(days=dayincrement)
            g = tuple(
                d
                for d in self._data_forecasts
                if d["period_start"].astimezone(tz).date() == da
            )
            m = max(z[self._use_data_field] for z in g)
            return int(m * 1000)
        except Exception as ex:
            return None

    def get_peak_w_time_day(self, dayincrement) -> dt:
        """Return hour of max kw for rooftop site N days ahead"""
        try:
            tz = self._tz
            da = dt.now(tz).date() + timedelta(days=dayincrement)
            g = tuple(
                d
                for d in self._data_forecasts
                if d["period_start"].astimezone(tz).date() == da
            )
            #HA strips any TZ info set and forces UTC tz, so dont need to return with local tz info
            return max((z for z in g), key=lambda x: x[self._use_data_field])["period_start"]
        except Exception as ex:
            return None

    def get_remaining_today(self) -> float:
        """Return Remaining Forecasts data for today"""
        try:
            tz = self._tz
            da = dt.now(tz).replace(second=0, microsecond=0) 

            if da.minute < 30:
                da = da.replace(minute=0)
            else:
                da = da.replace(minute=30)
            
            g = tuple(
                d
                for d in self._data_forecasts
                if d["period_start"].astimezone(tz).date() == da.date() and d["period_start"].astimezone(tz) >= da
            )

            return sum(z[self._use_data_field] for z in g) / 2
        except Exception as ex:
            return None

    def get_total_kwh_forecast_day(self, dayincrement) -> float:
        """Return total kwh total for rooftop site N days ahead"""
        try:
            tz = self._tz
            d = dt.now(tz) + timedelta(days=dayincrement)
            d = d.replace(hour=0, minute=0, second=0, microsecond=0)
            needed_delta = d.replace(hour=23, minute=59, second=59, microsecond=0) - d
            
            ret = 0.0
            for idx in range(1, len(self._data_forecasts)):
                prev = self._data_forecasts[idx - 1]
                curr = self._data_forecasts[idx]

                prev_date = prev["period_start"].astimezone(tz).date()
                cur_date = curr["period_start"].astimezone(tz).date()
                if prev_date != cur_date or cur_date != d.date():
                    continue

                delta: timedelta = curr["period_start"] - prev["period_start"]
                diff_hours = delta.total_seconds() / 3600
                ret += (prev[self._use_data_field] + curr[self._use_data_field]) / 2 * diff_hours
                needed_delta -= delta
            return ret
        except Exception as ex:
            return None
    
    def get_energy_data(self) -> dict[str, Any]:
        try:
            return self._dataenergy
        except Exception as e:
            _LOGGER.error(f"SOLCAST - get_energy_data: {e}")
            return None

    async def http_data(self, dopast = False):
        """Request forecast data via the Solcast API."""
        lastday = dt.now(self._tz) + timedelta(days=7)
        lastday = lastday.replace(hour=23,minute=59).astimezone(timezone.utc)

        for site in self._sites:
            _LOGGER.debug(f"SOLCAST - API polling for rooftop {site['resource_id']}")
            #site=site['resource_id'], apikey=site['apikey'],
            ok = await self.http_data_call(site['resource_id'], site['apikey'], dopast)
            if ok is None:
                return
            
            if len(self._sites) > 1:
                #try to stop Solcast from rate limiting calling too fast
                #little 3 sec sleep before calling API again
                await asyncio.sleep(3)

        self._data["last_updated"] = dt.now(timezone.utc).isoformat()
        #await self.sites_usage()
        self._data["version"] = _JSON_VERSION
        #self._data["weather"] = self._weather
        self._loaded_data = True
        
        await self.buildforcastdata()
        await self.serialize_data()

    async def http_data_call(self, r_id = None, api = None, dopast = False):
        """Request forecast data via the Solcast API."""
        lastday = dt.now(self._tz) + timedelta(days=7)
        lastday = lastday.replace(hour=23,minute=59).astimezone(timezone.utc)
        pastdays = dt.now(self._tz).date() + timedelta(days=-730)
        _LOGGER.debug(f"SOLCAST - Polling API for rooftop_id {r_id}")

        _data = []
        _data2 = []
        
        #this is one run once, for a new install or if the solcasft.json file is deleted
        #this does use up an api call count too
        if dopast:
            ae = None
            resp_dict = await self.fetch_data("estimated_actuals", 168, site=r_id, apikey=api, cachedname="actuals")
            if resp_dict is None:
                return None
            
            if not isinstance(resp_dict, dict):
                _LOGGER.warning("SOLCAST - No data was returned so this WILL cause errors.. either your limit is up, internet down.. what ever the case is it is NOT a problem with the integration, and all other problems of sensor values being wrong will be a seen")
                _LOGGER.debug(f"Solcast - Status {resp_dict.status} - API did not return a json object. Returned {resp_dict}")
                return None
            
            ae = resp_dict.get("estimated_actuals", None)
            
            if not isinstance(ae, list):
                raise TypeError(f"estimated actuals must be a list, not {type(ae)}")
            else:
                oldest = dt.now(self._tz).replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=6)
                oldest = oldest.astimezone(timezone.utc)

                for x in ae:
                    z = parse_datetime(x["period_end"]).astimezone(timezone.utc)
                    z = z.replace(second=0, microsecond=0) - timedelta(minutes=30)
                    if z.minute not in {0, 30}:
                        raise ValueError(
                            f"Solcast period_start minute is not 0 or 30. {z.minute}"
                        )
                    if z > oldest:
                        _data2.append(
                            {
                                "period_start": z,
                                "pv_estimate": x["pv_estimate"],
                                "pv_estimate10": 0,
                                "pv_estimate90": 0,
                            }
                        )

        resp_dict = await self.fetch_data("forecasts", 168, site=r_id, apikey=api, cachedname="forecasts")
        if resp_dict is None:
            return None
        if not isinstance(resp_dict, dict):
            raise TypeError(f"Solcast - API fectching data did not return a json object. Returned {resp_dict}")
        
        af = resp_dict.get("forecasts", None)
        if not isinstance(af, list):
            raise TypeError(f"forecasts must be a list, not {type(af)}")
        else:
            _LOGGER.debug(f"SOLCAST - Solcast returned {len(af)} records (should be 168)")

            for x in af:
                z = parse_datetime(x["period_end"]).astimezone(timezone.utc)
                z = z.replace(second=0, microsecond=0) - timedelta(minutes=30)
                if z.minute not in {0, 30}:
                    raise ValueError(
                        f"Solcast period_start minute is not 0 or 30. {z.minute}"
                    )
                if z < lastday:
                    _data2.append(
                        {
                            "period_start": z,
                            "pv_estimate": x["pv_estimate"],
                            "pv_estimate10": x["pv_estimate10"],
                            "pv_estimate90": x["pv_estimate90"],
                        }
                    )

            _data = sorted(_data2, key=itemgetter("period_start"))
            _forecasts = []

            try:
                _forecasts = self._data['siteinfo'][r_id]['forecasts']
            except Exception:
                pass
        
            for x in _data:
                #loop each rooftop site and its forecasts
                
                itm = next((item for item in _forecasts if item["period_start"] == x["period_start"]), None)
                if itm:
                    itm["pv_estimate"] = x["pv_estimate"]
                    itm["pv_estimate10"] = x["pv_estimate10"]
                    itm["pv_estimate90"] = x["pv_estimate90"]
                else:    
                    # _LOGGER.debug("adding itm")
                    _forecasts.append({"period_start": x["period_start"],"pv_estimate": x["pv_estimate"],
                                                            "pv_estimate10": x["pv_estimate10"],
                                                            "pv_estimate90": x["pv_estimate90"]})
            
            #_forecasts now contains all data for the rooftop site up to 730 days worth
            #this deletes data that is older than 730 days (2 years)   
            for x in _forecasts:
                zz = x['period_start'].astimezone(self._tz) - timedelta(minutes=30)
                if zz.date() < pastdays:
                    _forecasts.remove(x)
        
            _forecasts = sorted(_forecasts, key=itemgetter("period_start"))
            
            self._data['siteinfo'].update({r_id:{'forecasts': copy.deepcopy(_forecasts)}})
    
        return True

    async def fetch_data(self, path= "", hours=168, site="", apikey="", cachedname="forcasts") -> dict[str, Any]:
        """fetch data via the Solcast API."""
        
        try:
            params = {"format": "json", "api_key": apikey, "hours": hours}
            url=f"{self.options.host}/rooftop_sites/{site}/{path}"
            _LOGGER.debug(f"SOLCAST - fetch_data code url - {url}")

            async with async_timeout.timeout(120):
                apiCacheFileName = cachedname + "_" + site + ".json"
                if self.apiCacheEnabled and file_exists(apiCacheFileName):
                    _LOGGER.debug(f"SOLCAST - Getting cached testing data for site {site}")
                    status = 404
                    with open(apiCacheFileName) as f:
                        resp_json = json.load(f)
                        status = 200
                        _LOGGER.debug(f"SOLCAST - Got cached file data for site {site}")
                else:
                    #_LOGGER.debug(f"SOLCAST - OK REAL API CALL HAPPENING RIGHT NOW")
                    resp: ClientResponse = await self.aiohttp_session.get(
                        url=url, params=params, ssl=False
                    )
                    resp_json = await resp.json(content_type=None)
                    status = resp.status

                    if status == 200:
                        #_LOGGER.debug(f"SOLCAST - Status 200 OK - API returned data. API Counter incremented from {self._api_used} to {self._api_used + 1}")
                        #self._api_used = self._api_used + 1

                        _LOGGER.debug("SOLCAST - Status 200 OK - API returned data.")

                        if self.apiCacheEnabled:
                            with open(apiCacheFileName, 'w') as f:
                                json.dump(resp_json, f, ensure_ascii=False)
                        
                        d = cast(dict, resp_json)
                        _LOGGER.debug(f"SOLCAST - fetch_data Returned: {d}")
                        return d

                    elif status == 202:
                        _LOGGER.info(f"SOLCAST - Status 202 Accepted - The request was accepted but does not include any data in the response. {resp_json}")
                    elif status == 400:
                        _LOGGER.info(f"SOLCAST - Status 400 Bad Request - The request may have included invalid parameters. {resp_json}")
                        #raise Exception(f"HTTP error: The rooftop site missing capacity, please specify capacity or provide historic data for tuning.")
                    elif status == 401:
                        _LOGGER.info(f"SOLCAST - Status 401 Unauthorized - The request did not correctly include a valid API Key. {resp_json}")
                    elif status == 403:
                        _LOGGER.info(f"SOLCAST - Status 403 Forbidden - The request includes parameter(s) not available ")
                    elif status == 404:
                        _LOGGER.info("SOLCAST - Status 404. The rooftop site cannot be found or is not accessible.")
                        #raise Exception(f"HTTP error: The rooftop site cannot be found or is not accessible.")
                    elif status == 429:
                        _LOGGER.info(f"SOLCAST - Status 429 Too Many Requests - The request exceeds the available rate limit. {resp_json}")
                    elif status == 500:
                        _LOGGER.info(f"SOLCAST - Status 500 Internal Server Error - An internal error has prevented the request from processing.. {resp_json}")
                    else:
                        _LOGGER.info(f"SOLCAST - Status {status} - {resp_json}")
        except ConnectionRefusedError as err:
            _LOGGER.error("SOLCAST - Error. Connection Refused. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('SOLCAST - Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("SOLCAST - Connection Timeout Error - Timed out connectng to Solcast API server")
        except Exception as e:
            _LOGGER.error("SOLCAST - API Data Fetch Error: %s", traceback.format_exc())

        return None
    
    def makeenergydict(self) -> dict:
        wh_hours = {}
    
        try:
            lastv = -1
            lastk = -1
            for v in self._data_forecasts:
                d = v['period_start'].isoformat()
                if v[self._use_data_field] == 0.0:
                    if lastv > 0.0:
                        wh_hours[d] = round(v[self._use_data_field] * 500,0)
                        wh_hours[lastk] = 0.0
                    lastk = d
                    lastv = v[self._use_data_field]
                else:
                    if lastv == 0.0:
                        #add the last one
                        wh_hours[lastk] = round(lastv * 500,0)

                    wh_hours[d] = round(v[self._use_data_field] * 500,0)
                    
                    lastk = d
                    lastv = v[self._use_data_field]
        except Exception as e:
            _LOGGER.error("SOLCAST - makeenergydict: %s", traceback.format_exc())

        return wh_hours
    
    async def buildforcastdata(self):
        """build the data needed and convert where needed"""
        try:
            today = dt.now(self._tz).date()
            yesterday = dt.now(self._tz).date() + timedelta(days=-730)
            lastday = dt.now(self._tz).date() + timedelta(days=7)
            
            _forecasts = []
        
            for s in self._data['siteinfo']:
                tally = 0
                for x in self._data['siteinfo'][s]['forecasts']:   
                    #loop each rooftop site and its forecasts
                    z = x["period_start"]
                    zz = z.astimezone(self._tz) #- timedelta(minutes=30)

                    #v4.0.8 added code to dampen the forecast data.. (* self._damp[h])
                    
                    if zz.date() < lastday and zz.date() > yesterday:
                        h = f"{zz.hour}"
                        if zz.date() == today:
                            tally += min(x[self._use_data_field] * 0.5 * self._damp[h], self._hardlimit)
                        
                        itm = next((item for item in _forecasts if item["period_start"] == z), None)
                        if itm:
                            itm["pv_estimate"] = min(round(itm["pv_estimate"] + (x["pv_estimate"] * self._damp[h]),4), self._hardlimit)
                            itm["pv_estimate10"] = min(round(itm["pv_estimate10"] + (x["pv_estimate10"] * self._damp[h]),4), self._hardlimit)
                            itm["pv_estimate90"] = min(round(itm["pv_estimate90"] + (x["pv_estimate90"] * self._damp[h]),4), self._hardlimit)
                        else:    
                            _forecasts.append({"period_start": z,"pv_estimate": min(round((x["pv_estimate"]* self._damp[h]),4), self._hardlimit),
                                                                "pv_estimate10": min(round((x["pv_estimate10"]* self._damp[h]),4), self._hardlimit),
                                                                "pv_estimate90": min(round((x["pv_estimate90"]* self._damp[h]),4), self._hardlimit)})
                        
                self._data['siteinfo'][s]['tally'] = round(tally, 4)
                        
            _forecasts = sorted(_forecasts, key=itemgetter("period_start"))     
            
            self._data_forecasts = _forecasts 

            await self.checkDataRecords()
                    
            self._dataenergy = {"wh_hours": self.makeenergydict()}
                
        except Exception as e:
            _LOGGER.error("SOLCAST - http_data error: %s", traceback.format_exc())
        
    async def checkDataRecords(self):
        tz = self._tz
        for i in range(0,6):
            da = dt.now(tz).date() + timedelta(days=i)
            h = tuple(
                d
                for d in self._data_forecasts
                if d["period_start"].astimezone(tz).date() == da
            )

            if len(h) == 48:
                _LOGGER.debug(f"SOLCAST - Data for {da} contains all 48 records")
            else:
                _LOGGER.debug(f"SOLCAST - Data for {da} contains only {len(h)} of 48 records and may produce inaccurate forecast data")
            
            
    