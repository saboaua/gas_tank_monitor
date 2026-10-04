/**
 * Gas Tank Monitor Lovelace Card
 * Version 2.2.11 - Default Lovelace card border + dark theme
 */

class GasTankCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("gas-tank-card-editor");
  }

  static getStubConfig() {
    // HA card picker: do NOT include "type" (added by the UI)
    return {
      entity: "sensor.gas_tank_monitor_level",
      name: "Propane Tank",
      show_burn_rate: true,
      show_forecast: true,
    };
  }

  setConfig(config) {
    try {
      this.config = {
        show_burn_rate: true,
        show_forecast: true,
        entity: "",
        name: "Propane Tank",
        ...(config || {}),
      };
      if (this._hass) this._update();
    } catch (e) {
      console.warn("gas-tank-card setConfig", e);
    }
  }

  set hass(hass) {
    try {
      this._hass = hass;
      if (!this._rendered) {
        this._render();
        this._rendered = true;
      }
      this._update();
    } catch (e) {
      console.warn("gas-tank-card hass", e);
    }
  }

  _render() {
    try {
    this.innerHTML = `
      <ha-card class="gtc">
        <style>
          .gtc {
            /* Match default Lovelace ha-card chrome (border/radius/shadow from theme) */
            --gtc-bg: var(--ha-card-background, var(--card-background-color, #ffffff));
            --gtc-text: var(--primary-text-color, #0f172a);
            --gtc-muted: var(--secondary-text-color, #64748b);
            --gtc-border: var(--divider-color, #e2e8f0);
            --gtc-accent: #0ea5e9;
            --gtc-accent-deep: #0284c7;
            --gtc-panel: #f0f9ff;
            --gtc-panel-border: #e0f2fe;
            --gtc-tank-bg: #ffffff;
            --gtc-tank-border: #7dd3fc;
            --gtc-metric-bg: #f8fafc;
            --gtc-forecast-bg: #e0f2fe;
            --gtc-forecast-border: #bae6fd;
            --gtc-forecast-label: #0369a1;
            --gtc-chip-bg: #f1f5f9;
            --gtc-footer-hover: #f1f5f9;
            background: var(--gtc-bg);
            /* Use HA defaults — same as Sliding Doors / standard cards */
            border-radius: var(--ha-card-border-radius, 12px);
            border-width: var(--ha-card-border-width, 1px);
            border-style: solid;
            border-color: var(--ha-card-border-color, var(--divider-color, rgba(0,0,0,0.12)));
            box-shadow: var(--ha-card-box-shadow, var(--ha-card-shadow, none));
            font-family: system-ui, -apple-system, sans-serif;
            overflow: hidden;
            position: relative;
            padding: 16px;
            color: var(--gtc-text);
          }
          .gtc * { box-sizing: border-box; }
          .gtc-header { display:flex; align-items:center; justify-content:space-between; padding-bottom:14px; border-bottom:1px solid var(--gtc-border); }
          .gtc-title-row { display:flex; align-items:center; gap:10px; }
          .gtc-icon { width:36px; height:36px; border-radius:12px; background:var(--gtc-panel); border:1px solid var(--gtc-forecast-border); display:flex; align-items:center; justify-content:center; color:var(--gtc-accent-deep); }
          .gtc-icon ha-icon { --mdc-icon-size:20px; }
          .gtc-name { font-size:1rem; font-weight:700; color:var(--gtc-text); display:flex; align-items:center; gap:6px; line-height:1.2; }
          .gtc-battery { font-size:10px; font-weight:600; color:#047857; background:#ecfdf5; border:1px solid #a7f3d0; padding:2px 6px; border-radius:999px; display:none; align-items:center; gap:4px; }
          .gtc-battery .dot { width:6px; height:6px; border-radius:50%; background:#10b981; }
          .gtc-sub { font-size:11px; color:var(--gtc-muted); font-weight:500; margin-top:2px; }
          .gtc-status { display:flex; align-items:center; gap:6px; padding:4px 12px; border-radius:999px; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.04em; }
          .gtc-status.critical { background:#fee2e2; border:1px solid #fecaca; color:#dc2626; }
          .gtc-status.low { background:#ffedd5; border:1px solid #fed7aa; color:#c2410c; }
          .gtc-status.optimal { background:#d1fae5; border:1px solid #a7f3d0; color:#047857; }
          .gtc-status.unknown { background:var(--gtc-chip-bg); border:1px solid var(--gtc-border); color:var(--gtc-muted); }
          .gtc-status .pulse { width:8px; height:8px; border-radius:50%; background:currentColor; }
          .gtc-gauge { margin-top:14px; border-radius:16px; background:var(--gtc-panel); border:2px solid var(--gtc-panel-border); padding:10px; }
          .gtc-tank { position:relative; height:176px; border-radius:12px; border:1px solid var(--gtc-tank-border); background:var(--gtc-tank-bg); overflow:hidden; }
          .gtc-scale { position:absolute; top:0; right:0; bottom:0; width:78px; z-index:6; pointer-events:none; }
          .gtc-scale-item { position:absolute; right:8px; display:flex; flex-direction:row; align-items:center; justify-content:flex-end; gap:4px; font-size:9px; font-family:system-ui,sans-serif; font-weight:500; color:var(--gtc-muted); white-space:nowrap; line-height:1; transform:translateY(-50%); }
          .gtc-scale-item .tick { display:block; height:2px; background:var(--gtc-border); border-radius:1px; flex-shrink:0; order:-1; }
          .gtc-scale-item.s80 { top:20%; } .gtc-scale-item.s80 .tick { width:10px; }
          .gtc-scale-item.s50 { top:50%; } .gtc-scale-item.s50 .tick { width:6px; }
          .gtc-scale-item.s20 { top:80%; color:#d97706; font-weight:600; } .gtc-scale-item.s20 .tick { width:10px; background:#f59e0b; }
          .gtc-scale-item.s10 { top:90%; color:#f87171; font-weight:700; } .gtc-scale-item.s10 .tick { width:12px; background:#ef4444; }
          .gtc-center { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:10; text-align:center; padding-bottom:24px; }
          .gtc-percent { font-size:3rem; font-weight:900; color:var(--gtc-text); line-height:1; letter-spacing:-.02em; }
          .gtc-full { font-size:11px; font-weight:700; color:var(--gtc-accent-deep); letter-spacing:.08em; margin-top:2px; }
          .gtc-vol { display:inline-flex; align-items:center; gap:6px; margin-top:6px; padding:2px 10px; border-radius:999px; background:var(--gtc-chip-bg); border:1px solid var(--gtc-border); font-size:11px; font-weight:600; color:var(--gtc-muted); }
          .gtc-vol .dot { width:6px; height:6px; border-radius:50%; background:#ef4444; }
          .gtc-liquid { position:absolute; bottom:0; left:0; right:0; background:linear-gradient(to top,#0284c7,#0ea5e9,#38bdf8); transition:height .9s cubic-bezier(.4,0,.2,1); z-index:2; }
          .gtc-liquid::before { content:""; position:absolute; top:-2px; left:0; right:0; height:4px; background:#38bdf8; box-shadow:0 0 8px rgba(14,165,233,.6); }
          .gtc-sensors { display:flex; justify-content:space-between; padding:8px 4px 0; font-size:11px; color:var(--gtc-muted); font-weight:500; }
          .gtc-sensors span { display:none; align-items:center; gap:4px; }
          .gtc-sensors ha-icon { --mdc-icon-size:14px; color:var(--gtc-muted); }
          .gtc-metrics { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }
          .gtc-metric { background:var(--gtc-metric-bg); border:1px solid var(--gtc-border); border-radius:16px; padding:12px; }
          .gtc-metric-label { display:flex; justify-content:space-between; align-items:center; font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--gtc-muted); }
          .gtc-metric-label ha-icon { --mdc-icon-size:14px; }
          .gtc-metric-value { margin-top:8px; font-size:1.35rem; font-weight:900; color:var(--gtc-text); letter-spacing:-.02em; }
          .gtc-metric-value small { font-size:11px; font-weight:600; color:var(--gtc-muted); margin-left:2px; }
          .gtc-metric-sub { margin-top:4px; font-size:10px; color:var(--gtc-muted); font-weight:500; }
          .gtc-forecast { margin-top:12px; background:var(--gtc-forecast-bg); border:1px solid var(--gtc-forecast-border); border-radius:16px; padding:12px; }
          .gtc-forecast-row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
          .gtc-forecast-left { display:flex; align-items:center; gap:10px; }
          .gtc-forecast-icon { width:36px; height:36px; border-radius:12px; background:var(--gtc-tank-bg); border:1px solid var(--gtc-forecast-border); display:flex; align-items:center; justify-content:center; color:var(--gtc-accent-deep); }
          .gtc-forecast-icon ha-icon { --mdc-icon-size:20px; }
          .gtc-forecast-label { font-size:11px; font-weight:600; color:var(--gtc-forecast-label); }
          .gtc-forecast-value { font-size:14px; font-weight:600; color:var(--gtc-text); }
          .gtc-forecast-value strong { color:#f87171; font-weight:800; font-size:15px; }
          .gtc-bar { margin-top:10px; height:6px; background:var(--gtc-forecast-border); border-radius:999px; overflow:hidden; }
          .gtc-bar-fill { height:100%; border-radius:999px; background:linear-gradient(to right,#ef4444,#f59e0b); transition:width .8s ease; }
          .gtc-footer { margin-top:12px; padding-top:10px; border-top:1px solid var(--gtc-border); display:flex; justify-content:space-between; font-size:12px; color:var(--gtc-muted); }
          .gtc-footer button { background:none; border:none; display:flex; align-items:center; gap:6px; color:var(--gtc-muted); font-weight:500; cursor:pointer; padding:4px 6px; border-radius:8px; }
          .gtc-footer button:active { background:var(--gtc-footer-hover); }
          .gtc-footer ha-icon { --mdc-icon-size:14px; color:var(--gtc-muted); }

          /* Dark theme — HA dark mode + OS dark */
          @media (prefers-color-scheme: dark) {
            .gtc {
              --gtc-panel: #0c1929;
              --gtc-panel-border: #1e3a5f;
              --gtc-tank-bg: #0b1220;
              --gtc-tank-border: #1d4ed8;
              --gtc-metric-bg: #111827;
              --gtc-forecast-bg: #0c1929;
              --gtc-forecast-border: #1e3a5f;
              --gtc-forecast-label: #7dd3fc;
              --gtc-chip-bg: #1e293b;
              --gtc-footer-hover: #1e293b;
              --gtc-shadow: 0 12px 36px -6px rgba(0,0,0,.45);
              --gtc-accent-deep: #38bdf8;
            }
            .gtc-status.critical { background:#450a0a; border-color:#7f1d1d; color:#fca5a5; }
            .gtc-status.low { background:#431407; border-color:#9a3412; color:#fdba74; }
            .gtc-status.optimal { background:#052e16; border-color:#166534; color:#6ee7b7; }
            .gtc-battery { color:#6ee7b7; background:#052e16; border-color:#166534; }
          }
          /* HA theme forces dark even if OS is light */
          html[data-theme="dark"] .gtc,
          html.dark .gtc,
          body.dark-mode .gtc,
          .gtc.gtc-dark {
            --gtc-panel: #0c1929;
            --gtc-panel-border: #1e3a5f;
            --gtc-tank-bg: #0b1220;
            --gtc-tank-border: #1d4ed8;
            --gtc-metric-bg: #111827;
            --gtc-forecast-bg: #0c1929;
            --gtc-forecast-border: #1e3a5f;
            --gtc-forecast-label: #7dd3fc;
            --gtc-chip-bg: #1e293b;
            --gtc-footer-hover: #1e293b;
            --gtc-shadow: 0 12px 36px -6px rgba(0,0,0,.45);
            --gtc-accent-deep: #38bdf8;
          }
          html[data-theme="dark"] .gtc-status.critical,
          .gtc.gtc-dark .gtc-status.critical { background:#450a0a; border-color:#7f1d1d; color:#fca5a5; }
          html[data-theme="dark"] .gtc-status.low,
          .gtc.gtc-dark .gtc-status.low { background:#431407; border-color:#9a3412; color:#fdba74; }
          html[data-theme="dark"] .gtc-status.optimal,
          .gtc.gtc-dark .gtc-status.optimal { background:#052e16; border-color:#166534; color:#6ee7b7; }
          html[data-theme="dark"] .gtc-battery,
          .gtc.gtc-dark .gtc-battery { color:#6ee7b7; background:#052e16; border-color:#166534; }
        </style>
        <div class="gtc-header">
          <div class="gtc-title-row">
            <div class="gtc-icon"><ha-icon icon="mdi:propane-tank"></ha-icon></div>
            <div>
              <div class="gtc-name"><span class="name">Propane Tank</span><span class="gtc-battery"><span class="dot"></span><span class="batt-val">—</span></span></div>
              <div class="gtc-sub"><span class="conn">Sensor</span><span> • </span><span class="ago">—</span></div>
            </div>
          </div>
          <div class="gtc-status unknown"><span class="pulse"></span><span class="status-text">—</span></div>
        </div>
        <div class="gtc-gauge">
          <div class="gtc-tank">
            <div class="gtc-scale">
              <div class="gtc-scale-item s80"><span class="tick"></span><span>80% Max</span></div>
              <div class="gtc-scale-item s50"><span class="tick"></span><span>50%</span></div>
              <div class="gtc-scale-item s20"><span class="tick"></span><span>20% Low</span></div>
              <div class="gtc-scale-item s10"><span class="tick"></span><span>10% Alert</span></div>
            </div>
            <div class="gtc-center">
              <div class="gtc-percent">—</div><div class="gtc-full">FULL</div>
              <div class="gtc-vol"><span class="dot"></span><span class="vol-text">— / — Gal</span></div>
            </div>
            <div class="gtc-liquid" style="height:0%"></div>
          </div>
          <div class="gtc-sensors">
            <span class="temp-row"><ha-icon icon="mdi:thermometer"></ha-icon><span class="temp-val">—</span></span>
            <span class="press-row"><ha-icon icon="mdi:gauge"></ha-icon><span class="press-val">—</span></span>
          </div>
        </div>
        <div class="gtc-metrics">
          <div class="gtc-metric burn">
            <div class="gtc-metric-label"><span>Burn Rate</span><ha-icon icon="mdi:fire" style="color:#f59e0b"></ha-icon></div>
            <div class="gtc-metric-value">— <small>Gal/Day</small></div>
            <div class="gtc-metric-sub">—</div>
          </div>
          <div class="gtc-metric days">
            <div class="gtc-metric-label"><span>Days Since Full</span><ha-icon icon="mdi:clock-outline" style="color:#0284c7"></ha-icon></div>
            <div class="gtc-metric-value">— <small>Days</small></div>
            <div class="gtc-metric-sub">—</div>
          </div>
        </div>
        <div class="gtc-forecast">
          <div class="gtc-forecast-row">
            <div class="gtc-forecast-left">
              <div class="gtc-forecast-icon"><ha-icon icon="mdi:calendar-clock"></ha-icon></div>
              <div>
                <div class="gtc-forecast-label">Depletion & Refill Forecast</div>
                <div class="gtc-forecast-value">Depleted in <strong class="days-left">—</strong></div>
              </div>
            </div>
          </div>
          <div class="gtc-bar"><div class="gtc-bar-fill" style="width:0%"></div></div>
        </div>
        <div class="gtc-footer">
          <button type="button" class="history-btn"><ha-icon icon="mdi:history"></ha-icon>Tank History</button>
          <button type="button" class="cal-btn"><ha-icon icon="mdi:cog"></ha-icon>Calibrate</button>
        </div>
      </ha-card>
    `;
    this._els = {
      name: this.querySelector(".name"), battery: this.querySelector(".gtc-battery"), battVal: this.querySelector(".batt-val"),
      conn: this.querySelector(".conn"), ago: this.querySelector(".ago"), status: this.querySelector(".gtc-status"),
      statusText: this.querySelector(".status-text"), percent: this.querySelector(".gtc-percent"), vol: this.querySelector(".vol-text"),
      liquid: this.querySelector(".gtc-liquid"), tempRow: this.querySelector(".temp-row"), tempVal: this.querySelector(".temp-val"),
      pressRow: this.querySelector(".press-row"), pressVal: this.querySelector(".press-val"),
      burnVal: this.querySelector(".burn .gtc-metric-value"), burnSub: this.querySelector(".burn .gtc-metric-sub"),
      daysVal: this.querySelector(".days .gtc-metric-value"), daysSub: this.querySelector(".days .gtc-metric-sub"),
      daysLeft: this.querySelector(".days-left"), barFill: this.querySelector(".gtc-bar-fill"),
      historyBtn: this.querySelector(".history-btn"), calBtn: this.querySelector(".cal-btn"),
    };
    if (this._els.historyBtn) this._els.historyBtn.addEventListener("click", () => this._onHistory());
    if (this._els.calBtn) this._els.calBtn.addEventListener("click", () => this._onCalibrate());
    } catch (e) {
      console.warn("gas-tank-card _render", e);
    }
  }

  _fireEvent(node, type, detail) {
    const event = new Event(type, { bubbles: true, cancelable: false, composed: true });
    event.detail = detail || {};
    node.dispatchEvent(event);
    return event;
  }

  _navigate(path) {
    if (!path) return;
    try {
      history.pushState(null, "", path);
      this._fireEvent(window, "location-changed", { replace: false });
    } catch (e) {}
    setTimeout(() => {
      const cur = window.location.pathname + window.location.search + window.location.hash;
      if (cur !== path && !window.location.pathname.includes(path.split("/").pop())) {
        window.location.assign(path);
      }
    }, 250);
  }

  _onHistory() {
    if (!this.config.entity) return;
    this._fireEvent(this, "hass-more-info", { entityId: this.config.entity });
  }

  _onCalibrate() {
    // Always open the integration page (options / calibrate live there)
    this._navigate("/config/integrations/integration/gas_tank_monitor");
  }

  _update() {
    try {
    if (!this._hass || !this.config || !this._els) return;
    // Sync dark class with HA theme / OS (styles also use media + data-theme)
    const card = this.querySelector(".gtc");
    if (card) {
      let dark = false;
      try {
        const bg = getComputedStyle(document.body).getPropertyValue("--primary-background-color").trim()
          || getComputedStyle(document.body).getPropertyValue("--card-background-color").trim();
        if (bg.startsWith("#") && bg.length >= 7) {
          const r = parseInt(bg.slice(1, 3), 16), g = parseInt(bg.slice(3, 5), 16), b = parseInt(bg.slice(5, 7), 16);
          dark = (r * 299 + g * 587 + b * 114) / 1000 < 128;
        } else if (bg.startsWith("rgb")) {
          const m = bg.match(/(\d+)/g);
          if (m && m.length >= 3) {
            const r = +m[0], g = +m[1], b = +m[2];
            dark = (r * 299 + g * 587 + b * 114) / 1000 < 128;
          }
        }
        if (!dark) dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        if (!dark) {
          const html = document.documentElement;
          dark = html.classList.contains("dark") || html.getAttribute("data-theme") === "dark"
            || (this._hass.themes && this._hass.themes.darkMode === true);
        }
      } catch (e) {}
      card.classList.toggle("gtc-dark", !!dark);
    }
    const entity = this.config.entity;
    const state = entity ? this._hass.states[entity] : null;
    const attrs = state ? (state.attributes || {}) : {};
    const level = state ? parseFloat(state.state) : NaN;
    const pct = isNaN(level) ? 0 : Math.min(100, Math.max(0, level));
    if (this._els.name) this._els.name.textContent = this.config.name || attrs.friendly_name || "Propane Tank";
    if (attrs.battery_level != null || attrs.battery != null) {
      const b = attrs.battery_level ?? attrs.battery;
      this._els.battery.style.display = "inline-flex";
      this._els.battVal.textContent = Math.round(b) + "%";
    } else { this._els.battery.style.display = "none"; }
    this._els.conn.textContent = attrs.connection || attrs.source || "Sensor";
    this._els.ago.textContent = state && state.last_updated ? this._timeAgo(state.last_updated) : "—";
    const status = (attrs.status || "unknown").toLowerCase();
    this._els.status.className = "gtc-status " + status;
    this._els.statusText.textContent = attrs.status || "—";
    this._els.percent.textContent = isNaN(level) ? "—" : Math.round(level) + "%";
    const capacity = attrs.capacity_gallons || 23.6;
    const vol = attrs.volume_remaining != null ? attrs.volume_remaining : (capacity * pct / 100);
    this._els.vol.textContent = Number(vol).toFixed(1) + " / " + capacity + " Gal";
    this._els.liquid.style.height = pct + "%";
    if (attrs.temperature != null || attrs.temp != null) {
      this._els.tempRow.style.display = "flex";
      const t = attrs.temperature ?? attrs.temp;
      this._els.tempVal.textContent = (typeof t === "number" ? t.toFixed(1) : t) + "° Tank Temp";
    } else { this._els.tempRow.style.display = "none"; }
    if (attrs.pressure != null) {
      this._els.pressRow.style.display = "flex";
      this._els.pressVal.textContent = Math.round(attrs.pressure) + " PSI Pressure";
    } else { this._els.pressRow.style.display = "none"; }
    let rate = attrs.burn_rate;
    const cap = attrs.capacity_gallons || 23.6;
    if (rate != null && Number(rate) > cap) rate = null;
    this._els.burnVal.innerHTML = rate != null ? Number(rate).toFixed(2) + " <small>Gal/Day</small>" : "— <small>Gal/Day</small>";
    if (attrs.burn_rate_change) {
      this._els.burnSub.textContent = attrs.burn_rate_change;
      this._els.burnSub.style.color = String(attrs.burn_rate_change).startsWith("+") ? "#d97706" : "#64748b";
    } else if (attrs.burn_rate_7d != null) {
      this._els.burnSub.textContent = "7d avg: " + attrs.burn_rate_7d + " Gal/Day";
      this._els.burnSub.style.color = "";
    } else { this._els.burnSub.textContent = "—"; this._els.burnSub.style.color = ""; }
    const daysFull = attrs.days_since_full;
    this._els.daysVal.innerHTML = daysFull != null ? daysFull + " <small>Days</small>" : "— <small>Days</small>";
    this._els.daysSub.textContent = this._formatLastFull(attrs);
    this._els.daysSub.title = attrs.last_full || "";
    const daysLeft = attrs.days_remaining;
    if (daysLeft == null) this._els.daysLeft.textContent = "—";
    else if (Number(daysLeft) <= 0) this._els.daysLeft.textContent = "Now — refill";
    else if (Number(daysLeft) < 1) this._els.daysLeft.textContent = "~" + Math.max(1, Math.round(Number(daysLeft) * 24)) + " hrs";
    else this._els.daysLeft.textContent = "~" + Number(daysLeft).toFixed(1) + " Days";
    if (this._els.barFill) this._els.barFill.style.width = pct + "%";
    } catch (e) {
      console.warn("gas-tank-card _update", e);
    }
  }

  _timeAgo(iso) {
    try {
      const d = new Date(iso);
      const sec = Math.floor((Date.now() - d.getTime()) / 1000);
      if (sec < 60) return sec + "s ago";
      if (sec < 3600) return Math.floor(sec / 60) + "m ago";
      if (sec < 86400) return Math.floor(sec / 3600) + "h ago";
      return Math.floor(sec / 86400) + "d ago";
    } catch (e) { return "—"; }
  }

  _formatLastFull(attrs) {
    if (attrs.last_full_info) return attrs.last_full_info;
    if (!attrs.last_full) return "—";
    try {
      const d = new Date(attrs.last_full);
      if (isNaN(d.getTime())) return "—";
      const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
      const vol = attrs.capacity_gallons != null ? " (" + Number(attrs.capacity_gallons).toFixed(1) + " Gal)" : "";
      return "Last: " + months[d.getMonth()] + " " + d.getDate() + vol;
    } catch (e) { return "—"; }
  }

  getCardSize() { return 7; }
}

class GasTankCardEditor extends HTMLElement {
  constructor() { super(); this._config = {}; }
  setConfig(config) { this._config = config || {}; this._tryRender(); }
  set hass(hass) { this._hass = hass; this._tryRender(); }
  _tryRender() { if (!this._hass) return; this._render(); }
  _render() {
    const cfg = this._config || {};
    this.innerHTML = `<div style="padding:16px;font-family:system-ui">
      <div style="margin-bottom:12px"><label style="display:block;font-weight:500;margin-bottom:4px">Entity (Level Sensor)</label>
      <input id="entity" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:6px" value="${cfg.entity || ""}" placeholder="sensor.gas_tank_monitor_level"></div>
      <div style="margin-bottom:12px"><label style="display:block;font-weight:500;margin-bottom:4px">Name (optional)</label>
      <input id="name" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:6px" value="${cfg.name || ""}" placeholder="Propane Tank"></div>
      <div style="display:flex;gap:16px;margin-top:8px">
        <label style="display:flex;align-items:center;gap:6px"><input id="burn" type="checkbox" ${cfg.show_burn_rate !== false ? "checked" : ""}> Show Burn Rate</label>
        <label style="display:flex;align-items:center;gap:6px"><input id="forecast" type="checkbox" ${cfg.show_forecast !== false ? "checked" : ""}> Show Forecast</label>
      </div></div>`;
    const update = () => {
      const newConfig = { type: "custom:gas-tank-card", ...this._config, entity: this.querySelector("#entity").value, name: this.querySelector("#name").value || undefined, show_burn_rate: this.querySelector("#burn").checked, show_forecast: this.querySelector("#forecast").checked };
      this._config = newConfig;
      this.dispatchEvent(new CustomEvent("config-changed", {
        bubbles: true,
        composed: true,
        detail: { config: newConfig },
      }));
    };
    this.querySelector("#entity").addEventListener("change", update);
    this.querySelector("#name").addEventListener("change", update);
    this.querySelector("#burn").addEventListener("change", update);
    this.querySelector("#forecast").addEventListener("change", update);
  }
}

try {
if (!customElements.get("gas-tank-card")) {
  customElements.define("gas-tank-card", GasTankCard);
}
if (!customElements.get("gas-tank-card-editor")) {
  customElements.define("gas-tank-card-editor", GasTankCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.find((c) => c.type === "gas-tank-card")) {
  window.customCards.push({
    type: "gas-tank-card",
    name: "Gas Tank Card",
    description: "Propane / LPG tank gauge, burn rate, depletion forecast",
    preview: true,
    documentationURL: "https://github.com/saboaua/gas_tank_monitor",
    getEntitySuggestion: (hass, entityId) => {
      if (!entityId || !hass || !hass.states) return null;
      if (!String(entityId).startsWith("sensor.")) return null;
      const st = hass.states[entityId];
      if (!st) return null;
      const attrs = st.attributes || {};
      const isOurs =
        String(entityId).includes("gas_tank") ||
        attrs.capacity_gallons != null ||
        attrs.config_entry_id != null;
      if (!isOurs) return null;
      return {
        config: {
          type: "custom:gas-tank-card",
          entity: entityId,
          name: attrs.friendly_name || "Propane Tank",
          show_burn_rate: true,
          show_forecast: true,
        },
      };
    },
  });
}

console.info(
  "%c GAS-TANK-CARD %c 2.2.11 ",
  "color:white;background:#0284c7;font-weight:bold;padding:2px 6px;border-radius:4px 0 0 4px",
  "color:#0284c7;background:#e0f2fe;font-weight:bold;padding:2px 6px;border-radius:0 4px 4px 0"
);

} catch (err) {
  console.error("%c GAS-TANK-CARD %c failed to register", "color:white;background:#dc2626;font-weight:bold;padding:2px 6px", "color:#dc2626", err);
}
