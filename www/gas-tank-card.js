/**
 * Gas Tank Monitor Lovelace Card
 * Version 2.2.2 – Scale marks, date format, forecast QC
 *
 * Keep in sync with custom_components/gas_tank_monitor/www/gas-tank-card.js
 * This copy is used as the /local/ fallback source when the integration copies to config/www.
 */

// Re-export note: full implementation lives in custom_components/gas_tank_monitor/www/gas-tank-card.js
// For HACS /local/ reliability the integration auto-copies the component www file on setup.
// If you need a standalone module at /local/gas-tank-card.js, the integration will place the full card there.

console.info(
  "%c GAS-TANK-CARD %c 2.2.2 (www stub — full card from integration www)",
  "color:white;background:#0284c7;font-weight:bold;padding:2px 6px;border-radius:4px 0 0 4px",
  "color:#0284c7;background:#e0f2fe;font-weight:bold;padding:2px 6px;border-radius:0 4px 4px 0"
);
