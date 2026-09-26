/**
 * Gas Tank Monitor Lovelace Card
 * Clean light-theme design optimized for Caribbean 100 lb LPG cylinders
 * Version 1.0.0
 */

class GasTankCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("gas-tank-card-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:gas-tank-card",
      entity: "",
      tank_size: "100lb",
      show_burn_rate: true,
      show_forecast: true,
      show_status: true,
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity (level sensor)");
    }
    this.config = {
      show_burn_rate: true,
      show_forecast: true,
      show_status: true,
      tank_size: "100lb",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  connectedCallback() {
    this._render();
  }

  _render() {
    if (this.lastChild) return;

    const style = document.createElement("style");
    style.textContent = `
      :host {
        --gt-bg: #f8fafc;
        --gt-card-bg: #ffffff;
        --gt-text: #1e293b;
        --gt-text-secondary: #64748b;
        --gt-accent: #0ea5e9;
        --gt-accent-light: #e0f2fe;
        --gt-success: #10b981;
        --gt-warning: #f59e0b;
        --gt-danger: #ef4444;
        --gt-border: #e2e8f0;
        --gt-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05);
      }

      .card {
        background: var(--gt-card-bg);
        border-radius: 16px;
        box-shadow: var(--gt-shadow);
        border: 1px solid var(--gt-border);
        padding: 20px;
        font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
        color: var(--gt-text);
        max-width: 420px;
      }

      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }

      .title {
        font-size: 1.15rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .title ha-icon {
        color: var(--gt-accent);
      }

      .status-pill {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }

      .status-optimal { background: #d1fae5; color: #065f46; }
      .status-low     { background: #fef3c7; color: #92400e; }
      .status-critical{ background: #fee2e2; color: #991b1b; }
      .status-unknown { background: #f1f5f9; color: #64748b; }

      .gauge-container {
        position: relative;
        height: 180px;
        background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 16px;
        border: 1px solid #bae6fd;
      }

      .tank-outline {
        position: absolute;
        inset: 12px;
        border: 3px solid #7dd3fc;
        border-radius: 10px;
        background: rgba(255,255,255,0.5);
      }

      .liquid {
        position: absolute;
        bottom: 12px;
        left: 12px;
        right: 12px;
        background: linear-gradient(180deg, #38bdf8 0%, #0ea5e9 100%);
        border-radius: 0 0 7px 7px;
        transition: height 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: inset 0 2px 8px rgba(14, 165, 233, 0.3);
      }

      .liquid::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 8px;
        background: linear-gradient(180deg, rgba(255,255,255,0.4), transparent);
      }

      .level-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        z-index: 2;
      }

      .percent {
        font-size: 2.75rem;
        font-weight: 700;
        color: #0c4a6e;
        line-height: 1;
      }

      .percent-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0369a1;
        letter-spacing: 0.05em;
      }

      .volume {
        font-size: 0.9rem;
        color: #0c4a6e;
        margin-top: 4px;
        font-weight: 500;
      }

      .info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 12px;
      }

      .info-item {
        background: #f8fafc;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid var(--gt-border);
      }

      .info-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--gt-text-secondary);
        margin-bottom: 4px;
      }

      .info-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--gt-text);
      }

      .info-value small {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--gt-text-secondary);
      }

      .forecast {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        border-radius: 10px;
        padding: 14px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #bae6fd;
      }

      .forecast-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #0369a1;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .forecast-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0c4a6e;
      }

      .footer {
        margin-top: 12px;
        font-size: 0.75rem;
        color: var(--gt-text-secondary);
        text-align: center;
      }
    `;

    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="header">
        <div class="title">
          <ha-icon icon="mdi:propane-tank"></ha-icon>
          <span class="name">Gas Tank</span>
        </div>
        <div class="status-pill status-unknown">—</div>
      </div>

      <div class="gauge-container">
        <div class="tank-outline"></div>
        <div class="liquid" style="height: 0%"></div>
        <div class="level-text">
          <div class="percent">—</div>
          <div class="percent-label">FULL</div>
          <div class="volume">— / — Gal</div>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item burn-rate">
          <div class="info-label">Burn Rate</div>
          <div class="info-value">— <small>Gal/Day</small></div>
        </div>
        <div class="info-item days-full">
          <div class="info-label">Days Since Full</div>
          <div class="info-value">—</div>
        </div>
      </div>

      <div class="forecast">
        <div class="forecast-label">
          <ha-icon icon="mdi:calendar-clock"></ha-icon>
          Depletion & Refill Forecast
        </div>
        <div class="forecast-value">— Days</div>
      </div>
    `;

    this.appendChild(style);
    this.appendChild(card);
    this._elements = {
      name: card.querySelector(".name"),
      status: card.querySelector(".status-pill"),
      liquid: card.querySelector(".liquid"),
      percent: card.querySelector(".percent"),
      volume: card.querySelector(".volume"),
      burnRate: card.querySelector(".burn-rate .info-value"),
      daysFull: card.querySelector(".days-full .info-value"),
      forecast: card.querySelector(".forecast-value"),
      burnRateSection: card.querySelector(".burn-rate"),
      forecastSection: card.querySelector(".forecast"),
    };
  }

  _update() {
    if (!this._hass || !this.config || !this._elements) return;

    const stateObj = this._hass.states[this.config.entity];
    if (!stateObj) {
      this._elements.percent.textContent = "N/A";
      return;
    }

    const level = parseFloat(stateObj.state);
    const attrs = stateObj.attributes || {};

    // Name
    this._elements.name.textContent =
      this.config.name || stateObj.attributes.friendly_name || "Gas Tank";

    // Status
    const status = attrs.status || "unknown";
    this._elements.status.textContent = status;
    this._elements.status.className = `status-pill status-${status.toLowerCase()}`;

    // Gauge
    const pct = isNaN(level) ? 0 : Math.min(100, Math.max(0, level));
    this._elements.liquid.style.height = `calc(${pct}% - 0px)`;
    // Adjust liquid height properly inside the outline
    const maxHeight = 156; // approximate inner height
    this._elements.liquid.style.height = `${(pct / 100) * maxHeight}px`;

    this._elements.percent.textContent = isNaN(level) ? "—" : `${Math.round(level)}%`;

    const capacity = attrs.capacity_gallons || 23.6;
    const volume = attrs.volume_remaining ?? (capacity * pct / 100);
    this._elements.volume.textContent = `${volume.toFixed(1)} / ${capacity} Gal`;

    // Burn rate
    if (this.config.show_burn_rate !== false) {
      this._elements.burnRateSection.style.display = "";
      const rate = attrs.burn_rate;
      this._elements.burnRate.innerHTML = rate != null
        ? `${rate} <small>Gal/Day</small>`
        : "— <small>Gal/Day</small>";
    } else {
      this._elements.burnRateSection.style.display = "none";
    }

    // Days since full
    const daysFull = attrs.days_since_full;
    this._elements.daysFull.textContent = daysFull != null ? daysFull : "—";

    // Forecast
    if (this.config.show_forecast !== false) {
      this._elements.forecastSection.style.display = "";
      const days = attrs.days_remaining;
      this._elements.forecast.textContent = days != null ? `~${Math.round(days)} Days` : "— Days";
    } else {
      this._elements.forecastSection.style.display = "none";
    }
  }

  getCardSize() {
    return 4;
  }
}

class GasTankCardEditor extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || this.lastChild) return;

    const style = document.createElement("style");
    style.textContent = `
      .editor { padding: 16px; font-family: system-ui; }
      label { display: block; margin: 12px 0 4px; font-weight: 500; }
      input, select { width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; }
      .row { display: flex; gap: 12px; align-items: center; margin-top: 12px; }
    `;

    const div = document.createElement("div");
    div.className = "editor";
    div.innerHTML = `
      <label>Entity (Level Sensor)</label>
      <input type="text" id="entity" placeholder="sensor.gas_tank_level" value="${this.config.entity || ""}">

      <label>Card Name (optional)</label>
      <input type="text" id="name" placeholder="Propane Main" value="${this.config.name || ""}">

      <label>Tank Size</label>
      <select id="tank_size">
        <option value="20lb">20 lb</option>
        <option value="30lb">30 lb</option>
        <option value="40lb">40 lb</option>
        <option value="100lb">100 lb (Caribbean)</option>
        <option value="custom">Custom</option>
      </select>

      <div class="row">
        <input type="checkbox" id="show_burn_rate" ${this.config.show_burn_rate !== false ? "checked" : ""}>
        <label for="show_burn_rate" style="margin:0">Show Burn Rate</label>
      </div>
      <div class="row">
        <input type="checkbox" id="show_forecast" ${this.config.show_forecast !== false ? "checked" : ""}>
        <label for="show_forecast" style="margin:0">Show Forecast</label>
      </div>
    `;

    this.appendChild(style);
    this.appendChild(div);

    const entityInput = div.querySelector("#entity");
    const nameInput = div.querySelector("#name");
    const tankSelect = div.querySelector("#tank_size");
    const burnCheck = div.querySelector("#show_burn_rate");
    const forecastCheck = div.querySelector("#show_forecast");

    tankSelect.value = this.config.tank_size || "100lb";

    const update = () => {
      this.config = {
        ...this.config,
        entity: entityInput.value,
        name: nameInput.value || undefined,
        tank_size: tankSelect.value,
        show_burn_rate: burnCheck.checked,
        show_forecast: forecastCheck.checked,
      };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this.config } }));
    };

    entityInput.addEventListener("change", update);
    nameInput.addEventListener("change", update);
    tankSelect.addEventListener("change", update);
    burnCheck.addEventListener("change", update);
    forecastCheck.addEventListener("change", update);
  }
}

customElements.define("gas-tank-card", GasTankCard);
customElements.define("gas-tank-card-editor", GasTankCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "gas-tank-card",
  name: "Gas Tank Card",
  description: "Modern light-theme card for LPG / Propane tank monitoring (Caribbean 100 lb optimized)",
  preview: true,
});
