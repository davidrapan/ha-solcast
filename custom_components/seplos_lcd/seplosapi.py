"""Seplos API."""
from __future__ import annotations


import logging
import traceback
from dataclasses import dataclass
from datetime import datetime
# from datetime import timedelta, timezone
# from operator import itemgetter


from time import sleep

import struct
#from crc import Calculator, Crc16
#import serial

# from typing import Any, cast

# from isodate import parse_datetime


_LOGGER = logging.getLogger(__name__)

# class DateTimeEncoder(json.JSONEncoder):
#     def default(self, o):
#         if isinstance(o, dt):
#             return o.isoformat()


@dataclass
class ConnectionOptions:
    """Seplos API options for connection."""
    usb_address: str 

class SeplosApitest:
    """Seplos API rooftop."""

    def __init__(self,options: ConnectionOptions):
        self._cellcount = 0

class SeplosApi:
    """Seplos API rooftop."""

    def __init__(
        self,
        options: ConnectionOptions
    ):
        """Device init."""
        self.options = options
        self._data = dict()
        self._cellcount = 0
        # self.client = mqtt.Client("seplos-pack1")
        # self.client.username_pw_set("mqtt", "Tree0154")
        #self.client.connect(mqttBroker) 
        # self.ser = serial.Serial(options.usb_address, 9600,parity=serial.PARITY_NONE,
        #     stopbits=serial.STOPBITS_ONE,
        #     bytesize=serial.EIGHTBITS)
        # self.ser.timeout=10
        # self.calculator = Calculator(Crc16.CCITT, optimized=True)


    async def update_seplos_data(self):
        """Request data via the Seplos API."""
        _LOGGER.debug("Seplos update_seplos_data called")
        
        # try:
        #     #if not ser.closed:
        #     self.ser.read_all() 
        #     sleep(1)
        #     # ser.flush()
        #     # ser.flush()
            
        #     received_data = self.ser.read_all() 
        #     ##print(received_data)
        #     ll = struct.unpack(str(len(received_data)) + 'c', received_data)
        #     #print(ll)

        #     bHex = received_data.hex()
        
        #     #CRC CHECK
        #     returneddata = bytes.fromhex(bHex[2:-6]) #whole data string to crc
        #     expected = int(bHex[-6:-2],16)
        #     crccheck = self.calculator.verify(returneddata, expected)
        
        #     if crccheck and bHex[0:8] == '55464610':
                
        #         #print(bHex[0:8])
        #         #print(bHex)

        #         #battery cells
        #         cellcounter = 1
        #         mincell = 0
        #         mincellid = 0
        #         maxcell = 0
        #         maxcellid = 0
        #         for i in range(8,72,4):
        #             #print(bHex[i:i+2])
        #             cell = int(bHex[i:i+4], 16)/1000
        #             key = "cell" + str(cellcounter)
        #             self._data.update({key: cell})
        #             #min or max cell item?
        #             if cell < mincell:
        #                 mincell = cell
        #                 mincellid = cellcounter
        #             if cell > maxcell:
        #                 maxcell = cell
        #                 maxcellid = cellcounter
        #                 if mincell == 0:
        #                     mincell = maxcell
        #             cellcounter+=1

        #         self._data.update({"min_cell": mincellid})
        #         self._data.update({"max_cell": maxcellid})
        #         self._data.update({"cell_deviation": round(maxcell-mincell,3)})


        #         tempcounter=1
        #         for i in range(74,98,4):
        #             #print(bHex[i:i+2])
        #             temp = bHex[i:i+4]
        #             key = "temp" + str(tempcounter)
        #             self._data.update({key: round(int(temp, 16)/100,1)})
        #             tempcounter+=1

        #         self._data.update({"amps": int(bHex[98:98+4], 16)/100})
        #         self._data.update({"total_volts": int(bHex[102:102+4], 16)/100})
        #         remaing_capacity = int(bHex[106:106+4], 16)
        #         battery_capacity = int(bHex[112:112+4], 16)
        #         self._data.update({"SOC": round((remaing_capacity*100)/battery_capacity,1)})
        #         self._data.update({"remaing_capacity": round(remaing_capacity/100,1)})
        #         self._data.update({"battery_capacity": battery_capacity/100})
        #         self._data.update({"life_cycle": int(bHex[116:116+4], 16)})
        #         self._data.update({"port_voltage": int(bHex[120:120+4], 16)/100})
        #         self._data.update({"system_status": int(bHex[124:124+2], 16)})
        #         self._data.update({"switch_status": int(bHex[126:126+2], 16)})

        #         warncounter=1
        #         for i in range(130,142,2):
        #             #print(bHex[i:i+2])
        #             warn = bHex[i:i+2]
        #             key = "warn" + str(warncounter)
        #             self._data.update({key: int(warn, 16)})
        #             warncounter+=1  

        #         self._data.update({"reserved_1": int(bHex[142:142+2], 16)})
        #         self._data.update({"reserved_2": int(bHex[144:144+2], 16)}) 
        #         self._data.update({"last_updated": datetime.utcnow()})             

        #         print(self._data)
        #         # for i in range(0, len(ll) ):
        #         #     print (ll[i].hex())

        #         #print(int(bHex[120:120+4], 16))

        #     else:
        #         print("serial CRC failed")
        #         self.ser = serial.Serial("/dev/cu.usbserial-A50285BI", 9600,parity=serial.PARITY_NONE,
        #                 stopbits=serial.STOPBITS_ONE,
        #                 bytesize=serial.EIGHTBITS)
        #         self.ser.timeout=10
        #         #self.readBMS()
        
        # except Exception as e:
        #     _LOGGER.error("Seplos sites_data error: %s", traceback.format_exc())


    # def get_rooftop_site_extra_data(self, rooftopid = "") -> float:
    #     """Return a rooftop sites total kw for today"""
    #     try:
    #         g = [d for d in self._sites if d['resource_id'] == rooftopid]   
    #         site = g[0]
    #         d = {}

    #         if "name" in site:
    #             d["name"] = site["name"]
    #         if "resource_id" in site:
    #             d["resource_id"] = site["resource_id"]
    #         if "capacity" in site:
    #             d["capacity"] = site["capacity"]
    #         if "capacity_dc" in site:
    #             d["capacity_dc"] = site["capacity_dc"]
    #         if "longitude" in site:
    #             d["longitude"] = site["longitude"]
    #         if "latitude" in site:
    #             d["latitude"] = site["latitude"]
    #         if "azimuth" in site:
    #             d["azimuth"] = site["azimuth"]
    #         if "tilt" in site:
    #             d["tilt"] = site["tilt"]
    #         if "install_date" in site:
    #             d["install_date"] = site["install_date"]
    #         if "loss_factor" in site:
    #             d["loss_factor"] = site["loss_factor"]

    #         return d
    #     except Exception:
    #         return {}
