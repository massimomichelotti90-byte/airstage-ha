# Fujitsu AIRSTAGE Cloud for Home Assistant

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=massimomichelotti90-byte&repository=airstage-ha&category=integration)

Control Fujitsu AIRSTAGE air conditioners through the cloud service used by the AIRSTAGE mobile app.

## Features

- Climate entity with power, HVAC mode, and target temperature controls
- Separate indoor and outdoor temperature sensors for each unit
- Temperature sensors recorded by Home Assistant and available for History graphs
- Shared cloud refresh every 60 seconds
- Integration icon and Italian and English translations

Room and outdoor readings use AIRSTAGE's temperature encoding: `(raw - 5000) / 100` °C. The outdoor sensor has no value if the controller does not report an outdoor temperature.

## Installation

Once this repository is in the Home Assistant Marketplace catalog, search for **Fujitsu AIRSTAGE Cloud** in **Settings → Apps → Marketplace**.

Until then, add this GitHub repository as a custom **Integration** in the Marketplace, or copy `custom_components/airstage` into `<config>/custom_components/airstage` and restart Home Assistant.

After installation, select **Settings → Devices & services → Add integration → Fujitsu AIRSTAGE Cloud**. Choose the region used by the AIRSTAGE app, then enter the same account credentials. Home Assistant stores the credentials in the config entry.

## Supported controls

- Power and HVAC modes: auto, cool, dry, fan, and heat
- Target temperature
- Indoor and outdoor temperatures, when reported by the unit

Fan speed is not exposed yet because its cloud parameter mapping has not been confirmed across supported units.

## Notes

The AIRSTAGE cloud API is undocumented and may vary by region, account, or controller model. This is an unofficial community integration.
