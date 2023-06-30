# HomeAssistnat Solcast PV Solar Forecast Integration

Home Assistant(https://www.home-assistant.io/) Component

This custom component integrates the Solcast Hobby PV Forecast API into Home Assistant.
[<img src="https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png" width="200">]

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

```
⚠ **Solcast have altered their API limits for new account creators** 

Solcast now only offer new account creators 10 api calls per day (used to be 50). 
Old account users still have 50 api calls

The integration allows users to disable the auto api polling to create their own automations
to call the update solcast service to poll for new data to allow for the max 10 api poll limit.
```

## Solcast Requirements:
Sign up for an API key (https://solcast.com/)

!! Solcast may take up to 24hrs to create the account

Copy the API Key for use with this integration (See [Configuration](#Configuration) below).

## Installation

### HACS *(recommended)*

Easy install by default on HACS. More info [here](https://hacs.xyz/).

or click on:
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=oziee&repository=ha-solcast-solar&category=plugin)


<details>
<summary><h3>Manualy</summary></h3>

You probably **do not** want to do this! Use the HACS method above unless you know what you are doing and have a good reason as to why you are installing manually

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
1. If you do not have a `custom_components` directory there, you need to create it
1. In the `custom_components` directory create a new folder called `solcast_solar`
1. Download _all_ the files from the `custom_components/solcast_solar/` directory in this repository
1. Place the files you downloaded in the new directory you created
1. *Restart HA to load the new integration*
1. See [Configuration](#configuration) below

</details>

## Configuration

1. [Click Here](https://my.home-assistant.io/redirect/config_flow_start/?domain=solcast_solar) to directly add a `Solcast Solar` integration **or**<br/>
 a. In Home Assistant, go to Settings -> [Integrations](https://my.home-assistant.io/redirect/integrations/)<br/>
 b. Click `+ Add Integrations` and select `Solcast PV Forecast`<br/>
1. Enter you `Solcast API Key`
1. Choose to enable auto polling or not (enable if you only have like 10 API call limit, requires you to create your own automation to call the service `solcast_solar.update_forecasts` or `solcast_solar.update_actual_forecasts` when you like it to call)
1. Click `Submit`

* Options can be changed for existing `Solcast PV Forecast` integration in Home Assistant Integrations by selecting `Configure` (cog wheel)

* If you have more than one Solcast account because you have more than 2 rooftop setups, enter both account API keys seperated by a comma `xxxxxxxx-xxxxx-xxxx,yyyyyyyy-yyyyy-yyyy`

* This is you `API Key` not your rooftop id created in Solcast. You can find your API key here [api key](https://toolkit.solcast.com.au/account)

[<img src="https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/install.png" width="200">](https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/install.png)

<details>

<summary><h3>Basic HA Automation to manual poll Solcast API data</summary></h3>
Create a new HA automation and setup your prefered triggers to manually poll for new data
This is an example.. create your own to your own needs


```yaml
alias: Solcast_update
description: New API call Solcast
trigger:
 - platform: time_pattern
   minutes: "0"
   seconds: "0"
condition:
 - condition: sun
   before: sunset
   after: sunrise
action:
 - service: solcast_solar.update_forecasts
   data: {}
mode: single
```

</details>
<details>
<summary><h3>Set up HA Energy Dashboard settings</summary></h3>

Go to the `HA>Settings>Dashboards>Energy`
Click the edit the Solar Production item you have created. 


> **Note**
> _If you do not have a solar sensor in your system then this integration will not work. The graph, and adding the forecast integration rely on there being a sensor setup to be added here_

[<img src="https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png" width="200">](https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png)


Click the Forecast option button and select the Solcast Solar option.. Click SAVE.. HA will do all the rest for you

[<img src="https://user-images.githubusercontent.com/1471841/174471543-0833b141-0c97-4b90-a058-cf986e89bbce.png" width="200">](https://user-images.githubusercontent.com/1471841/174471543-0833b141-0c97-4b90-a058-cf986e89bbce.png)

</details>

## HA Views:
<details>
<summary><h3>HA Energy Tab</summary></h3>

[<img src="https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png" width="200">](https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png)

</details>
<details>
<summary><h3>Sensors</summary></h3>

[<img src="https://github.com/oziee/ha-solcast-solar/raw/v3/.github/SCREENSHOTS/sensors.png" width="200">](https://github.com/oziee/ha-solcast-solar/raw/v3/.github/SCREENSHOTS/sensors.png)

| Name | Type | Attributes | Default | Description |
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
| `Remaining Today` | number | N | `kWh` | Predicted remaining solar production today |
| `Peak Forecast Today` | number | N | `Wh` | Highest predicted production within an hour period today |
| `Peak Time Today` | date/time | N |  | Hour of max forecasted production of solar today |
| `Peak Forecast Tomorrow` | number | N | `Wh` | Highest predicted production within an hour period tomorrow |
| `Peak Time Tomorrow` | date/time | N |  | Hour of max forecasted production of solar tomorrow |

### Configuration

<img src="https://github.com/oziee/ha-solcast-solar/raw/v3/.github/SCREENSHOTS/conf.png" alt="sensors" style="width: 200px;">

| Name | Type | Attributes | Default | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Rooftop name` | number | Y | `kWh` | Total forecast for rooftop today (attributes contain the full solcast data) |

### Diagnostic

<img src="https://github.com/oziee/ha-solcast-solar/raw/v3/.github/SCREENSHOTS/diag.png" alt="sensors" style="width: 200px;">

| Name | Type | Attributes | Default | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `API Last Polled` | date/time | N |  | Date/time when the API data was polled |
| `API used` | number | N | `integer` | Total times the API has been called today (API counter resets to zero at midnight UTC) |


</details>

<summary><h3>Credits</summary></h3>

Modified from the great works of
* dannerph/homeassistant-solcast
* cjtapper/solcast-py
* home-assistant-libs/forecast_solar