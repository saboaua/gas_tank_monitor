# Gas Tank Card – Loading Instructions

If you see **"Custom element doesn't exist: gas-tank-card"**, the JavaScript file is not loaded.

## Method 1 – Automatic (preferred)

1. Restart Home Assistant after installing/updating the integration.
2. Hard-refresh the browser (Ctrl+Shift+R / Cmd+Shift+R).
3. Open browser console (F12) and check for:
   `GAS-TANK-CARD 2.1.0`
4. Also try opening this URL in the same browser (replace with your HA host):
   `http://HOMEASSISTANT:8123/gas_tank_monitor-card/gas-tank-card.js`
   You should see the JavaScript source. If you get 404, the static path failed.

## Method 2 – Manual Resource (most reliable)

1. Settings → Dashboards → ⋮ → **Resources** → **Add Resource**
2. URL: `/gas_tank_monitor-card/gas-tank-card.js`
3. Type: **JavaScript Module**
4. Create → Hard-refresh browser

## Method 3 – /local/ fallback

1. Copy `custom_components/gas_tank_monitor/www/gas-tank-card.js` from this repository
   into your Home Assistant `config/www/gas-tank-card.js` folder
   (create the `www` folder if it does not exist).
2. Settings → Dashboards → Resources → Add Resource  
   - URL: `/local/gas-tank-card.js`  
   - Type: **JavaScript Module**
3. Hard-refresh browser.

## Verify

In the browser console:

```js
customElements.get("gas-tank-card")
window.customCards.filter(c => c.type === "gas-tank-card")
```

Both should return something (not `undefined` / empty).
