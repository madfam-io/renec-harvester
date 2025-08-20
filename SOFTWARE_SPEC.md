# RENEC Harvester v02 — Software Specification (IR-root)

**Version:** 0.2.0
**Date:** 2025-08-20 (America/Mexico\_City)
**Owner:** Innovaciones MADFAM S.A.S. de C.V. — Data & Platforms
**Sponsor:** Aldo Ruiz Luna (Founder/CEO)

---

## 0) Executive Summary (one page)

**Objective.** Evolve the ECE-only scraper into a **site-wide RENEC Harvester** rooted at the **IR hub** (`controlador.do?comp=IR`). The system will discover all public RENEC components, extract and normalize every reachable dataset (entities + relationships), track changes over time, and publish versioned open data plus an API and UI.

**Outputs.**

* Versioned datasets: CSVs + SQLite/Postgres dumps for **entities** (`ec`, `certificador`, `centro`, `sector`, `comite`, `ubicacion`) and **edges** (`ece_ec`, `centro_ec`, `ec_sector`).
* **Event log** of harvests (XHR/HTML payloads, hashes, ETags) and **snapshots** (HTML on error).
* **Diff reports** (Markdown) and **run summaries** (JSONL).
* **Read-only API** (FastAPI) + **Next.js finder & visualizations** (ISR/SSG) fed by JSON bundles.

**Success criteria.**

* ≥99% coverage of rows reported by each RENEC component UI (or endpoint) on a full run.
* Accurate graph of EC↔ECE/OC↔Centros with `first_seen`/`last_seen` lifecycle.
* Automated weekly harvest (<20 min) with Slack alert + diff; daily lightweight freshness probe.
* Production of clean datasets & API/JSON artifacts with schema stability guarantees (semver).

**Non-goals (v2).** OCR/PDF extraction, private/PII data, authenticated areas, multi-language UI.

---

## 1) Scope & Coverage

**Entry point**: `https://conocer.gob.mx/RENEC/controlador.do?comp=IR` (IR hub).
**In scope components (examples; resolved during discovery):**

* **Certificadores**: `ECE`, `OC` directories and detail modals.
* **Estándares (EC)**: lists, detail pages, sector/comité relationships.
* **Centros de Evaluación (CE)**: listings, their EC offerings.
* **Sectores/Comités**: taxonomies and EC mappings.

**Data domains**

* **Entities**: `ec`, `certificador` (ECE/OC), `centro`, `sector`, `comite`, `ubicacion`.
* **Relationships**: `ece_ec`, `centro_ec`, `ec_sector`, and optional `certificador_centro` if exposed.
* **Provenance**: source URLs, XHR endpoints, ETags, hashes, timestamps.

---

## 2) Requirements

### 2.1 Functional Requirements (FR)

* **FR-001 Discovery**: Crawl from IR hub and enumerate **all internal links** matching `RENEC/controlador.do?comp=*`, breadth-first with domain scoping.
* **FR-002 Sniffing**: Record **XHR/fetch** requests/responses; persist candidate JSON endpoints, headers, bodies (with size caps), and hashes.
* **FR-003 Drivers**: Implement pluggable **component drivers** (EC, Certificadores, Centros, Sectores/Comités) that prefer **API/XHR path**; fallback to **DOM** when needed.
* **FR-004 Pagination/Modals**: Traverse all pages and open row actions/modals to extract nested data (e.g., acreditaciones, contacto).
* **FR-005 Parsing/Normalization**: Standardize Unicode, whitespace, state names → **INEGI codes**, EC code regex validation, email/phone/URL parsing.
* **FR-006 Storage**: Write to normalized relational schema (entities + edges) with `first_seen`/`last_seen` and `run_id`.
* **FR-007 Events & Snapshots**: Persist per-request **harvest events** and HTML **snapshots on failure**.
* **FR-008 Diffing**: Compute entity/edge adds, removals, and field changes between current and previous successful runs; emit Markdown report.
* **FR-009 Publishing**: Export CSVs & DB dumps; produce JSON bundles for API/UI; optionally publish to a CDN bucket.
* **FR-010 API**: Provide read-only endpoints for search/list/detail and a graph endpoint.
* **FR-011 UI**: Provide a Next.js finder with filters and visualizations (map, timeline, bipartite graph, sector Sankey).
* **FR-012 Scheduling**: GitHub Actions **weekly full harvest** and **daily freshness probe** that leverages ETag/If-Modified-Since where available.
* **FR-013 Observability**: Structured logs, per-run summary, and optional Slack alert.
* **FR-014 Configurability**: YAML config + env overrides; dry-run, headful debug, and page cap for smoke tests.

### 2.2 Non‑Functional Requirements (NFR)

* **NFR-001 Compliance**: Respect ToS/robots; conservative rate; institutional (non-PII) data only.
* **NFR-002 Performance**: Full weekly run ≤20 min on 1 vCPU/2GB; JSON bundles ≤50MB total.
* **NFR-003 Resilience**: Any single page/row failure does not abort run; retry with backoff; error budget ≤1% rows.
* **NFR-004 Stability**: Centralized selectors & endpoint registry; minimal churn in public API schemas (semver).
* **NFR-005 Security**: No secrets in repo; signed artifacts; least-privilege for storage/CDN.
* **NFR-006 Maintainability**: Typed models, docstrings, tests (≥85% for parsing/normalization).

---

## 3) Architecture

```
┌───────────────────────┐
│ CLI (Typer)           │  madfam-renec … crawl/sniff/harvest/publish/api/ui
└─────────────┬─────────┘
              │
       ┌──────▼───────────────────────────┐
       │ Playwright Engine                │  Chromium, polite pacing, headful debug
       └──────┬───────────────────────────┘
              │  DOM + Network
       ┌──────▼──────────────┐    ┌──────────────────────────┐
       │ Discovery Crawler   │    │ Network Recorder (XHR)   │ endpoints.json, payloads
       └──────┬──────────────┘    └───────────┬──────────────┘
              │                                 │
       ┌──────▼─────────────────────┐     ┌─────▼──────────────────┐
       │ Component Drivers          │     │ Endpoint Registry      │ selectors.py / endpoints.json
       │  (EC, ECE/OC, CE, …)       │     └────────────────────────┘
       └──────┬─────────────────────┘
              │
       ┌──────▼──────────────────────┐
       │ Parser & Normalizer         │  pydantic, regex, INEGI mapping
       └──────┬──────────────────────┘
              │
       ┌──────▼───────────────┐   ┌──────────────────────┐
       │ Storage (DB/CSVs)    │   │ Events & Snapshots   │ html/, xhr/
       └──────┬───────────────┘   └─────────┬────────────┘
              │                              │
       ┌──────▼───────────────┐        ┌─────▼──────────────┐
       │ QA & Diff Engine     │        │ Publisher          │ CSV/DB/JSON
       └──────┬───────────────┘        └─────────┬──────────┘
              │                                   │
       ┌──────▼───────────┐                 ┌─────▼────────────┐
       │ FastAPI (read)   │                 │ Next.js UI (ISR) │
       └──────────────────┘                 └───────────────────┘
```

---

## 4) Data Model (v2)

### 4.1 Entities

**`ec`** — estándar de competencia

* `ec_clave` (PK, TEXT, e.g., EC0274)
* `titulo` TEXT, `version` TEXT, `vigente` TEXT, `sector_id` TEXT NULL, `comite_id` TEXT NULL
* `renec_url` TEXT, `first_seen` TEXT, `last_seen` TEXT

**`certificador`** — ECE/OC

* `cert_id` (PK TEXT; public ID if present, else stable hash)
* `tipo` TEXT CHECK (ECE|OC)
* `nombre_legal` TEXT, `siglas` TEXT NULL, `estatus` TEXT NULL
* `domicilio_texto` TEXT NULL, `estado` TEXT NULL, `estado_inegi` TEXT NULL, `municipio` TEXT NULL, `cp` TEXT NULL
* `telefono` TEXT NULL, `correo` TEXT NULL, `sitio_web` TEXT NULL
* `src_url` TEXT, `first_seen` TEXT, `last_seen` TEXT, `row_hash` TEXT

**`centro`** — Centro de Evaluación (if exposed)

* `centro_id` (PK TEXT), `nombre` TEXT, `cert_id` TEXT NULL (parent), location/contact fields as above, `src_url`, `first_seen`, `last_seen`

**`sector`**

* `sector_id` (PK TEXT), `nombre` TEXT, `src_url`, `first_seen`, `last_seen`

**`comite`**

* `comite_id` (PK TEXT), `nombre` TEXT, `src_url`, `first_seen`, `last_seen`

**`ubicacion`** (optional normalized table)

* `ub_id` (PK TEXT), `estado`, `estado_inegi`, `municipio`, `cp`

### 4.2 Relationships

**`ece_ec`**

* `cert_id` TEXT FK, `ec_clave` TEXT FK, `acreditado_desde` TEXT NULL, `run_id` TEXT, PK (`cert_id`,`ec_clave`)

**`centro_ec`**

* `centro_id` TEXT FK, `ec_clave` TEXT FK, `run_id` TEXT, PK (`centro_id`,`ec_clave`)

**`ec_sector`**

* `ec_clave` TEXT FK, `sector_id` TEXT FK, `comite_id` TEXT NULL, PK (`ec_clave`,`sector_id`)

### 4.3 Events & Snapshots

**`harvest_events`**: `event_id` (PK), `run_id`, `url`, `method`, `status`, `etag`, `last_modified`, `content_sha256`, `content_length`, `ts`
**`page_snapshots`**: `run_id`, `url`, `path`, `ts`
**`xhr_payloads`**: (`url_hash`, `content_sha256`, `stored_at`, `path`) with size cap & dedupe

### 4.4 Views

* `v_current_*` views show records with `last_seen == latest_run` to represent the **current state**.

---

## 5) Discovery, Sniffing & Drivers

### 5.1 Discovery

* BFS crawl starting at IR; scope to `conocer.gob.mx/RENEC/`.
* Only follow links containing `controlador.do?comp=`.
* Record for each page: inlinks/outlinks, page title, content hash, discovered actions (buttons that open modals).

### 5.2 Network Recorder

* Intercept `fetch`/XHR; persist unique endpoints with request params, headers, and response metadata.
* Respect size caps (e.g., 10MB per body). Store **hash + first 256KB** for diffing.

### 5.3 Endpoint Registry (generated, then curated)

* JSON file `endpoints.json`:

```json
{
  "certificadores_list": {
    "url": "https://…/controlador.do?comp=CE&tipoCertificador=ECE",
    "method": "GET",
    "auth": null,
    "expects": "html",
    "notes": "Paginated table + modals"
  },
  "ec_list": {"url": "https://…/controlador.do?comp=EC", "expects": "html"}
}
```

### 5.4 Driver Interface

```python
class Driver(Protocol):
    name: str
    def discover(self, ctx: Ctx) -> list[Target]: ...    # seeds within component
    async def fetch(self, target: Target) -> Raw: ...   # API or DOM path
    def parse(self, raw: Raw) -> Records: ...           # entities + edges
```

---

## 6) Parsing, Normalization & Validation

* **Unicode** NFC; strip zero-width; collapse spaces; consistent quotes.
* **EC codes**: enforce upper-case; validate `^EC\d{4}$`; non-conformers → `notes`.
* **Emails/Phones/URLs**: permissive regex → normalize; MX phones try E.164 (`+52`) when confident.
* **States**: map aliases → canonical + **INEGI** (assets/states\_inegi.csv). Keep raw in `domicilio_texto`.
* **Expectations (QA)**: coverage parity vs. UI totals; uniqueness of keys; relationship integrity; drift checks for severe drops.

---

## 7) Change Detection & Freshness

* Prefer API freshness via **ETag/If-Modified-Since**; else hash body.
* Page-level **content hash** and per-row **row\_hash** for DOM sources.
* **Daily probe**: hit known endpoints with conditional requests; if changed, schedule an on-demand partial harvest.
* **Diff report** sections: Added/Removed/Changed for each entity; edge additions/removals; totals by component.

---

## 8) Publishing (Data, API, UI)

### 8.1 Data artifacts

* `/artifacts/runs/{run_id}/` contains CSVs, DB, logs, diffs, snapshots, xhr payloads.
* **Release channel**: `/artifacts/releases/{version}/` with semantic versioning for schema changes.

### 8.2 JSON bundles

* `/public/data/`:

  * `ec.json`, `certificadores.json`, `centros.json`, `sectors.json`, `graph.json` (ECE↔EC edges), paginated variants if large.

### 8.3 Read-only API (FastAPI)

* `GET /api/ec?search=&sector=&vigente=`
* `GET /api/certificadores?tipo=ECE|OC&estado=`
* `GET /api/certificadores/{cert_id}`
* `GET /api/certificadores/{cert_id}/estandares`
* `GET /api/graph` (bipartite, lightweight)

### 8.4 UI (Next.js 14+)

* **Finder** (EC search + filters), **Directory** (ECE/OC map/list by state), **Entity pages** (EC, Certificador, Centro), **Visualizations** (choropleth, timeline, bipartite, sector Sankey).
* **ISR**: revalidate on new release; data fetched from `/public/data` (static) or API.

---

## 9) Interfaces (CLI & Config)

### 9.1 CLI

```
madfam-renec [crawl|sniff|harvest|validate|diff|publish|serve|build-ui] [OPTIONS]

Options:
  --config PATH      YAML config (default: ./config.yaml)
  --headful          Visible browser
  --dry-run          No writes
  --max-pages INT    Cap for smoke runs
  --log-level LEVEL  DEBUG|INFO|WARN|ERROR
```

### 9.2 Config (YAML)

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
  # optional overrides for discovered components

storage:
  sqlite_path: ./artifacts/renec_v2.sqlite
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

---

## 10) Observability

* **Logs**: JSONL with `ts, run_id, event, component, url, page, row_idx, level, msg, duration_ms`.
* **Run summary**: counts per component, % coverage, failures, elapsed, data size.
* **Alerts**: Slack message with headline metrics + link to diff + artifacts.

---

## 11) Testing Strategy

* **Unit**: regex extractors; normalizers; state mapping; hashers.
* **Integration**: parse saved HTML/XHR fixtures per component; pagination; modal extraction.
* **E2E smoke**: CI `harvest --max-pages 1 --dry-run`.
* **Contract tests**: if stable XHRs exist, validate response schema (keys, types, required fields).
* **Coverage**: ≥85% in parsing/normalization; smoke workflows green.

---

## 12) Performance & Resilience

* Single browser context; 1 tab; jittered delays; retries (1s/2s/4s).
* Cache endpoint results within a run (dedupe by URL+params).
* Size caps: retain only first 256KB of large XHR bodies for diffing; full bodies optional via flag.
* Timeouts: 30s default; 60s for first page of each component.

---

## 13) Security, Legal & Compliance

* Institutional public data only; exclude person-level registries.
* Adhere to polite crawling and ToS; identify UA as research.
* Secrets via env/GitHub Secrets; artifact signing optional.
* Retention: keep 12 months of runs; rotate older snapshots.

---

## 14) Risks & Mitigations

| Risk                    | Likelihood | Impact | Mitigation                                             |
| ----------------------- | ---------: | -----: | ------------------------------------------------------ |
| Hidden/unstable XHRs    |     Medium | Medium | Prefer DOM baseline; record endpoints; contract tests. |
| Selector drift          |     Medium | Medium | Central registry; smoke tests; headful debug mode.     |
| Anti-automation         |        Low | Medium | Human-like pacing; one-tab; backoff; identifiable UA.  |
| Large payloads          |        Low |    Low | Size caps; hash-first; optional full retention.        |
| Mapping errors (states) |     Medium |    Low | Expand alias table; unit tests.                        |

---

## 15) Rollout Plan & Milestones

**Sprint 1 (Week 1)**

* Discovery crawler + network recorder; generate initial `endpoints.json` + crawl map.
* Implement **EC** and **Certificadores (ECE/OC)** drivers; storage v2 schema; CSV/DB export.
* QA expectations; diff engine; CI smoke run; Slack notifications.

**Sprint 2 (Week 2)**

* Add **Centros** & **Sector/Comité** drivers; relationship edges; JSON bundles.
* FastAPI read endpoints; Next.js finder (minimal) + map and bipartite viz.
* Daily probe workflow; release packaging; UAT + acceptance.

---

## 16) Acceptance Criteria

1. Weekly full harvest completes ≤20 minutes with **≥99% coverage** per component vs. UI totals.
2. Entities & edges populated with valid keys; EC code validation ≥95% pass; state mapping ≥98% success.
3. Diff report generated with adds/removals/changes; Slack alert sent.
4. API endpoints respond under 500ms p95 (local, no network) and serve current `v_current_*` views.
5. Next.js UI builds (SSG/ISR) and renders finder + at least **2 visualizations** from JSON bundles.

---

## 17) Repository Layout

```
/ (repo root)
├─ src/
│  ├─ cli.py
│  ├─ discovery/
│  │  ├─ crawler.py
│  │  └─ recorder.py
│  ├─ drivers/
│  │  ├─ ec.py
│  │  ├─ certificadores.py   # ECE/OC
│  │  ├─ centros.py
│  │  └─ sectores.py
│  ├─ registry/
│  │  ├─ selectors.py
│  │  └─ endpoints.json
│  ├─ parse/
│  │  ├─ normalizer.py
│  │  └─ validators.py
│  ├─ storage/
│  │  ├─ db.py
│  │  └─ export.py
│  ├─ qa/
│  │  ├─ expectations.py
│  │  └─ diff.py
│  ├─ publisher/
│  │  ├─ bundles.py
│  │  └─ release.py
│  ├─ api/
│  │  └─ main.py             # FastAPI
│  └─ ui/ (separate Next.js app in /ui)
├─ ui/ (Next.js)
│  ├─ app/
│  ├─ components/
│  └─ public/data/           # JSON bundles (optional)
├─ assets/
│  └─ states_inegi.csv
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ fixtures/ (html/xhr)
├─ artifacts/                # runs, releases (gitignored)
├─ docs/
│  └─ CrawlMap.md
├─ config.yaml
├─ requirements.txt
├─ Dockerfile
├─ Makefile
└─ .github/workflows/
   ├─ ci.yaml
   └─ harvest.yaml
```

---

## 18) Makefile (excerpt)

```makefile
.PHONY: install crawl sniff harvest validate diff publish serve build-ui

install:
	pip install -r requirements.txt && playwright install

crawl:
	python -m src.cli crawl --config ./config.yaml

sniff:
	python -m src.cli sniff --config ./config.yaml

harvest:
	python -m src.cli harvest --config ./config.yaml

validate:
	python -m src.cli validate --config ./config.yaml

diff:
	python -m src.cli diff --config ./config.yaml

publish:
	python -m src.cli publish --config ./config.yaml

serve:
	python -m src.api.main

build-ui:
	cd ui && npm i && npm run build
```

---

## 19) UI Spec (summary)

**Finder**: Search EC by keyword; filters: sector, vigente; result cards link to EC detail.
**Directory**: ECE/OC list + map; filters: estado, tipo, #EC acreditados.
**Entity pages**: EC → list of certificadores y centros; Certificador → contacto + EC list; Centro → EC ofrecidos.
**Visualizations**:

* Choropleth (ECE density by state),
* Bipartite graph (EC↔ECE) with hover highlighting,
* Timeline of new/retired ECs,
* Sector Sankey.

Accessibility: keyboard nav, semantic HTML; Spanish labels.

---

## 20) Appendix

### 20.1 Selector Registry (stub)

```
TABLE = "table.dataTable"
ROW = "table.dataTable tbody tr"
PAGINATION_NEXT = "a.paginate_button.next, button.next, li.next > a"
BTN_ESTANDARES = "a[title*='Estándares'], button:has-text('Estándares')"
BTN_CONTACTO = "a[title*='Contacto'], button:has-text('Contacto')"
MODAL = ".modal, .ui-dialog, .swal2-popup"
```

### 20.2 State Mapping (INEGI) — see `assets/states_inegi.csv`

(Complete table maintained as a CSV; aliases include AGS, CDMX, D.F., etc.)

### 20.3 API Example (FastAPI)

```python
@app.get("/api/certificadores")
async def certificadores(tipo: str | None = None, estado: str | None = None):
    # query v_current_certificador with filters
    ...
```

### 20.4 JSON Bundle Shapes

```json
// graph.json
{
  "nodes": [{"id": "EC0274", "type": "ec"}, {"id": "ECE-105-13", "type": "cert"}],
  "edges": [{"source": "EC0274", "target": "ECE-105-13"}]
}
```

---

**End of Specification v0.2.0**
