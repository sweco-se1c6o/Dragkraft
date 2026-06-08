"use strict";

// Bumped automatically by the deploy workflow; keep in sync with the built wheel.
const WHEEL_FILE = "dragkraft-0.1.0-py3-none-any.whl";

const COLORS = {
  speed: "#2457d6",
  speedFill: "rgba(36,87,214,0.10)",
  sth: "#1f2937",
  gradient: "#138a65",
  gradientSoft: "#52a884",
  altitude: "#7c3aed",
  curve: "#d97706",
  signal: "#b91c1c",
  stall: "#d94848",
  grid: "#e6edf5",
  plot: "#f8fafc",
};

const PLOT_CONFIG = { responsive: true, displaylogo: false };

// Field metadata drives the generated form. type: number | text | bool | select
const CORE_FIELDS = [
  { key: "scenario_name", label: "Scenario name", type: "text" },
  { key: "sheet_name", label: "Sheet", type: "select", options: ["NyProfil", "DagensProfil", "SpeedTest"] },
  { key: "train_name", label: "Train preset", type: "select", options: ["freight"] },
  { key: "extra_wagon_count", label: "Wagons", type: "number", step: 1 },
  { key: "adhesion_coefficient", label: "Adhesion coefficient", type: "number", step: 0.05 },
  { key: "speed_override_kmh", label: "Max speed [km/h]", type: "number", step: 1 },
  { key: "flip_profiles", label: "Flip direction", type: "bool" },
];

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

// --------------------------------------------------------------------------- //
// Boot
// --------------------------------------------------------------------------- //
async function boot() {
  const setStatus = (t) => (document.getElementById("boot-status").textContent = t);
  try {
    setStatus("Loading Python runtime…");
    pyodide = await loadPyodide();
    setStatus("Loading numpy…");
    await pyodide.loadPackage(["numpy", "micropip"]);
    setStatus("Loading openpyxl + Dragkraft engine…");
    const wheelUrl = new URL("dist/" + WHEEL_FILE, location.href).href;
    await pyodide.runPythonAsync(`
import micropip
await micropip.install("openpyxl")
await micropip.install("${wheelUrl}", deps=False)
from dragkraft.web.payload import run_simulation_json, default_form_values_json
`);
    const defaults = JSON.parse(pyodide.runPython("default_form_values_json()"));
    buildForm(defaults);
    document.getElementById("boot").style.display = "none";
    setEngine(true);
  } catch (err) {
    setStatus("Failed to start engine: " + err);
    setEngine(false, err);
    console.error(err);
  }
}

function setEngine(ready, err) {
  const pill = document.getElementById("engine-pill");
  if (ready) {
    pill.textContent = "Engine: ready";
    pill.className = "rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700";
  } else {
    pill.textContent = "Engine: failed";
    pill.className = "rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700";
  }
  updateRunButton();
}

// --------------------------------------------------------------------------- //
// Form
// --------------------------------------------------------------------------- //
function buildForm(defaults) {
  renderFields(document.getElementById("form"), CORE_FIELDS, defaults);
  renderFields(document.getElementById("form-advanced"), ADVANCED_FIELDS, defaults);
}

function renderFields(container, fields, defaults) {
  container.innerHTML = "";
  for (const f of fields) {
    const value = defaults[f.key];
    const wrap = document.createElement("div");
    if (f.type === "bool") {
      wrap.className = "flex items-center justify-between gap-2";
      wrap.innerHTML = `
        <span class="text-xs font-semibold text-slate-600">${f.label}</span>
        <label class="relative inline-flex cursor-pointer items-center">
          <input type="checkbox" data-field="${f.key}" data-type="bool" class="peer sr-only" ${value ? "checked" : ""} />
          <span class="h-5 w-9 rounded-full bg-slate-300 transition peer-checked:bg-brand-500"></span>
          <span class="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition peer-checked:translate-x-4"></span>
        </label>`;
    } else if (f.type === "select") {
      const opts = f.options.map((o) => `<option ${o === value ? "selected" : ""}>${o}</option>`).join("");
      wrap.innerHTML = `
        <label class="mb-1 block text-xs font-semibold text-slate-600">${f.label}</label>
        <select data-field="${f.key}" data-type="text" class="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm focus:border-brand-500 focus:outline-none">${opts}</select>`;
    } else {
      const step = f.step != null ? `step="${f.step}"` : "";
      wrap.innerHTML = `
        <label class="mb-1 block text-xs font-semibold text-slate-600">${f.label}</label>
        <input type="${f.type === "number" ? "number" : "text"}" ${step} data-field="${f.key}" data-type="${f.type}"
          value="${value ?? ""}" class="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm focus:border-brand-500 focus:outline-none" />`;
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
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("border-brand-500", "bg-brand-50"); })
  );
  ["dragleave", "drop"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("border-brand-500", "bg-brand-50"); })
  );
  drop.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]); });
  document.getElementById("run-btn").addEventListener("click", run);
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
  document.getElementById("empty").style.display = "none";
  document.getElementById("summary").classList.remove("hidden");
  document.getElementById("results").classList.remove("hidden");

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
  el.classList.remove("hidden");
  const styles = {
    ok: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warn: "border-amber-200 bg-amber-50 text-amber-800",
    error: "border-red-200 bg-red-50 text-red-800",
  };
  el.className = `rounded-xl border px-4 py-3 text-sm font-medium ${styles[kind]}`;
  el.textContent = text;
}

const CARD_FIELDS = [
  ["Run time", (s) => `${s.total_time_s} s`, "Simulation duration"],
  ["Route", (s) => `${s.route_length_m} m`, (s) => s.sheet],
  ["Max speed", (s) => `${s.simulated_max_speed_kmh} km/h`, "Simulated"],
  ["Consist", (s) => `${s.locomotives} loco / ${s.wagons} wagons`, (s) => s.vehicle_type],
  ["Train mass", (s) => `${s.train_mass_t} t`, (s) => `Dynamic ${s.dynamic_mass_t} t`],
  ["Length", (s) => `${s.train_length_m} m`, (s) => `Adhesion ${s.adhesion_mass_t} t`],
  ["Adhesion", (s) => `${s.adhesion_coefficient}`, "Coefficient"],
  ["Models", (s) => `${s.traction_model} / ${s.resistance_model}`, "Traction / resistance"],
  ["Braking", (s) => `${s.brake_deceleration_min_mps2}–${s.brake_deceleration_max_mps2}`, "Decel range [m/s²]"],
  ["Infrastructure", (s) => `${s.timing_points} timing / ${s.blocks} blocks`, "Workbook signals"],
];

function renderSummary(s) {
  const host = document.getElementById("summary");
  host.innerHTML = CARD_FIELDS.map(([label, val, detail]) => {
    const d = typeof detail === "function" ? detail(s) : detail;
    return `<div class="card p-4">
      <div class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">${label}</div>
      <div class="mt-1 text-lg font-bold text-slate-800">${val(s)}</div>
      <div class="text-xs text-slate-400">${d}</div>
    </div>`;
  }).join("");
}

function baseLayout(title, xTitle, yTitle, extra = {}) {
  return Object.assign(
    {
      title: { text: title, font: { size: 15 } },
      template: "plotly_white",
      paper_bgcolor: "#ffffff",
      plot_bgcolor: COLORS.plot,
      margin: { l: 58, r: 56, t: 48, b: 56 },
      hovermode: "x unified",
      hoverlabel: { bgcolor: "#172033", font: { color: "#fff" } },
      xaxis: { title: xTitle, gridcolor: COLORS.grid },
      yaxis: { title: yTitle, gridcolor: COLORS.grid, zerolinecolor: "#cbd5e1" },
      legend: { orientation: "h", y: -0.2, x: 0 },
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
  const layout = baseLayout("Route profile", "Position [km]", "Speed [km/h]", {
    yaxis: { title: "Speed [km/h]", range: [-10, 70], gridcolor: COLORS.grid, zerolinecolor: "#cbd5e1" },
    yaxis2: { title: "Overlays", overlaying: "y", side: "right", showgrid: false },
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
  const layout = baseLayout("Speed over time", "Time [s]", "Speed [km/h]", { shapes: [] });
  for (const line of t.timing_lines) layout.shapes.push({ type: "line", x0: line.time_s, x1: line.time_s, yref: "paper", y0: 0, y1: 1, line: { color: COLORS.signal, width: 1, dash: "dot" } });
  if (p.stall) layout.shapes.push(stallShape(p.stall.time_s));
  Plotly.react("chart-speed-time", traces, layout, PLOT_CONFIG);
}

function renderAcceleration(p) {
  const a = p.acceleration;
  const traces = [{ x: a.time_s, y: a.accel_mps2, name: "Acceleration [m/s²]", fill: "tozeroy", fillcolor: "rgba(19,138,101,0.10)", line: { color: COLORS.gradient, width: 2 } }];
  Plotly.react("chart-acceleration", traces, baseLayout("Acceleration over time", "Time [s]", "Acceleration [m/s²]"), PLOT_CONFIG);
}

function renderBlocks(p) {
  const b = p.blocks_chart;
  const traces = [{ x: b.trajectory_time_s, y: b.trajectory_pos_km, name: "Trajectory", line: { color: COLORS.speed, width: 2.2 } }];
  const layout = baseLayout("Block occupation", "Time [s]", "Position [km]", { hovermode: "closest", shapes: [], annotations: [] });
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
  const thead = `<thead class="sticky top-0 bg-slate-50"><tr>${headers.map((h) => `<th class="px-4 py-2 text-left text-xs font-bold text-slate-500">${h}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${rows
    .map((r) => `<tr class="border-t border-slate-100">${r.map((c) => `<td class="px-4 py-1.5 text-slate-700">${c ?? ""}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;
  table.innerHTML = thead + tbody;
}

wireInputs();
boot();
