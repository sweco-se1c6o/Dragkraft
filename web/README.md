# Dragkraft web app (static, GitHub Pages)

A fully static frontend that runs the Dragkraft engine **in the browser** via
Pyodide (WebAssembly) — no server, no npm. It loads numpy + openpyxl from the
Pyodide distribution and installs the `dragkraft` wheel from `dist/`.

## Run locally

1. Build the engine wheel into `dist/` (behind a TLS-proxy add the trusted-host
   flags shown in `requirements-dev.txt`):

   ```powershell
   python -m pip wheel . --no-deps --no-build-isolation -w web/dist
   ```

2. Serve the `web/` folder over HTTP (Pyodide will not run from `file://`):

   ```powershell
   python -m http.server 8000 --directory web
   ```

3. Open <http://localhost:8000>, drop in a workbook (e.g. `old/luleaHamn3.xlsx`),
   and run.

## Deploy

Pushing to `main` runs `.github/workflows/pages.yml`, which rebuilds the wheel
and publishes `web/` to GitHub Pages. Enable it once under
**Settings → Pages → Build and deployment → Source: GitHub Actions**.

## Files

- `index.html` — layout (Tailwind via CDN, Plotly.js via CDN, Pyodide via CDN).
- `app.js` — boots Pyodide, builds the form, runs the simulation, draws charts.
- `dist/` — built wheel (git-ignored; produced by the build step / CI).

The browser-facing Python entry points live in `dragkraft/web/payload.py`.
