# Gas Tank Monitor

Custom Home Assistant integration + Lovelace card for monitoring LPG / Propane gas cylinders (optimized for Caribbean 100 lb tanks).

## Preview

![Gas Tank Card](path/to/gasmonitorcard.png)

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

## Card Overview

The visual UI component displays full status metrics at a glance:

* **Header Status:** Sensor status header with live state alerts (e.g., `CRITICAL`, `WARNING`, `OK`)[cite: 1].
* **Main Tank Gauge:** Large percentage indicator, volume remaining (e.g., `1.6 / 23.6 Gal`), and visual threshold indicators for `Max (80%)`, `50%`, `Low (20%)`, and `Alert (10%)`[cite: 1].
* **Burn Rate:** Real-time daily usage consumption (`Gal/Day`) along with trend comparisons[cite: 1].
* **Days Since Full:** Tracks full refill duration with exact timestamp tracking[cite: 1].
* **Depletion & Refill Forecast:** Time-to-depletion indicator with an interactive **Order** button[cite: 1].
* **Footer Actions:** Quick navigation shortcuts for **Tank History** and **Calibrate** setup[cite: 1].

## Installation (HACS)

1. Add this repository as a custom repository in HACS (Integration category)
2. Download “Gas Tank Monitor”
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → Gas Tank Monitor**
5. Follow the config flow
6. Add the card: **Edit Dashboard → Add Card → Custom: Gas Tank Card**

## Manual Installation

Copy the `custom_components/gas_tank_monitor` folder into your Home Assistant `config/custom_components/` directory and restart.

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
