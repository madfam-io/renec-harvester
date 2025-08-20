# RENEC ECE Scraper

Public-data scraper for **RENEC** (México) focusing on **Entidades de Certificación y Evaluación (ECE)** and their accredited **Estándares de Competencia (EC)**. Built for reliability, compliance, and easy downstream use (CSVs + SQLite/Postgres), with automated QA and diff reports.

> Sponsor: Innovaciones MADFAM S.A.S. de C.V. · Owner: Data Engineering · Primary contact: Aldo Ruiz Luna
> Timezone: America/Mexico\_City

---

## ✨ Features

* Headless **Playwright** extractor resilient to JS-rendered tables and modals
* Full traversal of **pagination**, row actions (**Estándares**, **Contacto**)
* Clean **normalized outputs**: `ece.csv`, `ec_estandar.csv`, `ece_ec.csv`, plus `renec_ece.sqlite`
* **Diff report** (`diff_YYYYMMDD.md`) for adds/changes/removals vs. prior run
* **QA/validation** gates (row count parity, EC code regex, state mapping)
* **Provenance & audit**: source URL, timestamps, row hashes, run ID, failure snapshots
* **Dockerized**; **CI-ready** (GitHub Actions schedule + manual dispatch)

---

## 📦 What gets extracted

**ECE records**: legal name, status (if shown), location (state/municipality/CP if shown), contacts (email/phone/web), and provenance.
**EC standards**: EC code (e.g., EC0274), optional version/title/status if available.
**Mappings**: which ECs each ECE is accredited for.

See full data model in **docs/Specification.md** (three tables: `ece`, `ec_estandar`, `ece_ec`).

---

## 🚀 Quickstart

### 1) Requirements

* Python **3.11+**
* Node deps are handled by Playwright install step
* OS: Linux/macOS/Windows (Linux recommended for CI)

### 2) Install

```bash
# clone
git clone https://github.com/<your-org>/renec-ece-scraper.git
cd renec-ece-scraper

# python deps
pip install -r requirements.txt

# playwright browsers
playwright install
```

### 3) Configure

Edit **`config.yaml`** (or pass `--config` to CLI):

```yaml
run:
  timezone: America/Mexico_City
  out_dir: ./artifacts
  headless: true
  polite_delay_ms: [600, 1200]
  retries: 3
  timeout_sec: 30

sources:
  ece_url: "https://conocer.gob.mx/RENEC/controlador.do?comp=CE&tipoCertificador=ECE"

storage:
  sqlite_path: ./artifacts/renec_ece.sqlite
  postgres_url: null

parsing:
  state_mapping_path: ./assets/states_inegi.csv
  phone_country_code: "+52"

publishing:
  csv: true
  db: true
  keep_html_snapshots: true

notifications:
  slack_webhook: null
```

### 4) Run

```bash
# full scrape (headless)
python -m src.cli scrape --config ./config.yaml

# validate & export
python -m src.cli validate --config ./config.yaml
python -m src.cli export --config ./config.yaml

# diff vs. previous run
python -m src.cli diff --config ./config.yaml
```

Outputs will appear in `./artifacts/`:

* `ece.csv`, `ec_estandar.csv`, `ece_ec.csv`
* `renec_ece.sqlite`
* `diff_YYYYMMDD.md`
* `logs/run_<run_id>.jsonl`, `html/` snapshots if failures occur

---

## 🧭 CLI Reference

```
madfam-renec [COMMAND] [OPTIONS]

Commands:
  scrape      Run extractor; write DB/CSVs and artifacts
  validate    Run QA expectations; fail job on violations
  export      Re-generate CSVs from DB
  diff        Compare current snapshot vs. previous
  replay      Parse saved HTML snapshots (debug)
  doctor      Env & browser check

Common Options:
  --config PATH      YAML config (default: ./config.yaml)
  --headful          Visible browser for debugging
  --dry-run          No writes to disk
  --max-pages INT    Limit pages for testing
  --log-level LEVEL  DEBUG|INFO|WARN|ERROR (default: INFO)
```

---

## 🗄️ Data Model (summary)

**ece**: `ece_id?`, `nombre_legal*`, `siglas?`, `estatus?`, `domicilio_texto?`, `estado?`, `estado_inegi?`, `municipio?`, `cp?`, `telefono?`, `correo?`, `sitio_web?`, `fuente_url*`, `capturado_en*`, `row_hash*`, `run_id*`
**ec\_estandar**: `ec_clave*`, `version?`, `titulo?`, `vigente?`, `renec_url?`, `first_seen*`, `last_seen*`
**ece\_ec**: `ece_row_hash*`, `ec_clave*`, `acreditado_desde?`, `run_id*`

Keys & validation highlights:

* EC code regex: `^EC\d{4}$` (non-conformers flagged)
* State names mapped to canonical Spanish + **INEGI 2-digit** code
* Advisory uniqueness on `(nombre_legal, estado_inegi)`

---

## 🐳 Docker

```bash
docker build -t madfam/renec-ece-scraper:latest .

# run with artifacts mounted
mkdir -p artifacts
Docker run --rm \
  -v "$PWD/artifacts:/app/artifacts" \
  madfam/renec-ece-scraper:latest \
  python -m src.cli scrape --config ./config.yaml
```

> Tip: Use `--headful` locally (requires a display) when adjusting selectors.

---

## 🤖 CI/CD (GitHub Actions)

Example workflows (see `.github/workflows/`):

**ci.yaml** – lint, tests, headless smoke scrape (max 1 page)

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
      - run: python -m src.cli doctor
      - run: python -m src.cli scrape --config ./config.yaml --max-pages 1 --dry-run
```

**scrape.yaml** – weekly schedule + manual trigger, upload artifacts

```yaml
name: Scrape
on:
  schedule: [{ cron: '0 7 * * 1' }]  # Mondays 07:00 America/Mexico_City approx
  workflow_dispatch: {}
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: playwright install --with-deps
      - run: python -m src.cli scrape --config ./config.yaml
      - run: python -m src.cli validate --config ./config.yaml
      - run: python -m src.cli diff --config ./config.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: artifacts
          path: artifacts/**
```

---

## 🧪 Development

```bash
# tests
pytest -q

# lint
ruff check src tests

# make targets (optional)
make install
make scrape
make export
make diff
make test
make lint
```

**Project layout**

```
/ (repo root)
├─ src/
│  ├─ cli.py
│  ├─ extractor/
│  │  ├─ browser.py
│  │  ├─ selectors.py
│  │  └─ parser.py
│  ├─ models.py
│  ├─ normalize.py
│  ├─ storage.py
│  ├─ qa.py
│  ├─ diff.py
│  └─ utils.py
├─ assets/
│  └─ states_inegi.csv
├─ tests/
│  ├─ test_regex.py
│  ├─ test_normalize.py
│  ├─ test_parser.py
│  └─ fixtures/
│     ├─ rows_sample.html
│     ├─ modal_estandares.html
│     └─ modal_contacto.html
├─ docs/
│  └─ Specification.md
├─ artifacts/  # outputs (gitignored)
├─ config.yaml
├─ requirements.txt
├─ Dockerfile
├─ Makefile
└─ .github/workflows/
   ├─ ci.yaml
   └─ scrape.yaml
```

---

## 🛡️ Compliance & Ethics

* Public institutional data only; respect site ToS/robots and maintain human-like pacing.
* No storage of non-public PII. Rotate artifacts; keep 12 months by default.
* Keep **provenance** (source URL, timestamp). Save HTML snapshots on failure for audit/troubleshooting.
* Store secrets (DB URLs, webhooks) in environment / GitHub Encrypted Secrets.

---

## 🆘 Troubleshooting

* **Table rows never appear** → Confirm Playwright installed browsers; use `--headful` and inspect selectors in `src/extractor/selectors.py`.
* **Pagination stops early** → Update `PAGINATION_NEXT` selector; some UIs disable via CSS—check `is_disabled()` logic.
* **Modals not found** → Increase `timeout_sec`, ensure `MODAL_ROOT` covers framework in use (`.modal`, `.ui-dialog`, `.swal2-popup`).
* **Contact parsing misses fields** → Adjust regexes in `parser.py`; some emails/phones may be embedded in labels.
* **State mapping gaps** → Update `assets/states_inegi.csv` aliases.

---

## 📄 License & Attribution

* Copyright © Innovaciones MADFAM S.A.S. de C.V.
* Distributed internally; specify license before public release.

---

## 🤝 Contributing

* Create a feature branch, open a PR, and ensure CI is green.
* For selector changes, update `SELECTORS.md` (in `src/extractor/`) and add/adjust fixtures + tests.

---

## 📫 Contact

* Product/strategy: **Aldo Ruiz Luna**
* Maintainers: **Data Engineering @ MADFAM**

> *Nota:* Se aceptan PRs con mejoras de documentación en español. Para dudas operativas, abre un issue con logs adjuntos y, si es posible, un **HTML snapshot** del caso fallido.
