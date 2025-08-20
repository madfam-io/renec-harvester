# RENEC ECE Scraper — Software Specification

**Version:** 0.1.0
**Date:** 2025-08-20 (America/Mexico\_City)
**Owner:** Innovaciones MADFAM S.A.S. de C.V. — Data Engineering
**Sponsor:** Aldo Ruiz Luna (Founder/CEO)

---

## 0) Executive Summary (one-page)

**Objective.** Build a repeatable, legally compliant pipeline that extracts all publicly available **Entidades de Certificación y Evaluación (ECE)** records from RENEC, including their accredited **Estándares de Competencia (EC)**, normalizes the data, and publishes clean CSV/DB outputs with QA, diffing, and audit trails.

**Primary outputs.**

* `ece.csv`, `ec_estandar.csv`, `ece_ec.csv` (UTF-8)
* `renec_ece.sqlite` (or Postgres) with a 3-table relational schema
* `diff_YYYYMMDD.md` (adds/changes/removals vs. last run)

**Success criteria (go/no‑go).**

* 100% of visible ECE rows captured; row count parity with on-page total.
* ≥95% rows with at least one parsed contact field (email/phone/web) when present.
* EC codes validated (`^EC\d{4}$`), standards mapping complete for ≥90% of ECEs.
* CI job completes in <15 minutes under normal load; no rate-limit violations.
* Full lineage: timestamp, source URL, HTML snapshot on failure.

**Out of scope (v1).** Non-public PII, PDF downloads, OCR, and deep cross-linking beyond the ECE/EC mapping on the main directory views/modals.

**Operating cadence.** Automated weekly refresh (configurable), on-demand manual runs via CLI.

---

## 1) Scope & Coverage

**In-scope entities**

* **ECE** (certification entities): legal name, status, location (state/municipality if available), contact details, source URL, captured timestamps.
* **EC (standards)**: EC code, optional version/title, active status if shown.
* **ECE↔EC mapping**: which standards each ECE is accredited for.

**Navigation surfaces**

* Starting page for **ECE** directory.
* Row-level actions/modals providing **estándares acreditados** and **contacto**.
* Pagination controls (client- or server-side) across the directory table.

**Assumptions**

* Pages are public and rendered with client-side JavaScript; modals are either DOM-inserted or loaded via XHR.
* Some content may require clicking row actions or buttons; non-deterministic selectors possible.

---

## 2) Requirements

### 2.1 Functional Requirements (FR)

* **FR-001**: The system shall start from the configured ECE URL and fetch all rows across all pages.
* **FR-002**: The system shall detect and iterate pagination until the last page.
* **FR-003**: For each ECE row, the system shall extract visible columns (e.g., name, state, status) with whitespace/diacritics normalized.
* **FR-004**: The system shall open the **Estándares** action/modal (if present) and extract EC codes (+version/title where available).
* **FR-005**: The system shall open the **Contacto** action/modal (if present) and extract email(s), phone(s), and website URL(s).
* **FR-006**: The system shall store data in three normalized tables: `ece`, `ec_estandar`, `ece_ec`.
* **FR-007**: The system shall export CSVs and a SQLite database on each successful run.
* **FR-008**: The system shall produce a **diff report** against the prior successful snapshot (added/removed/changed ECEs and EC mappings).
* **FR-009**: The system shall track provenance: `fuente_url`, `capturado_en` (UTC ISO 8601), `row_hash`, and `run_id`.
* **FR-010**: The system shall validate EC codes with regex `^EC\d{4}$`; non-conforming values go to a `notes` field.
* **FR-011**: The system shall standardize `estado` names to official Mexican states and map to **INEGI codes**.
* **FR-012**: The system shall handle transient errors with retries and exponential backoff; on persistent failure it shall continue the run, logging the failed row and saving an HTML snapshot.
* **FR-013**: The system shall expose a CLI with subcommands: `scrape`, `export`, `validate`, `diff`, `replay` (from saved HTML), and `doctor` (env check).
* **FR-014**: The system shall be configurable via a YAML file and environment variables (12-factor friendly).
* **FR-015**: The system shall support dry-run mode (no writes) and headful debug mode for local troubleshooting.
* **FR-016**: The system shall run in Docker and via GitHub Actions on a schedule (weekly by default) and on manual dispatch.

### 2.2 Non‑Functional Requirements (NFR)

* **NFR-001 (Compliance)**: Respect robots/ToS, low request rate, and polite headers; no collection of non-public PII.
* **NFR-002 (Performance)**: End-to-end job finishes in <15 minutes with a single browser context and conservative delays.
* **NFR-003 (Resilience)**: Any single row/modal failure does not abort the run; error budget ≤2% rows.
* **NFR-004 (Observability)**: Structured logs, run metrics, and a summarized report artifact.
* **NFR-005 (Portability)**: Python 3.11+, Linux container; minimal external dependencies.
* **NFR-006 (Maintainability)**: Centralized selectors, typed models, docstrings, and a selector inventory readme.
* **NFR-007 (Security)**: No secrets stored in repo; use GitHub Encrypted Secrets; least-privilege IAM if Cloud is used.

---

## 3) Data Model & Schemas

### 3.1 Relational Schema (SQLite/Postgres)

**Table: `ece`**

* `ece_id` TEXT NULL — public ID like "ECE 105-13" if shown; else null
* `nombre_legal` TEXT NOT NULL
* `siglas` TEXT NULL
* `estatus` TEXT NULL  — e.g., "Vigente"/"No vigente" if present
* `domicilio_texto` TEXT NULL
* `estado` TEXT NULL  — canonical state name (Spanish)
* `estado_inegi` TEXT NULL — 2-digit INEGI code (string)
* `municipio` TEXT NULL
* `cp` TEXT NULL
* `telefono` TEXT NULL  — `;`-joined multi-values
* `correo` TEXT NULL    — `;`-joined multi-values
* `sitio_web` TEXT NULL — `;`-joined multi-values
* `fuente_url` TEXT NOT NULL
* `capturado_en` TEXT NOT NULL  — ISO 8601 UTC
* `row_hash` TEXT NOT NULL  — SHA-256 across canonicalized row
* `run_id` TEXT NOT NULL  — UUID per job

**PK/Indexes**

* PK: `(row_hash, run_id)` (technical)
* Unique advisory index: `(nombre_legal, estado_inegi)`

**Table: `ec_estandar`**

* `ec_clave` TEXT PRIMARY KEY  — e.g., EC0274
* `version` TEXT NULL
* `titulo` TEXT NULL
* `vigente` TEXT NULL
* `renec_url` TEXT NULL
* `first_seen` TEXT NOT NULL, `last_seen` TEXT NOT NULL

**Table: `ece_ec`** (many-to-many)

* `ece_row_hash` TEXT NOT NULL  — FK to `ece.row_hash` for the run where mapping was seen
* `ec_clave` TEXT NOT NULL  — FK to `ec_estandar.ec_clave`
* `acreditado_desde` TEXT NULL
* `run_id` TEXT NOT NULL
* Composite PK: `(ece_row_hash, ec_clave, run_id)`

### 3.2 CSVs

* `ece.csv` — columns mirroring `ece` except `run_id` (optional).
* `ec_estandar.csv` — `ec_clave,version,titulo,vigente,renec_url,first_seen,last_seen`.
* `ece_ec.csv` — `ece_row_hash,ec_clave,acreditado_desde,run_id`.

### 3.3 JSON Schemas (excerpt)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "madfam.renec.ece.v1",
  "type": "object",
  "properties": {
    "nombre_legal": {"type": "string", "minLength": 2},
    "estado": {"type": ["string", "null"]},
    "correo": {"type": ["string", "null"]},
    "telefono": {"type": ["string", "null"]}
  },
  "required": ["nombre_legal"]
}
```

---

## 4) System Architecture

```
┌───────────────────────────────┐
│ CLI (Typer)                   │  madfam-renec … (scrape/validate/diff)
└──────────────┬────────────────┘
               │
        ┌──────▼────────────────────┐
        │ Extractor (Playwright)    │  headless Chromium, polite rate limiting
        └──────┬────────────────────┘
               │ DOM / XHR
        ┌──────▼────────────────────┐
        │ Parser & Normalizer       │  Pydantic models, Unicode/regex
        └──────┬────────────────────┘
               │
        ┌──────▼───────────────┐   ┌──────────────────────┐
        │ Storage Layer        │   │ QA & Validation      │ Great Expectations-lite
        │ (SQLite/Postgres)    │   │ (expectations)       │
        └──────┬───────────────┘   └───────────┬──────────┘
               │                                │
        ┌──────▼───────────────┐         ┌──────▼──────────────┐
        │ Publisher (CSVs/DB)  │         │ Diff Engine         │ md report + stats
        └─────────┬────────────┘         └─────────┬───────────┘
                  │                                  │
            ┌─────▼─────┐                        ┌───▼──────────┐
            │ Artifacts │                        │ Notifications│ (optional Slack/email)
            └───────────┘                        └───────────────┘
```

**Key design choices**

* **Headless browser first** to tolerate JS rendering and DOM drift; **XHR replication** optional for performance if stable endpoints are discovered during Recon.
* **Selector abstraction** (single module) to minimize future maintenance.
* **Immutable snapshots** (raw HTML on failures) to support replayable tests and fast bug triage.

---

## 5) Extraction Strategy & Selectors

### 5.1 Recon Checklist (to be completed and committed pre-production)

* Identify **table root selector** (e.g., `table#…`), **tbody row selector**, and **pagination controls**.
* Identify **Estándares** trigger selector per row (button/link/icon) and **modal root** selector.
* Identify **Contacto** trigger selector per row and modal fields.
* Capture any **XHR endpoints** in DevTools → Network; note parameters for pagination/filtering.
* Confirm presence/format of **ECE IDs**, **status**, and geographic fields.
* Record **total row count** reported by UI (if present) to compare with scraped count.

Commit a `SELECTORS.md` with the exact CSS/XPath and any endpoint URLs/params.

### 5.2 Browser Automation Rules

* Launch Chromium with custom UA: `Mozilla/5.0 (MADFAM-Research)`.
* Load page with `wait_until="networkidle"`, then `wait_for_selector("table tbody tr")`.
* Pagination iteration: prefer **Next** button (`a.paginate_button.next`, `button.next`, or `li.next > a`) with disabled-state detection; fallback to page numbers if next is absent.
* Between page turns: `await page.wait_for_timeout(600–1200ms)` + re-check row presence.
* Row processing:

  * Extract visible `td` text; trim; collapse multiple spaces; replace non-breaking spaces.
  * For **Estándares**: open modal → scrape EC rows; for each, parse `ec_clave` (`^EC\d{4}$`), `version` (`^v(ersión)?\s*\d+`), and a free-text title if present.
  * For **Contacto**: parse modal text; extract using regex:

    * Email: `[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}`
    * Phone: permissive `\+?\d[\d\s().-]{7,}`; normalize to E.164 if possible, else keep raw.
    * URL: `https?://\S+`
* Close modals with robust selectors (`[aria-label=Close]`, `[data-dismiss='modal']`, `.ui-dialog-titlebar-close`).
* Capture **HTML snapshot** on exceptions (per row or per modal) to `artifacts/html/{run_id}/{page}-{row}.html`.

### 5.3 Rate Limiting & Backoff

* Global concurrency: 1 page; 1 modal at a time.
* Default delay: 600–1200ms between page flips and modal opens (jittered).
* Retries: 3 attempts for modal loads with backoff (1s, 2s, 4s).

---

## 6) Normalization & Enrichment

* **Unicode**: `unicodedata.normalize('NFC')`, remove zero-width, standardize quotes.
* **Whitespace**: strip, collapse internal spaces, normalize line breaks.
* **Case**: preserve proper case; for EC codes upper-case enforce.
* **Emails**: lowercase, deduplicate; join with `;`.
* **Phones**: remove duplicate separators; keep as raw + `telefono_e164` when confidently parsed (Mexico `+52`).
* **Websites**: URL-normalize (strip trailing punctuation, ensure scheme), deduplicate.
* **States**: map Spanish names and common abbreviations to canonical names + **INEGI** codes.

### 6.1 INEGI State Map (excerpt — complete table in Appendix A)

| Canonical        | Aliases (examples)           | INEGI |
| ---------------- | ---------------------------- | ----- |
| Aguascalientes   | AGS, Ags., Aguascalientes    | 01    |
| Baja California  | B.C., Baja California        | 02    |
| Ciudad de México | CDMX, D.F., Distrito Federal | 09    |
| Jalisco          | Jal., Jalisco                | 14    |
| Yucatán          | Yuc., Yucatán                | 31    |

---

## 7) Data Quality & Validation

**Mandatory expectations**

* ECE: `nombre_legal` not null; `fuente_url` not null; `capturado_en` ISO-8601.
* EC: `ec_clave` matches `^EC\d{4}$` or flagged in `notes`.
* Row parity: scraped row count equals UI-displayed total (± 0 if total provided).
* Uniqueness: `ece` records de-duplicated on `nombre_legal + estado_inegi` (post-normalization).
* Contact completeness: ≥95% of rows have at least one contact field if modals present.

**Soft expectations (warn-only)**

* Share of EC-mapped ECEs ≥90%.
* Phone normalization success rate ≥70%.

**Validation pipeline**

* Run expectations after extraction, before publishing. Fail the job if any **mandatory** expectation fails.

---

## 8) Diffing & Change Management

* Store prior snapshot CSVs/DBs in `artifacts/runs/{run_id}`.
* Compute diff by stable keys (`nombre_legal + estado_inegi`, `ec_clave`).
* Generate `diff_YYYYMMDD.md` with sections: **Added ECE**, **Removed ECE**, **Changed ECE fields**, **EC Additions/Removals** per ECE.
* Include summary metrics (counts, % change) and top changes.

---

## 9) Interfaces (CLI & Config)

### 9.1 CLI (Typer)

```
madfam-renec [COMMAND] [OPTIONS]

Commands:
  scrape      Run Playwright extractor and write raw JSON (tmp) + DB/CSVs.
  validate    Run expectations; fail non-compliant runs.
  export      Re-generate CSVs from DB.
  diff        Compare current snapshot vs. previous; emit Markdown report.
  replay      Parse from saved HTML snapshots for debugging.
  doctor      Environment and browser check.

Common Options:
  --config PATH         Path to YAML config (default: ./config.yaml)
  --headful             Run with visible browser (debug).
  --dry-run             Do not write outputs.
  --max-pages INT       Limit pages for testing.
  --log-level LEVEL     DEBUG|INFO|WARN|ERROR (default: INFO)
```

### 9.2 Config (YAML)

```yaml
run:
  timezone: America/Mexico_City
  out_dir: ./artifacts
  headless: true
  polite_delay_ms: [600, 1200]  # jitter range
  retries: 3
  timeout_sec: 30

sources:
  ece_url: "https://conocer.gob.mx/RENEC/controlador.do?comp=CE&tipoCertificador=ECE"
  # optional: oc_url for future extension

storage:
  sqlite_path: ./artifacts/renec_ece.sqlite
  postgres_url: null  # or env: ${POSTGRES_URL}

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

---

## 10) Logging & Observability

* **Structured logs** (JSON lines) with fields: `ts`, `run_id`, `event`, `page`, `row_index`, `level`, `message`, `duration_ms`.
* **Run summary** (stdout + artifact): total pages, total rows, standards extracted, failures, elapsed time.
* Optional **Slack** message: key metrics + link to diff report artifact.

---

## 11) Testing Strategy

**Unit tests**

* Regex extractors (emails, phones, URLs, EC codes).
* Normalization functions (Unicode, whitespace, state mapping).

**Integration tests**

* Parse saved HTML samples for: table, estándares modal, contacto modal.
* Pagination handler with mocked selectors.

**End-to-end (E2E)**

* Headless scrape against live site with `--max-pages 1` (CI smoke test).
* Full run gated behind manual workflow dispatch.

**Test fixtures**

* `tests/fixtures/rows_sample.html` (table with 3 rows, mixed content).
* `tests/fixtures/modal_estandares.html`.
* `tests/fixtures/modal_contacto.html`.

**Coverage target**: ≥85% statements in parsing/normalization modules.

---

## 12) Deployment & Operations

**Local dev**

* `pip install -r requirements.txt` ; `playwright install`.
* `.env` for secrets (if any); `make scrape`.

**Docker**

* Base image with Playwright deps; non-root user; healthcheck.
* Mount `artifacts/` for outputs.

**CI/CD (GitHub Actions)**

* Workflow: `ci.yaml` (lint, unit tests, integration with saved HTML, package).
* Workflow: `scrape.yaml` (manual + scheduled weekly; uploads artifacts; optional Slack notify).
* Timezone: schedule in **America/Mexico\_City** off-peak hours.

**Resources**

* 1 vCPU, 1.5GB RAM sufficient; disk ≤ 1GB for artifacts rotation.

---

## 13) Security, Legal & Compliance

* **Robots/ToS**: Honor crawl-delay semantics; single-browser, low-frequency access.
* **PII**: Only public institutional contacts; no enrichment with private datasets.
* **Data retention**: Keep last 12 months of snapshots; rotate older artifacts.
* **Provenance**: Persist `fuente_url`, timestamps, and (on failures) HTML snapshots for audit.
* **Secrets**: Store webhooks/DB URLs in GitHub Encrypted Secrets; never in code.

---

## 14) Risks & Mitigations

| Risk                       | Likelihood | Impact | Mitigation                                                      |
| -------------------------- | ---------: | -----: | --------------------------------------------------------------- |
| DOM/selector changes       |     Medium | Medium | Centralize selectors; add smoke test; quick hotfix path.        |
| Modal load flakiness       |     Medium |    Low | Retries + backoff; snapshot on failure; continue run.           |
| Anti-automation heuristics |        Low | Medium | Human-like pacing; no parallel clicks; identify as research UA. |
| Incomplete contact data    |     Medium |    Low | Best-effort parsing; mark as null; track coverage KPI.          |
| XHR endpoint changes       |        Low | Medium | Prefer DOM scraping; treat XHR path as optimization.            |

---

## 15) Implementation Plan & Milestones

**M0 (Day 0–1):** Recon & SELECTORS.md; stub schemas; state map asset.
**M1 (Day 2–3):** Playwright extractor; pagination; row parsing; standards modal.
**M2 (Day 4):** Contact modal parser; normalization; DB/CSV writer.
**M3 (Day 5):** QA expectations; diff engine; CLI polish.
**M4 (Day 6):** Tests & fixtures; Docker; CI pipelines; docs.
**M5 (Day 7):** UAT run; acceptance sign-off.

---

## 16) Acceptance Criteria (for sign‑off)

1. A full run completes with outputs (CSVs + SQLite) and a diff report, with **row count parity** vs. UI total (if available).
2. `ece.csv` has **no duplicate** `(nombre_legal, estado_inegi)` pairs post-normalization.
3. ≥90% of ECEs have ≥1 mapped EC; ≥95% of EC codes pass regex validation.
4. CI smoke test (`--max-pages 1`) is green; unit/integration tests ≥85% coverage in parsing modules.
5. Artifacts include logs and, for any failures, HTML snapshots.

---

## 17) Future Extensions (backlog)

* Add **OC** (Organismos Certificadores) by switching parameter; unify schemas.
* Enrich standards with sector metadata and cross-references.
* Publish to a **read-only dashboard** (Metabase) for internal stakeholders.
* Auto-open GitHub issue when validation fails; attach artifacts.
* i18n: lightweight English export variants of field names if needed.

---

## Appendix A — INEGI State Mapping (complete)

| INEGI | Canonical                       | Aliases (comma-separated)         |
| ----- | ------------------------------- | --------------------------------- |
| 01    | Aguascalientes                  | AGS, Ags., Aguascalientes         |
| 02    | Baja California                 | B.C., Baja California             |
| 03    | Baja California Sur             | BCS, Baja California Sur          |
| 04    | Campeche                        | Camp., Campeche                   |
| 05    | Coahuila de Zaragoza            | Coahuila, Coah.                   |
| 06    | Colima                          | Col., Colima                      |
| 07    | Chiapas                         | Chis., Chiapas                    |
| 08    | Chihuahua                       | Chih., Chihuahua                  |
| 09    | Ciudad de México                | CDMX, D.F., Distrito Federal      |
| 10    | Durango                         | Dgo., Durango                     |
| 11    | Guanajuato                      | Gto., Guanajuato                  |
| 12    | Guerrero                        | Gro., Guerrero                    |
| 13    | Hidalgo                         | Hgo., Hidalgo                     |
| 14    | Jalisco                         | Jal., Jalisco                     |
| 15    | México                          | Edo. Méx., Estado de México, Méx. |
| 16    | Michoacán de Ocampo             | Mich., Michoacán                  |
| 17    | Morelos                         | Mor., Morelos                     |
| 18    | Nayarit                         | Nay., Nayarit                     |
| 19    | Nuevo León                      | N.L., Nuevo Leon                  |
| 20    | Oaxaca                          | Oax., Oaxaca                      |
| 21    | Puebla                          | Pue., Puebla                      |
| 22    | Querétaro                       | Qro., Querétaro                   |
| 23    | Quintana Roo                    | Q. Roo, Quintana Roo              |
| 24    | San Luis Potosí                 | SLP, San Luis Potosí              |
| 25    | Sinaloa                         | Sin., Sinaloa                     |
| 26    | Sonora                          | Son., Sonora                      |
| 27    | Tabasco                         | Tab., Tabasco                     |
| 28    | Tamaulipas                      | Tamps., Tamaulipas                |
| 29    | Tlaxcala                        | Tlax., Tlaxcala                   |
| 30    | Veracruz de Ignacio de la Llave | Ver., Veracruz                    |
| 31    | Yucatán                         | Yuc., Yucatán                     |
| 32    | Zacatecas                       | Zac., Zacatecas                   |

---

## Appendix B — Sample CSV Headers

* `ece.csv`: `ece_id,nombre_legal,siglas,estatus,domicilio_texto,estado,estado_inegi,municipio,cp,telefono,correo,sitio_web,fuente_url,capturado_en,row_hash`
* `ec_estandar.csv`: `ec_clave,version,titulo,vigente,renec_url,first_seen,last_seen`
* `ece_ec.csv`: `ece_row_hash,ec_clave,acreditado_desde,run_id`

---

## Appendix C — Repository Layout

```
/ (repo root)
├─ src/
│  ├─ cli.py
│  ├─ extractor/
│  │  ├─ browser.py
│  │  ├─ selectors.py       # centralized selectors + recon notes
│  │  └─ parser.py
│  ├─ models.py             # pydantic models
│  ├─ normalize.py
│  ├─ storage.py            # sqlite/postgres writers
│  ├─ qa.py                 # expectations
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
├─ artifacts/               # run outputs, snapshots, logs (gitignored)
├─ config.yaml
├─ requirements.txt
├─ Dockerfile
├─ Makefile
├─ .env.example
└─ .github/workflows/
   ├─ ci.yaml
   └─ scrape.yaml
```

---

## Appendix D — Makefile (excerpt)

```makefile
.PHONY: install scrape test lint docker

install:
	pip install -r requirements.txt
	playwright install

scrape:
	python -m src.cli scrape --config ./config.yaml

export:
	python -m src.cli export --config ./config.yaml

diff:
	python -m src.cli diff --config ./config.yaml

test:
	pytest -q

lint:
	ruff check src tests

docker:
	docker build -t madfam/renec-scraper:latest .
```

---

## Appendix E — Coding Standards

* Type hints everywhere; `mypy` optional in CI.
* Docstrings (Google style) on public functions.
* One module per concern; no hard-coded selectors outside `selectors.py`.
* Avoid sleeps >1.5s; prefer awaits on selectors and `networkidle`.

---

## Appendix F — Example Selector Inventory (to fill during Recon)

```
TABLE_ROOT = "table.dataTable"
ROW = "table.dataTable tbody tr"
PAGINATION_NEXT = "a.paginate_button.next, button.next, li.next > a"
BTN_ESTANDARES = "a[title*='Estándares'], button:has-text('Estándares')"
BTN_CONTACTO = "a[title*='Contacto'], button:has-text('Contacto')"
MODAL_ROOT = ".modal, .ui-dialog, .swal2-popup"
```

---

**End of Specification v0.1.0**
