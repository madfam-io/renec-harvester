# RENEC Harvester v02 — Development Roadmap

**Date:** 2025-08-20
**Owner:** Innovaciones MADFAM · Data & Platforms
**Sponsor:** Aldo Ruiz Luna

---

## 0) Purpose (one‑pager)

Deliver a production‑grade, IR‑rooted **RENEC Harvester** that discovers all public components, extracts entities/relationships, tracks change, and publishes versioned data + API + UI. Target **GA by Oct 3, 2025** with measurable coverage and reliability.

**Key outcomes**

* ≥99% coverage vs. UI totals across components (EC, ECE/OC, CE, Sectores/Comités)
* Weekly full harvest ≤20 min; daily probe using ETag/IMS; diff + Slack alerts
* Public‑ready artifacts: CSV/SQLite dumps, JSON bundles; read‑only API; Next.js finder + 2 visualizations

---

## 1) Timeline at a glance (MX Time)

| Phase                       | Dates (2025)  | Goal                                                                              |
| --------------------------- | ------------- | --------------------------------------------------------------------------------- |
| **Sprint 0 — Recon & Map**  | Aug 21–22     | Crawl map, selectors, endpoint registry stub                                      |
| **Sprint 1 — Core Harvest** | Aug 25–Sep 5  | Drivers for EC + Certificadores (ECE/OC); storage v2; QA & diff                   |
| **Sprint 2 — Graph & UI**   | Sep 8–Sep 19  | Drivers for Centros + Sectores/Comités; JSON bundles; FastAPI; minimal Next.js UI |
| **Hardening & RC**          | Sep 22–Sep 26 | Perf, resilience, CI probes, docs; RC cut `v0.2.0-rc.1`                           |
| **Launch & Handover (GA)**  | Sep 29–Oct 3  | GA `v0.2.0`; runbook; KT; backlog triage                                          |

> Cadence: Mon/Wed standups (15m), Fri demo (20m), async updates by default.

---

## 2) Workstreams → Epics → Milestones

### A) Discovery & Sniffing

* **E1.1** IR‑rooted crawler (domain‑scoped BFS) → *M0:* CrawlMap.md + URL graph
* **E1.2** Network recorder (XHR/Fetch) → *M0:* `registry/endpoints.json` (auto‑generated + curated)
* **E1.3** Change fingerprinting → *M1:* page content hash, XHR body hash, headers (ETag/Last‑Modified)

### B) Drivers (Pluggable Extractors)

* **E2.1** EC driver (list + detail; sector/comité links) → *M1 deliverable: `ec.csv`*
* **E2.2** Certificadores driver (ECE & OC) with modals (Estándares, Contacto) → *M1: `certificadores.csv`, `ece_ec.csv`*
* **E2.3** Centros driver (if exposed) → *M2: `centros.csv`, `centro_ec.csv`*
* **E2.4** Sectores/Comités driver → *M2: `sectors.csv`, `ec_sector.csv`*

### C) Storage, QA & Diff

* **E3.1** Schema (entities + edges + events) → *M1: `renec.sqlite`*
* **E3.2** Expectations (coverage, EC regex, INEGI mapping) → *M1:* `validate` gate
* **E3.3** Diff engine & report → *M1:* `diff_YYYYMMDD.md`

### D) Publishing & API

* **E4.1** CSV/DB publisher (releases/) → *M1*
* **E4.2** JSON bundle builder → *M2*
* **E4.3** FastAPI (read‑only) → *M2:* `/api/ec`, `/api/certificadores`, `/api/graph`

### E) UI & Visualizations (Next.js)

* **E5.1** Finder (EC search + filters) → *M2*
* **E5.2** Directory (ECE/OC by state) → *M2*
* **E5.3** Viz: Choropleth + Bipartite → *M2*
* **E5.4** Performance & ISR hooks → *RC*

### F) Ops, CI/CD & Docs

* **E6.1** CI smoke (harvest 1 page, dry‑run) → *M1*
* **E6.2** Weekly harvest + daily probe workflows → *M2*
* **E6.3** Runbook, README, Spec, CrawlMap → *RC*
* **E6.4** Handover & KT → *GA*

---

## 3) Gantt‑style outline (ASCII)

```
Aug 21  Aug 28        Sep 4         Sep 11        Sep 18        Sep 25        Oct 2
| Sprint0 |
 [Discovery■■]
 [Sniffing ■]
| Sprint1 |
 [EC Driver  ■■■■]
 [Certif.Drv ■■■■]
 [Schema/QA  ■■■ ]
| Sprint2 |
 [CentrosDrv  ■■■]
 [SectoresDrv ■■■]
 [Bundles/API ■■ ]
 [UI Finder   ■■ ]
| RC |
 [Perf/Resil ■■ ] [Docs/Runbook ■]
| GA |
 [Release/KT ■]
```

---

## 4) Staffing & RACI

| Role            | Name         | R | A | C | I |
| --------------- | ------------ | - | - | - | - |
| Product/Sponsor | Aldo         |   | A | C | I |
| Tech Lead       | Sr. Data Eng | R |   | C | I |
| Backend/Drivers | Data Eng     | R |   |   | I |
| Frontend (UI)   | FE Eng       | R |   | C | I |
| DevOps/CI       | DevOps       | R |   | C | I |
| QA              | QA Eng       | R |   | C | I |

Notes: Tech Lead is DRI for architectural decisions; Aldo is final approver at RC/GA gates.

---

## 5) KPIs & Acceptance Gates

**Coverage:** ≥99% rows vs. UI totals per component (gate for GA)
**Correctness:** EC code regex pass ≥95%; state mapping success ≥98%
**Performance:** Full weekly harvest ≤20 min; API p95 ≤500ms (local)
**Resilience:** Row failure rate ≤1%; 0 fatal aborts in last 3 runs
**Ops:** CI green; weekly + daily workflows succeed for 7 consecutive days (pre‑GA)

**Go/No‑Go (RC → GA)**

* All KPIs met; diff report clean; docs/runbook complete; on‑call calendar set

---

## 6) Dependencies & Constraints

* Python 3.11+, Playwright runtime; Node 18+ for UI
* Access to GitHub Actions; Slack webhook (optional)
* ToS/robots compliance; one‑tab conservative pacing

---

## 7) Risk Register

| Risk                               | Likelihood | Impact | Owner     | Mitigation                                      |
| ---------------------------------- | ---------: | -----: | --------- | ----------------------------------------------- |
| XHR endpoints unstable/hidden      |        Med |    Med | Data Eng  | DOM fallback; endpoint registry; contract tests |
| Selector drift                     |        Med |    Med | Data Eng  | Central selectors; smoke tests; headful debug   |
| UI structure differs per component |        Med |    Low | Tech Lead | Driver plugin abstraction                       |
| Large payloads → slow runs         |        Low |    Low | DevOps    | Size caps; caching; prefer API                  |
| Contact parsing noisy              |        Med |    Low | QA        | Regex tuning; heuristic cleanup; unit tests     |

---

## 8) Backlog (MoSCoW, prioritized)

**Must**: IR crawl, XHR recorder, EC + Certificadores drivers, schema v2, QA/diff, CSV/DB export, CI smoke
**Should**: Centros & Sectores drivers, JSON bundles, FastAPI, Next.js finder + 2 vizzes
**Could**: Choropleth theming; Sankey; API pagination; CDN publish
**Won’t (v2)**: OCR/PDF, PII sources, authenticated areas, multi‑language

---

## 9) Detailed Sprint Plans

### ✅ Sprint 0 (Aug 21–22) — COMPLETE

* ✅ **Crawl from IR**: 13+ active RENEC components discovered and mapped
* ✅ **Export CrawlMap**: Site structure documented with URLs, titles, component types
* ✅ **Record XHRs**: Network interception foundation implemented  
* ✅ **Seed endpoints.json**: Working RENEC URLs identified and verified
* ✅ **Draft selectors.py**: Component detection and parsing framework ready
* ✅ **QA expectations**: Testing framework with 80% pass rate achieved
* ✅ **Prepare fixtures**: Comprehensive test suite and validation scripts
  **Deliverables:** ✅ `docs/SPRINT_0_COMPLETION.md`, ✅ `src/core/constants.py` (updated), ✅ Local testing framework

**Major Breakthrough**: Eliminated all 404 errors and achieved functional site access! 🎉

### 🚀 Sprint 1 (Aug 25–Sep 5) — READY TO START

**Foundation Status**: ✅ SOLID - All Sprint 0 blockers resolved, 13 components accessible

**Priority Tasks**:
* **EC driver implementation**: Extract standards from discovered endpoints (`ESLACT`, `ESLNORMTEC`, etc.)
* **Certificadores driver**: Parse ECE/OC data with modal interaction support
* **PostgreSQL schema v2**: Implement full relational model with temporal tracking
* **Data pipelines**: Validation, normalization, and deduplication systems
* **Export capabilities**: CSV/DB output with proper formatting
* **QA framework**: Coverage validation and diff reporting
* **CI integration**: Smoke tests and quality gates

**Target Deliverables**: `ec.csv`, `certificadores.csv`, `ece_ec.csv`, `renec_v2.sqlite`, `diff_*.md`

**Risk Assessment**: LOW (architecture proven, endpoints verified) 🔥

### Sprint 2 (Sep 8–Sep 19)

* Centros + Sectores/Comités drivers; edges `centro_ec`, `ec_sector`
* JSON bundles; FastAPI endpoints; Next.js finder + 2 visualizations
* Daily probe workflow; release packaging
  **Deliverables:** JSON bundles, FastAPI app, basic UI, GH workflows

### RC (Sep 22–Sep 26)

* Perf tuning; resilience (retries/backoff, timeouts), docs/runbook, acceptance test
  **Deliverables:** `v0.2.0-rc.1`, runbook, green probe for 3 days

### GA (Sep 29–Oct 3)

* Final validations; announce; handover/KT; backlog triage
  **Deliverables:** `v0.2.0`, KT deck, post‑launch plan

---

## 10) Testing Matrix

| Area                              | Unit | Integration | E2E |
| --------------------------------- | ---- | ----------- | --- |
| Regex/normalizers                 | ✓    |             |     |
| Drivers parse (HTML/XHR fixtures) |      | ✓           |     |
| Pagination/modals                 |      | ✓           |     |
| Harvest smoke (1 page)            |      |             | ✓   |
| API responses                     | ✓    | ✓           |     |
| UI pages render (ISR)             |      | ✓           |     |

Coverage target ≥85% in parsing/normalization; CI must pass on PRs.

---

## 11) Ops & Runbook (summary)

* **Schedules**: Weekly full harvest (Mon 07:00 MX), Daily probe (08:00 MX)
* **Alerts**: Slack webhook on failure or material diffs
* **Artifacts**: keep 12 months; rotate older; sign releases (optional)
* **On‑call**: Data Eng primary; DevOps backup during RC/GA week

---

## 12) Definition of Done (DoD)

* Code typed + documented; tests written and passing; selectors centralized
* QA expectations pass locally and in CI; artifacts produced; diff reviewed
* Docs updated (README, Spec v2, CrawlMap, Runbook); dashboards show KPIs

---

## 13) Post‑Launch (30/60/90)

**+30 days:** Improve UI viz set; API pagination; bundle compression; CDN publish
**+60 days:** Add OC/ECE benchmarking dashboard; sector insights; stability SLOs
**+90 days:** Public data release cadence; lightweight community docs; optional Kaggle/DataHub mirrors

---

## 14) Immediate next 48 hours

1. Run Sprint 0 tasks; produce CrawlMap + registry files
2. Create repo skeleton (folders, CLI, workflows)
3. Book 30‑min demo slot for Aug 23 to review crawl map + selectors

---

**End of Roadmap**
