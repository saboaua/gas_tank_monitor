# Gas Tank Monitor

Custom Home Assistant integration + Lovelace card for monitoring LPG / Propane gas cylinders (optimized for Caribbean 100 lb tanks).

## What the card looks like

<img src="images/gas-tank-card-example.png" alt="Gas Tank Monitor card showing 19% full, 4.4 of 23.6 gallons remaining, burn rate, days since full, and a depletion forecast" width="360">

The card shows current fill level with a gauge, remaining volume in gallons, burn rate (Gal/Day), days since the tank was last full, and a depletion/refill forecast with a quick-order shortcut. The status pill (e.g. "CRITICAL") changes color based on your configured low/alert thresholds.

## Features

- Config Flow (UI setup)
- Accepts an existing pressure (PSI) or level sensor
- Calculates:
  - % Full
  - Volume remaining (Gallons)
  - Burn rate (Gal/Day)
  - Days since last full
  - Forecast days until recommended switch (default 20%)
- Modern light-theme Lovelace card with tank gauge
- Appears in the official “Add Card” picker
- Fully configurable via visual editor

## Installation (HACS)

1. Add this repository as a custom repository in HACS (Integration category)
2. Download “Gas Tank Monitor”
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → Gas Tank Monitor**
5. Follow the config flow
6. Add the card: **Edit Dashboard → Add Card → Custom: Gas Tank Card**

## Manual Installation

Copy the `custom_components/gas_tank_monitor` folder into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

After adding the integration, open its **Configure** options to link sensors and set up the tank:

<img src="images/gas-tank-monitor-options.png" alt="Gas Tank Monitor Options screen with Pressure Sensor, Level Sensor, Temperature Sensor, Battery Sensor, Signal Strength Sensor, and Tank Size fields" width="360">

- **Pressure Sensor (PSI)** — your ESPHome/analog pressure entity (required if no Level Sensor is set)
- **Level Sensor (%)** — a direct level entity (e.g. an ultrasonic sensor), used instead of pressure if set
- **Temperature Sensor (optional)** — improves the pressure-to-level conversion, since tank pressure varies with temperature
- **Battery Sensor (optional)** and **Signal Strength Sensor (optional)** — surfaced as diagnostic attributes on the card
- **Tank Size** — 20 / 30 / 40 / 100 lb or a custom capacity in gallons

These can be changed anytime from **Settings → Devices & Services → Gas Tank Monitor → Configure** without removing the integration.

## Lovelace Card

The card is automatically registered.  
In the visual editor you can select:

- Level / pressure entity
- Tank size (20 / 30 / 40 / 100 lb or custom)
- Which sections to display

## Supported Tank Sizes

- 20 lb
- 30 lb
- 40 lb
- **100 lb (Caribbean default)**
- Custom capacity in gallons

## Notes

Pressure-to-level conversion uses a simplified LPG curve with optional temperature compensation.  
For best accuracy use an ultrasonic sensor (e.g. Mopeka) as the source entity.

## License

MIT
