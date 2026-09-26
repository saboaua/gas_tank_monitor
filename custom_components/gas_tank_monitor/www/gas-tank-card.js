/**
 * Gas Tank Monitor Lovelace Card
 * Clean modern card for LPG / Propane tanks (Caribbean 100 lb optimized)
 * Version 1.1.0
 */

class GasTankCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("gas-tank-card-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:gas-tank-card",
      entity: "sensor.gas_tank_monitor_level",
      name: "Propane Tank",
      show_burn_rate: true,
      show_forecast: true,
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this.config = {
      show_burn_rate: true,
      show_forecast: true,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    if (this._rendered) {
      this._update();
    } else {
      this._render();
      this._rendered = true;
      this._update();
    }
  }

  _render() {
    this.innerHTML = `
      <ha-card>
        <style>
          ha-card {
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            font-family: "Segoe UI", system-ui, sans-serif;
          }
          .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px 8px;
          }
          .title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.15rem;
            font-weight: 600;
            color: #1e293b;
          }
          .title ha-icon {
            color: #0ea5e9;
            --mdc-icon-size: 24px;
          }
          .status {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 999px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }
          .status-optimal { background: #d1fae5; color: #065f46; }
          .status-low { background: #fef3c7; color: #92400e; }
          .status-critical { background: #fee2e2; color: #991b1b; }
          .status-unknown { background: #f1f5f9; color: #64748b; }

          .gauge-wrap {
            margin: 0 16px 16px;
            height: 170px;
            background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 14px;
            border: 1px solid #bae6fd;
            position: relative;
            overflow: hidden;
          }
          .tank-border {
            position: absolute;
            inset: 10px;
            border: 3px solid #7dd3fc;
            border-radius: 10px;
            background: rgba(255,255,255,0.45);
          }
          .liquid {
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            background: linear-gradient(180deg, #38bdf8, #0284c7);
            border-radius: 0 0 7px 7px;
            transition: height 0.9s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: inset 0 4px 12px rgba(2, 132, 199, 0.25);
          }
          .liquid::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 10px;
            background: linear-gradient(180deg, rgba(255,255,255,0.45), transparent);
          }
          .level-center {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 2;
          }
          .percent {
            font-size: 2.8rem;
            font-weight: 700;
            color: #0c4a6e;
            line-height: 1;
          }
          .full-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: #0369a1;
            letter-spacing: 0.06em;
            margin-top: 2px;
          }
          .volume {
            font-size: 0.9rem;
            color: #0c4a6e;
            margin-top: 4px;
            font-weight: 500;
          }

          .info-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 0 16px 12px;
          }
          .info-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px;
          }
          .info-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #64748b;
            margin-bottom: 4px;
          }
          .info-value {
            font-size: 1.15rem;
            font-weight: 600;
            color: #1e293b;
          }
          .info-value span {
            font-size: 0.8rem;
            font-weight: 500;
            color: #64748b;
          }

          .forecast {
            margin: 0 16px 16px;
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            border: 1px solid #bae6fd;
            border-radius: 12px;
            padding: 14px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .forecast-left {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            color: #0369a1;
          }
          .forecast-left ha-icon {
            --mdc-icon-size: 20px;
          }
          .forecast-days {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0c4a6e;
          }
        </style>

        <div class="header">
          <div class="title">
            <ha-icon icon="mdi:propane-tank"></ha-icon>
            <span class="name">Gas Tank</span>
          </div>
          <div class="status status-unknown">—</div>
        </div>

        <div class="gauge-wrap">
          <div class="tank-border"></div>
          <div class="liquid" style="height: 0px;"></div>
          <div class="level-center">
            <div class="percent">—</div>
            <div class="full-label">FULL</div>
            <div class="volume">— / — Gal</div>
          </div>
        </div>

        <div class="info-row">
          <div class="info-box burn">
            <div class="info-label">Burn Rate</div>
            <div class="info-value">— <span>Gal/Day</span></div>
          </div>
          <div class="info-box days">
            <div class="info-label">Days Since Full</div>
            <div class="info-value">—</div>
          </div>
        </div>

        <div class="forecast">
          <div class="forecast-left">
            <ha-icon icon="mdi:calendar-clock"></ha-icon>
            Depletion & Refill Forecast
          </div>
          <div class="forecast-days">— Days</div>
        </div>
      </ha-card>
    `;

    this._els = {
      name: this.querySelector(".name"),
      status: this.querySelector(".status"),
      liquid: this.querySelector(".liquid"),
      percent: this.querySelector(".percent"),
      volume: this.querySelector(".volume"),
      burn: this.querySelector(".burn .info-value"),
      days: this.querySelector(".days .info-value"),
      forecast: this.querySelector(".forecast-days"),
      burnBox: this.querySelector(".burn"),
      forecastBox: this.querySelector(".forecast"),
    };
  }

  _update() {
    if (!this._hass || !this.config || !this._els) return;

    const state = this._hass.states[this.config.entity];
    if (!state) {
      this._els.percent.textContent = "N/A";
      return;
    }

    const level = parseFloat(state.state);
    const attrs = state.attributes || {};
    const pct = isNaN(level) ? 0 : Math.min(100, Math.max(0, level));

    this._els.name.textContent =
      this.config.name || attrs.friendly_name || "Gas Tank";

    const status = (attrs.status || "unknown").toLowerCase();
    this._els.status.textContent = attrs.status || "—";
    this._els.status.className = `status status-${status}`;

    const maxH = 146;
    this._els.liquid.style.height = (pct / 100) * maxH + "px";

    this._els.percent.textContent = isNaN(level) ? "—" : Math.round(level) + "%";
    const capacity = attrs.capacity_gallons || 23.6;
    const vol = attrs.volume_remaining != null ? attrs.volume_remaining : (capacity * pct / 100);
    this._els.volume.textContent = Number(vol).toFixed(1) + " / " + capacity + " Gal";

    if (this.config.show_burn_rate !== false) {
      this._els.burnBox.style.display = "";
      const rate = attrs.burn_rate;
      this._els.burn.innerHTML = rate != null
        ? rate + " <span>Gal/Day</span>"
        : "— <span>Gal/Day</span>";
    } else {
      this._els.burnBox.style.display = "none";
    }

    this._els.days.textContent = attrs.days_since_full != null ? attrs.days_since_full : "—";

    if (this.config.show_forecast !== false) {
      this._els.forecastBox.style.display = "";
      const days = attrs.days_remaining;
      this._els.forecast.textContent = days != null ? "~" + Math.round(days) + " Days" : "— Days";
    } else {
      this._els.forecastBox.style.display = "none";
    }
  }

  getCardSize() {
    return 5;
  }
}

class GasTankCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._render();
      this._rendered = true;
    }
  }

  _render() {
    this.innerHTML = `
      <div style="padding:16px;font-family:system-ui">
        <div style="margin-bottom:12px">
          <label style="display:block;font-weight:500;margin-bottom:4px">Entity (Level Sensor)</label>
          <input id="entity" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:6px"
            value="${this._config.entity || ""}" placeholder="sensor.gas_tank_monitor_level">
        </div>
        <div style="margin-bottom:12px">
          <label style="display:block;font-weight:500;margin-bottom:4px">Name (optional)</label>
          <input id="name" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:6px"
            value="${this._config.name || ""}" placeholder="Propane Main">
        </div>
        <div style="display:flex;gap:16px;margin-top:8px">
          <label style="display:flex;align-items:center;gap:6px">
            <input id="burn" type="checkbox" ${this._config.show_burn_rate !== false ? "checked" : ""}>
            Show Burn Rate
          </label>
          <label style="display:flex;align-items:center;gap:6px">
            <input id="forecast" type="checkbox" ${this._config.show_forecast !== false ? "checked" : ""}>
            Show Forecast
          </label>
        </div>
      </div>
    `;

    const update = () => {
      this._config = {
        ...this._config,
        entity: this.querySelector("#entity").value,
        name: this.querySelector("#name").value || undefined,
        show_burn_rate: this.querySelector("#burn").checked,
        show_forecast: this.querySelector("#forecast").checked,
      };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
    };

    this.querySelector("#entity").addEventListener("change", update);
    this.querySelector("#name").addEventListener("change", update);
    this.querySelector("#burn").addEventListener("change", update);
    this.querySelector("#forecast").addEventListener("change", update);
  }
}

customElements.define("gas-tank-card", GasTankCard);
customElements.define("gas-tank-card-editor", GasTankCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "gas-tank-card",
  name: "Gas Tank Card",
  description: "Modern tank level card with gauge, burn rate and forecast (Caribbean 100 lb optimized)",
  preview: true
});

console.info(
  "%c GAS-TANK-CARD %c 1.1.0 ",
  "color:white;background:#0ea5e9;font-weight:bold;padding:2px 6px;border-radius:4px 0 0 4px",
  "color:#0ea5e9;background:#e0f2fe;font-weight:bold;padding:2px 6px;border-radius:0 4px 4px 0"
);
