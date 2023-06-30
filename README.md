# Solcast Solar

Home Assistant(https://www.home-assistant.io/) Component

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)


This custom component integrates the Solcast Hobby PV Forecast API into Home Assistant.


## Solcast have altered their API limits for new account creators:
Solcast now only offer new account creators 10 api calls per day (used to be 50). Old account users still have 50 api calls

The integration allows users to disable the auto api polling. Users can create their own automations to call the update solcast service to poll for new data to adjust for the max 10 api poll limit.

## Solcast Requirements:
Sign up for an API key (https://solcast.com/)

^Solcast may take up to 24hrs to apply the 50 API counter from the default 10.. give it time to work:)
-this seems to not be the case anymore for new account creators that sign up

Copy the API Key for use with this integration.

## Install

<details>
<summary><h3>via HACS</summary></h3>

Easy install by default on HACS. More info [here](https://hacs.xyz/).

or click on:
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=oziee&repository=ha-solcast-solar&category=plugin)

</details>

<details>
<summary><h3>Manualy</summary></h3>

1. Download the [latest release zip file](https://github.com/oziee/ha-solcast-solar/releases).
1. Unzip and copy the `solcast_solar` directory to your Home Assistant `config/custom_components` directory

*Restart HA to load the new integration*


In Home Assistant / Settings / Devices & Services click the `Add Integration`.
1. Search and add `Solcast PV Forecast`.
1. Enter you `Solcast API Key`.
1. Choose to either use the auto polling for data (not great if your stuck with only the new 10 poll limit), or disable and create your own automation to call the service `solcast_solar.update_forecasts` or `solcast_solar.update_actual_forecasts` when you like it to call.

</details>

## Basic Installation/Configuration Instructions:

If you have more than one Solcast account because you have more than 2 rooftop setups, enter both account API keys seperated by a comma `xxxxxxxx-xxxxx-xxxx,yyyyyyyy-yyyyy-yyyy`

*This is you `API Key` not your rooftop id created in Solcast. You can find your API key here [api key](https://toolkit.solcast.com.au/account)

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
| `Rooftop name` | number | Y | `kWh` | Total forecast for today for this rootop item created in Solcast |

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
