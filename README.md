
# HA Solcast PV Solar Forecast Integration

Home Assistant(https://www.home-assistant.io) Integration Component

This custom component integrates the Solcast Hobby PV Forecast API into Home Assistant.
[<img src="https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png" width="200">](https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

```
⚠️ Solcast have altered their API limits for new account creators

Solcast now only offer new account creators 10 api calls per day (used to be 50). 
Old account users still have 50 api calls

The integration now no longer includes auto api polling. Users now need to create their own automations
to call the update solcast service to poll for new data. Keep in mind your API poll limit.
```

## Solcast Requirements:
Sign up for an API key (https://solcast.com/)

> Solcast may take up to 24hrs to create the account

Copy the API Key for use with this integration (See [Configuration](#Configuration) below).

## Installation

### HACS *(recommended)*

Using HACS. More info [here](https://hacs.xyz/)  

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=oziee&repository=ha-solcast-solar&category=plugin)

Manually in HACS  
Follow the link [here](https://hacs.xyz/docs/faq/custom_repositories/)  
Use the custom repo link `https://github.com/oziee/ha-solcast-solar`  
Select the category type `integration`  
Then once it's there (still in HACS) click the INSTALL button  
Then go to the HA Devices and Services and add a new Solcast Integration  



<summary><h3>Manually</summary></h3>

You probably **do not** want to do this! Use the HACS method above unless you know what you are doing and have a good reason as to why you are installing manually

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
1. If you do not have a `custom_components` directory there, you need to create it
1. In the `custom_components` directory create a new folder called `solcast_solar`
1. Download _all_ the files from the `custom_components/solcast_solar/` directory in this repository
1. Place the files you downloaded in the new directory you created
1. *Restart HA to load the new integration*
1. See [Configuration](#configuration) below



## Configuration

1. [Click Here](https://my.home-assistant.io/redirect/config_flow_start/?domain=solcast_solar) to directly add a `Solcast Solar` integration **or**<br/>
 a. In Home Assistant, go to Settings -> [Integrations](https://my.home-assistant.io/redirect/integrations/)<br/>
 b. Click `+ Add Integrations` and select `Solcast PV Forecast`<br/>
1. Enter you `Solcast API Key`
1. Click `Submit`

* Create your own [automation](#services) to call the service `solcast_solar.update_forecasts` when you like it to call

* Change the configuration options for an existing `Solcast PV Forecast` integration in the Home Assistant Integrations by selecting Solcast then `Configure` (cog wheel)

* If you have more than one Solcast account because you have more than 2 rooftop setups, enter both account API keys separated by a comma `xxxxxxxx-xxxxx-xxxx,yyyyyyyy-yyyyy-yyyy` (NB: this goes against Solcast T&C's by having more than one account)

* Make sure you enter your `API Key` not your rooftop id created in Solcast. You can find your API key here [api key](https://toolkit.solcast.com.au/account)

[<img src="https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/install.png" width="200">](https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/install.png)

## Dampening Configuration

New in v4.0.8 is the option to configure hourly dampening values

[<img src="https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/reconfig.png" width="200">](https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/reconfig.png)

[<img src="https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/damp.png" width="200">](https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/damp.png)

Here you can change the dampening factor value for any hour. Values from 0.0 - 1.0 are valid. Setting 0.95 will dampen each Solcast forecast data value by 5%. This is reflected in the sensor values and attributes and also in the graphical Home Assistant Energy dashboard.

[<img src="https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/dampopt.png" width="200">](https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/dampopt.png)

## Services
These are the services for this integration ([Configuration](#configuration))

| Service | Action |
| --- | --- |
| `solcast_solar.update_forecasts` | Updates the future forecast data only |
| `solcast_solar.clear_all_solcast_data` | Deletes the `solcast.json` cached file |
| `solcast_solar.query_forecast_data` | Returns a list of forecast data using a datetime range start - end |
| `solcast_solar.set_dampening` | Updates the hourly dampening factors |
| `solcast_solar.set_hard_limit` | Set inverter forecast hard limit |
| `solcast_solar.remove_hard_limit` | Remove inverter forecast hard limit |

### Basic HA Automation to manual poll Solcast API data
Create a new HA automation and setup your prefered trigger times to manually poll for new Solcast forecast data.  
These are examples.. alter these or create your own to fit your own needs


```yaml
alias: Solcast_update
description: New API call Solcast
trigger:
 - platform: time_pattern
   hours: /4
condition:
 - condition: sun
   before: sunset
   after: sunrise
action:
 - delay:
     seconds: "{{ range(30, 360)|random|int }}"
 - service: solcast_solar.update_forecasts
   data: {}
mode: single
```

or

```yaml
alias: Solcast update
description: ""
trigger:
  - platform: time
    at: "4:00:00"
  - platform: time
    at: "10:00:00"
  - platform: time
    at: "16:00:00"
condition: []
action:
  - delay:
      seconds: "{{ range(30, 360)|random|int }}"
  - service: solcast_solar.update_forecasts
    data: {}
mode: single
```
To make the most of the available API calls, you can call the API in an interval calculated by the number of daytime hours divided by the number of total API calls a day you can make:

```yaml
alias: Solcast update
description: ""
trigger:
  - platform: template
    value_template: >-
      {% set nr = as_datetime(state_attr('sun.sun','next_rising')) | as_local %}
      {% set ns = as_datetime(state_attr('sun.sun','next_setting')) | as_local %}
      {% set api_request_limit = 10 %}
      {% if nr > ns %}
        {% set nr = nr - timedelta(hours = 24) %} 
      {% endif %}
      {% set hours_difference = (ns - nr) %}
      {% set interval_hours = hours_difference / api_request_limit %}
      {% set ns = namespace(match = false) %}
      {% for i in range(api_request_limit) %}
        {% set start_time = nr + (i * interval_hours) %}
        {% if ((start_time - timedelta(seconds=30)) <= now()) and (now() <= (start_time + timedelta(seconds=30))) %}
          {% set ns.match = true %}
        {% endif %}
      {% endfor %}
      {{ ns.match }}
condition:
  - condition: sun
    before: sunset
    after: sunrise
action:
  - delay:
      seconds: "{{ range(30, 360)|random|int }}"
  - service: solcast_solar.update_forecasts
    data: {}
mode: single
```

> **Note**
> _If you have two arrays on your roof then 2 api calls will be made for each update, effectively reducing the number of updates to 5 per day. For this case, change to: `api_request_limit = 5`_


<summary><h3>Set up HA Energy Dashboard settings</summary></h3>

Go to the `HA>Settings>Dashboards>Energy`

Click the 'edit the Solar Production' item you have previously created in the Energy dashboard. 


> **Note**
> _If you do not have a solar generation sensor in your system then this integration will not work in the Energy dashboard. The graph, and adding the forecast integration rely on there being a generation sensor setup_

[<img src="https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png" width="200">](https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png)

Click the Forecast option button and select the Solcast Solar option.. Click SAVE.. HA will do all the rest for you

[<img src="https://user-images.githubusercontent.com/1471841/174471543-0833b141-0c97-4b90-a058-cf986e89bbce.png" width="200">](https://user-images.githubusercontent.com/1471841/174471543-0833b141-0c97-4b90-a058-cf986e89bbce.png)

## HA Views:

<summary><h3>HA Energy Tab</summary></h3>

[<img src="https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png" width="200">](https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png)

<summary><h3>Sensors</summary></h3>

| Name | Type | Attributes | Unit | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Today` | number | Y | `kWh` | Total forecast solar production for today |
| `Tomorrow` | number | Y | `kWh` | Total forecast solar production for day + 1 (tomorrow) |
| `D3` | number | Y | `kWh` | Total forecast solar production for day + 2 (day 3) |
| `D4` | number | Y | `kWh` | Total forecast solar production for day + 3 (day 4) |
| `D5` | number | Y | `kWh` | Total forecast solar production for day + 4 (day 5) |
| `D6` | number | Y | `kWh`| Total forecast solar production for day + 5 (day 6) |
| `D7` | number | Y | `kWh` | Total forecast solar production for day + 6 (day 7) |
| `This Hour` | number | N | `Wh` | Forecasted solar production current hour |
| `Next Hour` | number | N | `Wh` | Forecasted solar production next hour |
| `Forecast Next X Hours` | number | N | `kWh` | Custom user defined X hour forecast |
| `Remaining Today` | number | N | `kWh` | Predicted remaining solar production today |
| `Peak Forecast Today` | number | N | `W` | Highest predicted production within an hour period today |
| `Peak Time Today` | date/time | N |  | Hour of max forecasted production of solar today |
| `Peak Forecast Tomorrow` | number | N | `W` | Highest predicted production within an hour period tomorrow |
| `Peak Time Tomorrow` | date/time | N |  | Hour of max forecasted production of solar tomorrow |
| `Power Now` | number | N | `W` | Power forecast during the current 0-30 / 30-59 min hour period |
| `Power Next 30 Mins` | number | N | `W` | Power forecast for the next 30 min block period |
| `Power Next Hour` | number | N | `W` | Power forecast for the next block 60 min from now |


### Configuration

| Name | Type | Attributes | Unit | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Forecast Field` | selector | N |  | selector to select the Solcast value field for calculations either 'estimate', 'estimate10' or 'estimate90' |

### Diagnostic

| Name | Type | Attributes | Unit | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `API Last Polled` | date/time | N |  | Date/time when the API data was polled |
| `API Limit` | number | N | `integer` | Total times the API can been called in a 24 hour period[^1] |
| `API used` | number | N | `integer` | Total times the API has been called today (API counter resets to zero at midnight UTC)[^1] |  
| `Hard Limit Set` |  | N |  | `False` is not set, else set integer value in `watts`. Can only be set or removed by service ([services](#services))|
| `Rooftop(s) name` | number | Y | `kWh` | Total forecast for rooftop today (attributes contain the solcast rooftop setup)[^2] |

[^1]: API usage information is directly read from Solcast
[^2]: Each rooftop created in Solcast will be listed separately

<summary><h3>Credits</summary></h3>

Modified from the great works of
* @rany2 - ranygh@riseup.net
* dannerph/homeassistant-solcast
* cjtapper/solcast-py
* home-assistant-libs/forecast_solar
