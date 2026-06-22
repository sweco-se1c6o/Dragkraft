"use strict";

// Bumped automatically by the deploy workflow; keep in sync with the built wheel.
const WHEEL_FILE = "dragkraft-0.1.0-py3-none-any.whl";

const COLORS = {
  speed: "#e8431f",
  speedFill: "rgba(232,67,31,0.10)",
  sth: "#16130d",
  gradient: "#6f6a5a",
  gradientSoft: "#a59f8c",
  altitude: "#3c6e71",
  curve: "#b8860b",
  signal: "#e8431f",
  stall: "#e8431f",
  grid: "#e3ddcf",
  ink3: "#8c8472",
  line: "#d8d1c0",
};

const FONT = '"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace';
const PLOT_CONFIG = { responsive: true, displayModeBar: false };

// Field metadata drives the generated form. type: number | text | bool | select
const CORE_FIELDS = [
  { key: "scenario_name", label: "Scenario name", type: "text" },
  { key: "sheet_name", label: "Sheet", type: "select", options: ["NyProfil", "DagensProfil", "SpeedTest"] },
  { key: "extra_wagon_count", label: "Wagons", type: "number", step: 1 },
  { key: "adhesion_coefficient", label: "Adhesion coefficient", type: "number", step: 0.05 },
  { key: "speed_override_kmh", label: "Max speed [km/h]", type: "number", step: 1 },
  { key: "flip_profiles", label: "Flip direction", type: "bool" },
];

// Shown only when the "Custom train…" preset is selected.
const CUSTOM_FIELDS = [
  { key: "custom_locomotive_count", label: "Locomotives", type: "number", step: 1 },
  { key: "custom_locomotive_mass_t", label: "Loco mass total [t]", type: "number", step: 1 },
  { key: "custom_wagon_mass_t", label: "Wagon mass each [t]", type: "number", step: 1 },
  { key: "custom_max_force_kn", label: "Max tractive force [kN]", type: "number", step: 10 },
  { key: "custom_power_kw", label: "Continuous power [kW]", type: "number", step: 100 },
  { key: "custom_start_force_kn", label: "Start force [kN]", type: "number", step: 10 },
  { key: "custom_start_speed_kmh", label: "Start-force speed [km/h]", type: "number", step: 1 },
  { key: "custom_vehicle_max_speed_kmh", label: "Vehicle max speed [km/h]", type: "number", step: 1 },
  { key: "custom_max_acceleration_mps2", label: "Max acceleration [m/s²]", type: "number", step: 0.1 },
  { key: "custom_max_deceleration_mps2", label: "Max deceleration [m/s²]", type: "number", step: 0.1 },
  { key: "custom_locomotive_length_m", label: "Loco length each [m]", type: "number", step: 0.1 },
  { key: "custom_wagon_length_m", label: "Wagon length each [m]", type: "number", step: 0.1 },
];

// Editable overrides for a library train (prefilled from its spec on selection).
const OVERRIDE_FIELDS = [
  { key: "loco_mass_t", label: "Loco mass total [t]", type: "number", step: 1, from: "locomotive_mass_t" },
  { key: "loco_length_m", label: "Loco length total [m]", type: "number", step: 0.1, from: "locomotive_length_m" },
  { key: "wagon_mass_t", label: "Wagon mass each [t]", type: "number", step: 0.5, from: "wagon_mass_t" },
  { key: "wagon_length_m", label: "Wagon length each [m]", type: "number", step: 0.1, from: "wagon_length_m" },
];

let trainLibrary = [];

const ADVANCED_FIELDS = [
  { key: "altitude_at_start_m", label: "Start altitude [m]", type: "number", step: 0.1 },
  { key: "time_offset_s", label: "Time offset [s]", type: "number", step: 1 },
  { key: "short_time_margin", label: "Short-time margin", type: "number", step: 0.01 },
  { key: "switch_speed_kmh", label: "Switch speed [km/h]", type: "number", step: 1 },
  { key: "speed_tolerance_kmh", label: "Speed tolerance [km/h]", type: "number", step: 0.1 },
  { key: "min_signal_deceleration_mps2", label: "Min signal decel [m/s²]", type: "number", step: 0.01 },
  { key: "reserve_before_arrival_s", label: "Reserve before arrival [s]", type: "number", step: 1 },
  { key: "freight_signal_advance_s_per_mps", label: "Freight signal advance [s/(m/s)]", type: "number", step: 0.1 },
  { key: "freight_signal_advance2_s_per_mps", label: "Freight signal advance 2 [s/(m/s)]", type: "number", step: 0.1 },
  { key: "freight_signal_advance2_m", label: "Freight signal advance 2 [m]", type: "number", step: 1 },
  { key: "min_time_to_hold_speed_s", label: "Min time to hold speed [s]", type: "number", step: 0.1 },
  { key: "use_train_length_delay", label: "Use train-length delay", type: "bool" },
  { key: "use_distance_before_signal", label: "Use distance before signal", type: "bool" },
  { key: "use_tav_distance", label: "Use TAV distance", type: "bool" },
  { key: "use_min_time_to_hold_speed", label: "Use min time to hold speed", type: "bool" },
];

let pyodide = null;
let workbookBytes = null;
let lastPayload = null;
let savedScenarios = loadScenarios();

const CMP_COLORS = ["#e8431f", "#16130b", "#3c6e71", "#b8860b", "#6f6a5a", "#9333ea", "#2563eb"];

// --------------------------------------------------------------------------- //
// Boot
// --------------------------------------------------------------------------- //
async function boot() {
  const setStatus = (t) => (document.getElementById("boot-status").textContent = t);
  try {
    setStatus("Starting simulation engine");
    pyodide = await loadPyodide();
    await pyodide.loadPackage(["numpy", "micropip"]);
    setStatus("Preparing engine");
    await pyodide.runPythonAsync(`
import micropip
await micropip.install("openpyxl")
`);
    // Fetch the wheel ourselves and hand micropip a filesystem path. Installing
    // straight from a URL trips a micropip download bug in recent Pyodide.
    const wheelUrl = new URL("dist/" + WHEEL_FILE, location.href).href;
    const resp = await fetch(wheelUrl);
    if (!resp.ok) throw new Error(`wheel fetch failed (${resp.status})`);
    pyodide.FS.writeFile("/tmp/" + WHEEL_FILE, new Uint8Array(await resp.arrayBuffer()));
    setStatus("Almost ready");
    await pyodide.runPythonAsync(`
await micropip.install("emfs:/tmp/${WHEEL_FILE}", deps=False)
from dragkraft.web.payload import run_simulation_json, default_form_values_json, train_library_json
`);
    const defaults = JSON.parse(pyodide.runPython("default_form_values_json()"));
    trainLibrary = JSON.parse(pyodide.runPython("train_library_json()"));
    buildForm(defaults);
    renderComparison(); // restore any scenarios saved in a previous visit
    document.getElementById("boot").style.display = "none";
    setEngine(true);
  } catch (err) {
    bootError();
    console.error("Engine startup failed:", err);
  }
}

function bootError() {
  const boot = document.getElementById("boot");
  boot.innerHTML =
    '<div class="boot-error">' +
    "<p>The simulation engine couldn’t start.</p>" +
    "<p class=\"boot-hint\">Check your network connection and reload the page.</p>" +
    '<button class="btn-primary" onclick="location.reload()">Reload</button>' +
    "</div>";
  setEngine(false);
}

function setEngine(ready) {
  const pill = document.getElementById("engine-pill");
  if (ready) {
    pill.textContent = "Engine ready";
    pill.className = "status status--ready";
  } else {
    pill.textContent = "Engine failed";
    pill.className = "status status--failed";
  }
  updateRunButton();
}

// --------------------------------------------------------------------------- //
// Form
// --------------------------------------------------------------------------- //
function buildForm(defaults) {
  const select = document.getElementById("train-select");
  select.innerHTML = trainLibrary
    .map((t) => `<option value="${t.key}" ${t.key === defaults.train_name ? "selected" : ""}>${t.label}</option>`)
    .join("");
  select.addEventListener("change", () => updateTrainUI(select.value));

  renderFields(document.getElementById("custom-train"), CUSTOM_FIELDS, defaults);
  renderFields(document.getElementById("train-overrides-fields"), OVERRIDE_FIELDS, defaults);
  renderFields(document.getElementById("form"), CORE_FIELDS, defaults);
  renderFields(document.getElementById("form-advanced"), ADVANCED_FIELDS, defaults);
  updateTrainUI(select.value);
}

function updateTrainUI(key) {
  const features = document.getElementById("train-features");
  const custom = document.getElementById("custom-train");
  const overrides = document.getElementById("train-overrides");
  const lib = trainLibrary.find((t) => t.key === key);
  const isCustom = lib && lib.custom;
  custom.classList.toggle("hidden", !isCustom);
  overrides.classList.toggle("hidden", !lib || isCustom);
  if (!lib || isCustom) {
    features.classList.add("hidden");
    return;
  }
  features.classList.remove("hidden");
  // Prefill the editable mass/length fields from the selected train's spec.
  for (const f of OVERRIDE_FIELDS) {
    const el = document.querySelector(`#train-overrides-fields [data-field="${f.key}"]`);
    if (el && lib[f.from] != null) el.value = lib[f.from];
  }
  const row = (k, v) => `<div><dt>${k}</dt><dd>${v}</dd></div>`;
  features.innerHTML =
    `<p class="train-desc">${lib.description}</p>` +
    '<dl class="mini-spec">' +
    row("Locomotives", lib.locomotives) +
    row("Max force", lib.max_tractive_force_kn + " kN") +
    row("Max speed", lib.vehicle_max_speed_kmh + " km/h") +
    row("Traction", lib.traction_model) +
    "</dl>";
}

function renderFields(container, fields, defaults) {
  container.innerHTML = "";
  for (const f of fields) {
    const value = defaults[f.key];
    const wrap = document.createElement("div");
    if (f.type === "bool") {
      wrap.className = "field-row";
      wrap.innerHTML = `
        <span class="field-label">${f.label}</span>
        <label class="switch">
          <input type="checkbox" data-field="${f.key}" data-type="bool" ${value ? "checked" : ""} />
          <span class="switch-track"></span>
          <span class="switch-thumb"></span>
        </label>`;
    } else if (f.type === "select") {
      const opts = f.options.map((o) => `<option ${o === value ? "selected" : ""}>${o}</option>`).join("");
      wrap.innerHTML = `
        <label class="field-label">${f.label}</label>
        <select data-field="${f.key}" data-type="text" class="field-select">${opts}</select>`;
    } else {
      const step = f.step != null ? `step="${f.step}"` : "";
      wrap.innerHTML = `
        <label class="field-label">${f.label}</label>
        <input type="${f.type === "number" ? "number" : "text"}" ${step} data-field="${f.key}" data-type="${f.type}"
          value="${value ?? ""}" class="field-input" />`;
    }
    container.appendChild(wrap);
  }
}

function gatherForm() {
  const values = {};
  document.querySelectorAll("[data-field]").forEach((el) => {
    const key = el.dataset.field;
    const type = el.dataset.type;
    if (type === "bool") values[key] = el.checked;
    else if (type === "number") values[key] = el.value === "" ? null : Number(el.value);
    else values[key] = el.value;
  });
  return values;
}

// --------------------------------------------------------------------------- //
// File handling + run
// --------------------------------------------------------------------------- //
function wireInputs() {
  const fileInput = document.getElementById("workbook-file");
  fileInput.addEventListener("change", (e) => loadFile(e.target.files[0]));
  const drop = document.getElementById("drop");
  ["dragover", "dragenter"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("dragover"); })
  );
  ["dragleave", "drop"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("dragover"); })
  );
  drop.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]); });
  document.getElementById("run-btn").addEventListener("click", run);

  document.getElementById("save-scenario").addEventListener("click", saveScenario);
  document.getElementById("clear-scenarios").addEventListener("click", clearScenarios);

  document.addEventListener("click", (e) => {
    // Export a chart to PNG via its figure header button.
    const png = e.target.closest(".fig-export[data-target]");
    if (png) {
      const gd = document.getElementById(png.dataset.target);
      if (gd && gd.data) exportChartPng(gd, png.dataset.name);
      return;
    }
    // Export data (JSON / CSV) via the run-action buttons.
    const data = e.target.closest("[data-export]");
    if (data) exportData(data.dataset.export);
  });
}

// --------------------------------------------------------------------------- //
// Scenario comparison
// --------------------------------------------------------------------------- //
function loadScenarios() {
  try {
    return JSON.parse(localStorage.getItem("dragkraft.scenarios") || "[]");
  } catch (e) {
    return [];
  }
}

function persistScenarios() {
  try {
    localStorage.setItem("dragkraft.scenarios", JSON.stringify(savedScenarios));
  } catch (e) {
    /* storage full or disabled — comparison still works in-memory this session */
  }
}

function saveScenario() {
  if (!lastPayload) return;
  const label =
    (document.getElementById("scenario-label").value || lastPayload.scenario_name || "Scenario").trim() ||
    "Scenario";
  const r = lastPayload.route;
  const t = lastPayload.speed_time;
  savedScenarios.push({
    label,
    summary: lastPayload.summary,
    position_km: downsample(r.position_km, 800),
    speed_by_position_kmh: downsample(r.simulated_speed_kmh, 800),
    time_s: downsample(t.time_s, 800),
    speed_by_time_kmh: downsample(t.speed_kmh, 800),
  });
  persistScenarios();
  renderComparison();
  document.getElementById("comparison").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearScenarios() {
  savedScenarios = [];
  persistScenarios();
  renderComparison();
}

function renderComparison() {
  const section = document.getElementById("comparison");
  document.getElementById("comparison-count").textContent = `${savedScenarios.length} saved`;
  if (savedScenarios.length === 0) {
    section.classList.add("hidden");
    if (document.getElementById("results").classList.contains("hidden")) {
      document.getElementById("empty").classList.remove("hidden");
    }
    return;
  }
  section.classList.remove("hidden");
  document.getElementById("empty").classList.add("hidden");

  const line = (_s, i) => ({ color: CMP_COLORS[i % CMP_COLORS.length], width: 2 });
  Plotly.react(
    "chart-cmp-position",
    savedScenarios.map((s, i) => ({ x: s.position_km, y: s.speed_by_position_kmh, name: s.label, mode: "lines", line: line(s, i) })),
    baseLayout("Position [km]", "Speed [km/h]"),
    PLOT_CONFIG
  );
  Plotly.react(
    "chart-cmp-time",
    savedScenarios.map((s, i) => ({ x: s.time_s, y: s.speed_by_time_kmh, name: s.label, mode: "lines", line: line(s, i) })),
    baseLayout("Time [s]", "Speed [km/h]"),
    PLOT_CONFIG
  );

  const base = savedScenarios[0].summary.total_time_s;
  renderTable(
    "table-comparison",
    ["#", "Scenario", "Total [s]", "Δ [s]", "Route [m]", "Wagons", "Adhesion", "Mass [t]", "Max [km/h]"],
    savedScenarios.map((s, i) => {
      const su = s.summary;
      return [
        i + 1, s.label, su.total_time_s, round1(su.total_time_s - base),
        su.route_length_m, su.wagons, su.adhesion_coefficient, su.train_mass_t, su.simulated_max_speed_kmh,
      ];
    })
  );
}

function downsample(arr, n) {
  if (!arr || arr.length <= n) return (arr || []).slice();
  const out = [];
  const step = (arr.length - 1) / (n - 1);
  for (let i = 0; i < n; i++) out.push(arr[Math.round(i * step)]);
  return out;
}

function round1(x) {
  return Math.round(x * 10) / 10;
}

// --------------------------------------------------------------------------- //
// Export (JSON / CSV)
// --------------------------------------------------------------------------- //
function exportData(kind) {
  if (!lastPayload) return;
  const name = (lastPayload.scenario_name || "scenario").replace(/[^a-z0-9_-]+/gi, "-");
  if (kind === "json") {
    download(`dragkraft-${name}.json`, JSON.stringify(lastPayload, null, 2), "application/json");
  } else if (kind === "speed") {
    const r = lastPayload.route, t = lastPayload.speed_time;
    const rows = r.position_km.map((p, i) => [p, r.simulated_speed_kmh[i], t.time_s[i]]);
    download(`dragkraft-${name}-speed.csv`, toCsv(["position_km", "speed_kmh", "time_s"], rows), "text/csv");
  } else if (kind === "timing") {
    const rows = lastPayload.tables.timing.map((x) => [x.position_m, x.name, x.time_s]);
    download(`dragkraft-${name}-timing.csv`, toCsv(["position_m", "name", "time_s"], rows), "text/csv");
  } else if (kind === "blocks") {
    const rows = lastPayload.tables.blocks.map((x) => [
      x.name, x.signal_position_m, x.speed_difference_mps, x.intersection_position_m,
      x.booking_time_s, x.arrival_time_s, x.release_time_s,
    ]);
    const headers = ["name", "signal_position_m", "speed_difference_mps", "intersection_position_m", "booking_time_s", "arrival_time_s", "release_time_s"];
    download(`dragkraft-${name}-blocks.csv`, toCsv(headers, rows), "text/csv");
  }
}

function toCsv(headers, rows) {
  return [headers.join(","), ...rows.map((r) => r.map(csvCell).join(","))].join("\n");
}

function csvCell(v) {
  if (v == null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

// Export a chart as a report-ready PNG: temporarily give it a solid white
// background (the live charts use a transparent canvas), then restore.
function exportChartPng(gd, name) {
  Plotly.relayout(gd, { paper_bgcolor: "#ffffff", plot_bgcolor: "#ffffff" })
    .then(() =>
      Plotly.downloadImage(gd, {
        format: "png",
        filename: "dragkraft-" + name,
        scale: 2,
        width: gd.clientWidth,
        height: gd.clientHeight,
      })
    )
    .finally(() =>
      Plotly.relayout(gd, { paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" })
    );
}

function download(filename, text, mime) {
  const blob = new Blob([text], { type: mime || "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function loadFile(file) {
  if (!file) return;
  workbookBytes = new Uint8Array(await file.arrayBuffer());
  document.getElementById("file-name").textContent = file.name;
  updateRunButton();
}

function updateRunButton() {
  document.getElementById("run-btn").disabled = !(pyodide && workbookBytes);
}

async function run() {
  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  btn.textContent = "Running…";
  try {
    pyodide.FS.writeFile("/workbook.xlsx", workbookBytes);
    pyodide.globals.set("FORM_JSON", JSON.stringify(gatherForm()));
    const out = await pyodide.runPythonAsync(`run_simulation_json("/workbook.xlsx", FORM_JSON)`);
    const payload = JSON.parse(out);
    if (payload.error) showBanner("error", payload.error);
    else render(payload);
  } catch (err) {
    showBanner("error", String(err));
    console.error(err);
  } finally {
    btn.textContent = "Run simulation";
    updateRunButton();
  }
}

// --------------------------------------------------------------------------- //
// Render
// --------------------------------------------------------------------------- //
function render(p) {
  lastPayload = p;
  document.getElementById("scenario-label").value = p.scenario_name || "Scenario";
  document.getElementById("empty").classList.add("hidden");
  document.getElementById("summary").classList.remove("hidden");
  const results = document.getElementById("results");
  results.classList.remove("hidden");
  results.classList.remove("reveal");
  void results.offsetWidth; // restart the reveal animation on each run
  results.classList.add("reveal");

  if (p.stall) {
    showBanner(
      "warn",
      `Train stalled — partial result. Reached ${p.stall.position_m} m in ${p.summary.total_time_s} s before traction ` +
        `could no longer keep the consist moving (speed ${p.stall.speed_mps} m/s, accel ${p.stall.acceleration_mps2} m/s²). ` +
        `Reduce wagons or raise adhesion to complete the route.`
    );
  } else {
    showBanner("ok", `Simulation ready — ${p.summary.route_length_m} m, ${p.summary.total_time_s} s.`);
  }

  renderSummary(p.summary);
  renderRoute(p);
  renderSpeedTime(p);
  renderAcceleration(p);
  renderBlocks(p);
  renderTable("table-timing", ["Position [m]", "Name", "Time [s]"], p.tables.timing.map((r) => [r.position_m, r.name, r.time_s]));
  renderTable(
    "table-blocks",
    ["Name", "Signal [m]", "Booking [s]", "Arrival [s]", "Release [s]"],
    p.tables.blocks.map((r) => [r.name, r.signal_position_m, r.booking_time_s, r.arrival_time_s, r.release_time_s])
  );
}

function showBanner(kind, text) {
  const el = document.getElementById("status-banner");
  el.className = `banner banner-${kind}`;
  el.textContent = text;
}

const SPEC_FIELDS = [
  ["Route", (s) => `${s.route_length_m} m`, (s) => s.sheet],
  ["Max speed", (s) => `${s.simulated_max_speed_kmh} km/h`, "Simulated"],
  ["Vehicle max", (s) => `${s.vehicle_max_speed_kmh} km/h`, "Rated"],
  ["Consist", (s) => `${s.locomotives}+${s.wagons}`, (s) => s.vehicle_type],
  ["Train mass", (s) => `${s.train_mass_t} t`, (s) => `Dyn ${s.dynamic_mass_t} t`],
  ["Length", (s) => `${s.train_length_m} m`, (s) => `Adh ${s.adhesion_mass_t} t`],
  ["Adhesion", (s) => `${s.adhesion_coefficient}`, "Coefficient"],
  ["Models", (s) => `${s.traction_model} / ${s.resistance_model}`, "Traction / resist"],
  ["Braking", (s) => `${s.brake_deceleration_min_mps2}–${s.brake_deceleration_max_mps2}`, "m/s² range"],
  ["Timing pts", (s) => `${s.timing_points}`, "Reached"],
  ["Blocks", (s) => `${s.blocks}`, "Reached"],
  ["Direction", (s) => (s.flip_profiles ? "Flipped" : "Normal"), "Profile"],
];

function renderSummary(s) {
  const host = document.getElementById("summary");
  const spec = SPEC_FIELDS.map(([label, val, sub]) => {
    const sv = typeof sub === "function" ? sub(s) : sub;
    return `<div><dt>${label}</dt><dd>${val(s)}<span class="sub">${sv}</span></dd></div>`;
  }).join("");
  host.innerHTML = `
    <div class="hero reveal">
      <div class="hero-label">Total run time</div>
      <div class="hero-value">${s.total_time_s}<span class="unit">s</span></div>
      <div class="hero-sub">${s.route_length_m} m route · ${s.sheet} · ${s.vehicle_type} · ${s.wagons} wagons</div>
    </div>
    <dl class="spec reveal">${spec}</dl>`;
}

function axis(title) {
  return {
    title: { text: title, font: { size: 11, color: COLORS.ink3 } },
    gridcolor: COLORS.grid,
    zeroline: false,
    linecolor: COLORS.line,
    ticks: "outside",
    tickcolor: COLORS.line,
    ticklen: 4,
    tickfont: { size: 10, color: COLORS.ink3 },
  };
}

function baseLayout(xTitle, yTitle, extra = {}) {
  return Object.assign(
    {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: FONT, size: 11, color: COLORS.ink3 },
      margin: { l: 56, r: 46, t: 10, b: 46 },
      hovermode: "x unified",
      hoverlabel: { bgcolor: "#16130d", bordercolor: "#16130d", font: { color: "#f3efe6", family: FONT, size: 12 } },
      xaxis: axis(xTitle),
      yaxis: axis(yTitle),
      legend: { orientation: "h", y: -0.24, x: 0, font: { size: 10 }, bgcolor: "rgba(0,0,0,0)" },
    },
    extra
  );
}

function stallShape(x, axisRefY = "paper") {
  return {
    type: "line", x0: x, x1: x, yref: axisRefY, y0: 0, y1: 1,
    line: { color: COLORS.stall, width: 2, dash: "dash" },
  };
}

function renderRoute(p) {
  const r = p.route;
  const traces = [
    { x: r.position_km, y: r.sth_kmh, name: "STH [km/h]", line: { color: COLORS.sth, width: 2.4 } },
    { x: r.position_km, y: r.simulated_speed_kmh, name: "Simulated [km/h]", fill: "tozeroy", fillcolor: COLORS.speedFill, line: { color: COLORS.speed, width: 3 } },
    { x: r.position_km, y: r.eq_gradient_promille, name: "Eq gradient [‰]", yaxis: "y2", line: { color: COLORS.gradient, width: 1.6 } },
    { x: r.position_km, y: r.raw_gradient_promille, name: "Gradient [‰]", yaxis: "y2", line: { color: COLORS.gradientSoft, width: 1.1, dash: "dash" } },
    { x: r.position_km, y: r.altitude_m, name: "Altitude [m]", yaxis: "y2", line: { color: COLORS.altitude, width: 1.4 } },
    { x: r.position_km, y: r.curve_radius_disp, name: "Curve radius [m/10]", yaxis: "y2", line: { color: COLORS.curve, width: 1 } },
  ];
  if (r.timing_markers.length) {
    traces.push({
      x: r.timing_markers.map((m) => m.position_km), y: r.timing_markers.map((m) => m.speed_kmh),
      text: r.timing_markers.map((m) => m.name), mode: "markers", name: "Timing",
      marker: { symbol: "diamond", size: 9, color: COLORS.signal },
    });
  }
  const yax = axis("Speed [km/h]");
  yax.range = [-10, 70];
  const layout = baseLayout("Position [km]", "Speed [km/h]", {
    yaxis: yax,
    yaxis2: {
      title: { text: "Overlays", font: { size: 12, color: "#94a3b8" } },
      overlaying: "y", side: "right", showgrid: false, zeroline: false,
      linecolor: "#e5e8f0", tickfont: { size: 11, color: "#94a3b8" },
    },
    shapes: (r.tunnels || []).map((t) => ({
      type: "line", x0: t.x0_km, x1: t.x1_km, y0: -4, y1: -4, line: { color: COLORS.sth, width: 5 },
    })),
  });
  if (p.stall) layout.shapes.push(stallShape(p.stall.position_km));
  Plotly.react("chart-route", traces, layout, PLOT_CONFIG);
}

function renderSpeedTime(p) {
  const t = p.speed_time;
  const traces = [{ x: t.time_s, y: t.speed_kmh, name: "Speed [km/h]", fill: "tozeroy", fillcolor: COLORS.speedFill, line: { color: COLORS.speed, width: 3 } }];
  const layout = baseLayout("Time [s]", "Speed [km/h]", { shapes: [] });
  for (const line of t.timing_lines) layout.shapes.push({ type: "line", x0: line.time_s, x1: line.time_s, yref: "paper", y0: 0, y1: 1, line: { color: COLORS.signal, width: 1, dash: "dot" } });
  if (p.stall) layout.shapes.push(stallShape(p.stall.time_s));
  Plotly.react("chart-speed-time", traces, layout, PLOT_CONFIG);
}

function renderAcceleration(p) {
  const a = p.acceleration;
  const traces = [{ x: a.time_s, y: a.accel_mps2, name: "Acceleration [m/s²]", fill: "tozeroy", fillcolor: "rgba(22,19,13,0.06)", line: { color: COLORS.sth, width: 1.8 } }];
  Plotly.react("chart-acceleration", traces, baseLayout("Time [s]", "Acceleration [m/s²]"), PLOT_CONFIG);
}

function renderBlocks(p) {
  const b = p.blocks_chart;
  const traces = [{ x: b.trajectory_time_s, y: b.trajectory_pos_km, name: "Trajectory", line: { color: COLORS.speed, width: 2.4 } }];
  const layout = baseLayout("Time [s]", "Position [km]", { hovermode: "closest", shapes: [], annotations: [] });
  for (const rect of b.rects) {
    layout.shapes.push({
      type: "rect", x0: rect.booking_time_s, x1: rect.release_time_s, y0: rect.position_km - 0.02, y1: rect.position_km + 0.02,
      fillcolor: "rgba(185,28,28,0.18)", line: { color: "rgba(185,28,28,0.55)", width: 1 },
    });
    layout.annotations.push({ x: rect.arrival_time_s, y: rect.position_km, text: rect.name, showarrow: false, font: { size: 10 } });
  }
  Plotly.react("chart-blocks", traces, layout, PLOT_CONFIG);
}

function renderTable(id, headers, rows) {
  const table = document.getElementById(id);
  const thead = `<thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${rows
    .map((r) => `<tr>${r.map((c) => `<td>${c ?? ""}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;
  table.innerHTML = thead + tbody;
}

wireInputs();
boot();
