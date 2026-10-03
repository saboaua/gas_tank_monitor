# Gas Tank Card – Loading Instructions

## Automatic (v1.4.2+)

On install/restart the integration:

1. Copies `gas-tank-card.js` → `config/www/gas-tank-card.js`
2. Registers static path `/gas_tank_monitor-card/`
3. Injects the script via the frontend
4. Tries to add a Lovelace **module** resource at `/local/gas-tank-card.js`

After restart, hard-refresh the browser (`Ctrl+Shift+R`).

## If you still see "Custom element doesn't exist"

### 1) Confirm the file is served

Open in the browser:

`http://YOUR-HA:8123/local/gas-tank-card.js`

You must see JavaScript source (not 404).

### 2) Add the resource manually

**Settings → Dashboards → ⋮ → Resources → Add Resource**

| Field | Value |
|--------|--------|
| URL | `/local/gas-tank-card.js` |
| Type | **JavaScript Module** |

Then hard-refresh.

### 3) Console check

```js
customElements.get("gas-tank-card")
```

Must not be `undefined`. Look for `GAS-TANK-CARD 2.2.3`.

## YAML card

```yaml
type: custom:gas-tank-card
entity: sensor.gas_tank_monitor_level
name: Propane Tank
show_burn_rate: true
show_forecast: true
```
