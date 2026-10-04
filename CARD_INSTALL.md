# Gas Tank Card – Fix "Custom element doesn't exist"

## Quick fix (most installs)

1. **Restart Home Assistant** after installing/updating the integration.
2. Open in a browser tab:  
   `http://YOUR-HA:8123/local/gas-tank-card.js?v=2.2.6`  
   You **must** see JavaScript source (starts with `/**`).  
   If you get **404**, the file was not copied — continue below.
3. **Settings → Dashboards → ⋮ (top right) → Resources → Add Resource**

   | Field | Value |
   |--------|--------|
   | URL | `/local/gas-tank-card.js?v=2.2.6` |
   | Type | **JavaScript Module** |

4. Hard-refresh the browser: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac).
5. Console check (F12 → Console):

```js
customElements.get("gas-tank-card")
// should be a function/class, not undefined
```

Look for: `GAS-TANK-CARD 2.2.6`

## Service repair

**Developer Tools → Services**

- Service: `gas_tank_monitor.register_card`
- Call service → restart is not required, then hard-refresh the browser.

## Still broken?

1. Confirm the integration is configured: **Settings → Devices & Services → Gas Tank Monitor**.
2. Check HA logs for `gas_tank_monitor` / `Card copied`.
3. Delete any old resource pointing at a wrong path, add the one above.
4. Try the alternate URL as a resource: `/gas_tank_monitor-card/gas-tank-card.js?v=2.2.6`

## YAML card (after element loads)

```yaml
type: custom:gas-tank-card
entity: sensor.gas_tank_monitor_level
name: Propane Tank
show_burn_rate: true
show_forecast: true
```
