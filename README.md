# RENEC Harvester v02 (IR‑root)

Site‑wide public‑data **harvester** for México’s **RENEC** platform, rooted at the **IR hub**. Discovers components, sniffs XHR/JSON, extracts entities & relationships (EC, ECE/OC, Centros, Sectores/Comités), and publishes clean, versioned datasets plus a **read‑only API** and **Next.js UI**.

> Sponsor: Innovaciones MADFAM S.A.S. de C.V. · Owner: Data & Platforms · Primary contact: Aldo Ruiz Luna
> Timezone: America/Mexico\_City · License: TBD (internal for now)

---

## ✨ Features

* **IR‑rooted crawl** discovers all `controlador.do?comp=*` components (domain‑scoped)
* **Network sniffer** records XHR/fetch (URLs, headers, hashes); prefers API endpoints, falls back to DOM
* **Pluggable drivers** for EC, Certificadores (ECE/OC), Centros, Sectores/Comités
* **Normalized graph schema** (entities + edges with `first_seen/last_seen`)
* **QA & diff engine** (row‑count parity, key validation, change report)
* **Versioned outputs**: CSV + SQLite/Postgres, plus **JSON bundles** for web
* **Read‑only FastAPI** and **Next.js UI** (finder + maps/graphs) fed by bundles/API
* **ETag/If‑Modified‑Since** aware daily probe; weekly full harvest via GitHub Actions
* **Artifacts for audit**: structured logs, HTML snapshots on failure, XHR payload hashes
* **Dockerized**; Makefile targets; conservative, ToS‑friendly pacing

---

## 📦 What’s collected

**Entities**: `ec` (estándares), `certificador` (ECE/OC), `centro` (CE), `sector`, `comite`, optional `ubicacion`.
**Edges**: `ece_ec` (acreditaciones), `centro_ec` (oferta), `ec_sector` (taxonomía).
**Provenance**: source URLs, request metadata (ETag/Last‑Modified), content hashes, timestamps.

See **docs/Specification.md** (v2) for full schemas and acceptance criteria.

---

## 🚀 Quickstart

### 1) Requirements

* Python **3.11+**
* Playwright browsers (`playwright install`)
* Node **18+** (for UI in `/ui`)
* Optional: Docker 24+

### 2) Install

```bash
# clone
git clone https://github.com/madfam-io/renec-harvester.git
cd renec-harvester

# python deps
pip install -r requirements.txt

# playwright runtime
playwright install --with-deps
```

### 3) Configure

Create/edit **`config.yaml`**:

```yaml
run:
  timezone: America/Mexico_City
  out_dir: ./artifacts
  headless: true
  polite_delay_ms: [600, 1200]
  retries: 3
  timeout_sec: 30

sources:
  ir_url: "https://conocer.gob.mx/RENEC/controlador.do?comp=IR"

storage:
  sqlite_path: ./artifacts/renec.sqlite
  postgres_url: null

parsing:
  state_mapping_path: ./assets/states_inegi.csv
  phone_country_code: "+52"

publishing:
  csv: true
  db: true
  json_bundles: true
  release_channel: ./artifacts/releases

notifications:
  slack_webhook: null

scheduling:
  weekly_harvest_cron: "0 7 * * 1"   # Mondays 07:00 MX
  daily_probe_cron: "0 8 * * *"      # Daily 08:00 MX
```

### 4) Run

```bash
# 1) Map the site (IR-rooted crawl)
python -m src.cli crawl --config ./config.yaml

# 2) Sniff XHR endpoints while browsing targets
python -m src.cli sniff --config ./config.yaml

# 3) Harvest (extract all components via drivers)
python -m src.cli harvest --config ./config.yaml

# 4) Validate & Diff (gate + report)
python -m src.cli validate --config ./config.yaml
python -m src.cli diff --config ./config.yaml

# 5) Publish artifacts (CSVs/DB/JSON bundles)
python -m src.cli publish --config ./config.yaml

# Optional: serve read-only API
python -m src.api.main
```

**Outputs** in `./artifacts/runs/<run_id>/`:

* CSVs: `ec.csv`, `certificadores.csv`, `centros.csv`, `sectors.csv`, edges `ece_ec.csv`, `centro_ec.csv`, `ec_sector.csv`
* DB: `renec_v2.sqlite` (with `v_current_*` views)
* JSON: `/public/data/*.json` bundles (if enabled)
* Logs: `logs/run_<run_id>.jsonl`
* HTML/XHR: `html/` snapshots on failure, `xhr/` payload stubs & hashes
* Report: `diff_YYYYMMDD.md`, `summary.json`

---

## 🧭 CLI Reference

```
madfam-renec [crawl|sniff|harvest|validate|diff|publish|serve|build-ui] [OPTIONS]

Options:
  --config PATH      YAML config (default: ./config.yaml)
  --headful          Visible browser (debug)
  --dry-run          No writes (smoke)
  --max-pages INT    Limit pages (smoke)
  --log-level LEVEL  DEBUG|INFO|WARN|ERROR (default: INFO)
```

---

## 🗄️ Data Model (summary)

### Entities

* **`ec`**: `ec_clave*`, `titulo?`, `version?`, `vigente?`, `sector_id?`, `comite_id?`, `renec_url?`, `first_seen*`, `last_seen*`
* **`certificador` (ECE/OC)**: `cert_id*`, `tipo* (ECE|OC)`, `nombre_legal*`, `siglas?`, `estatus?`, `domicilio_texto?`, `estado?`, `estado_inegi?`, `municipio?`, `cp?`, `telefono?`, `correo?`, `sitio_web?`, `src_url*`, `first_seen*`, `last_seen*`, `row_hash*`
* **`centro`**: `centro_id*`, `nombre*`, `cert_id?`, location/contact fields, `src_url*`, `first_seen*`, `last_seen*`
* **`sector`**, **`comite`**: `*_id*`, `nombre*`, `src_url*`, `first_seen*`, `last_seen*`

### Relationships

* **`ece_ec`**: `cert_id*`, `ec_clave*`, `acreditado_desde?`, `run_id*`
* **`centro_ec`**: `centro_id*`, `ec_clave*`, `run_id*`
* **`ec_sector`**: `ec_clave*`, `sector_id*`, `comite_id?`

**Validation highlights**

* EC code regex: `^EC\d{4}$` (non‑conformers flagged in `notes`)
* State names → canonical + **INEGI 2‑digit** codes (see `assets/states_inegi.csv`)
* Coverage parity vs. UI totals per component; advisory uniqueness on stable keys

---

## 🌐 API (read‑only, FastAPI)

### Endpoints

* `GET /api/ec?search=&sector=&vigente=`
* `GET /api/certificadores?tipo=ECE|OC&estado=`
* `GET /api/certificadores/{cert_id}`
* `GET /api/certificadores/{cert_id}/estandares`
* `GET /api/graph` → bipartite nodes/edges (ECE↔EC)

**Run locally**

```bash
uvicorn src.api.main:app --reload --port 8787
```

---

## 🖥️ UI (Next.js)

A lightweight finder + directory with visualizations.

**Dev**

```bash
cd ui
npm i
npm run dev  # http://localhost:3000
```

**Build (ISR/SSG)**

```bash
npm run build && npm run start
```

**Data sources**

* Static JSON bundles from `/public/data/*.json` (exported by `publish`), or
* Live API at `/api/*` (configure base URL in `ui/.env.local`).

**Visualizations** (initial set)

* Choropleth: ECE/OC density by state
* Bipartite: EC ↔ ECE (hover highlight)
* Timeline: newly added/retired ECs
* Sankey: Sector → EC → ECE

---

## 🤖 CI/CD (GitHub Actions)

**ci.yaml** – lint, tests, smoke harvest (max 1 page, dry‑run)
**harvest.yaml** – weekly full harvest + daily probe + artifact upload

```yaml
name: CI
on: [push, pull_request]
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: playwright install --with-deps
      - run: pytest -q
      - run: python -m src.cli harvest --config ./config.yaml --max-pages 1 --dry-run
```

```yaml
name: Harvest
on:
  schedule:
    - cron: '0 7 * * 1'   # weekly (MX)
    - cron: '0 8 * * *'   # daily probe
  workflow_dispatch: {}
jobs:
  harvest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: playwright install --with-deps
      - run: python -m src.cli crawl --config ./config.yaml
      - run: python -m src.cli sniff --config ./config.yaml
      - run: python -m src.cli harvest --config ./config.yaml
      - run: python -m src.cli validate --config ./config.yaml
      - run: python -m src.cli diff --config ./config.yaml
      - run: python -m src.cli publish --config ./config.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: artifacts
          path: artifacts/**
```

---

## 🐳 Docker

```bash
# build
docker build -t madfam/renec-harvester:v02 .

# run harvest with artifacts mounted
mkdir -p artifacts
Docker run --rm \
  -v "$PWD/artifacts:/app/artifacts" \
  madfam/renec-harvester:v02 \
  python -m src.cli harvest --config ./config.yaml

# serve API
Docker run --rm -p 8787:8787 madfam/renec-harvester:v2 \
  uvicorn src.api.main:app --host 0.0.0.0 --port 8787
```

---

## 🧪 Development

```bash
# tests
pytest -q

# lint
ruff check src tests

# make (optional)
make install
make crawl
make sniff
make harvest
make validate
make diff
make publish
make build-ui
```

**Repo layout**

```
/ (repo root)
├─ src/
│  ├─ cli.py
│  ├─ discovery/        # crawler + recorder
│  ├─ drivers/          # ec, certificadores, centros, sectores
│  ├─ registry/         # selectors.py + endpoints.json
│  ├─ parse/            # normalizer + validators
│  ├─ storage/          # db + export
│  ├─ qa/               # expectations + diff
│  ├─ publisher/        # bundles + release
│  └─ api/              # FastAPI
├─ ui/                  # Next.js app
├─ assets/              # states_inegi.csv
├─ tests/               # unit + integration + fixtures
├─ artifacts/           # run outputs (gitignored)
├─ docs/                # spec + crawl map
├─ config.yaml
├─ requirements.txt
├─ Dockerfile
├─ Makefile
└─ .github/workflows/   # ci.yaml, harvest.yaml
```

---

## 🆘 Troubleshooting

* **No rows appear** → Ensure Playwright browsers installed; try `--headful` and inspect `registry/selectors.py`.
* **Pagination stalls** → Adjust `PAGINATION_NEXT` selector; some UIs disable via CSS.
* **Modals not found** → Expand `MODAL` selector to include framework variants (`.modal`, `.ui-dialog`, `.swal2-popup`).
* **Low contact parse rate** → Tune regexes in `parse/normalizer.py`; some fields include labels or punctuation.
* **State mapping gaps** → Add aliases to `assets/states_inegi.csv`; run unit tests.
* **Large payloads** → Increase size caps in recorder; enable full retention via config.

---

## 🛡️ Compliance & Ethics

* Public institutional data only; **no PII**; respect site ToS and robots directives.
* Polite, low‑rate crawling; single tab/context; backoff with jitter; identify as research UA.
* Keep provenance (timestamps, URLs, hashes); rotate artifacts (12‑month window by default).
* Store secrets in environment/GitHub Encrypted Secrets.

---

## 🤝 Contributing

* Open a PR with green CI (tests + smoke harvest).
* For selector/endpoint changes: update `registry/selectors.py`, `registry/endpoints.json`, fixtures under `tests/fixtures/`, and **docs/CrawlMap.md**.
* Use conventional commits; document breaking schema changes in **CHANGELOG.md** and bump dataset/API **semver**.

---

## 📄 License & Attribution

* © Innovaciones MADFAM S.A.S. de C.V.
* License: TBD (internal use). Before any public release, set explicit license and review compliance.

---

## 📫 Contact

* Product/strategy: **Aldo Ruiz Luna**
* Maintainers: **Data & Platforms @ MADFAM**
* Issues: please attach `summary.json` + relevant HTML snapshot or XHR hash reference.
