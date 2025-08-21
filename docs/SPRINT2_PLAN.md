# Sprint 2: Extended Entity Extraction

**Duration**: Sep 8 - Sep 19, 2025  
**Status**: IN PROGRESS (Starting early on Aug 21, 2025)

## Overview

Sprint 2 extends the data extraction capabilities to cover the remaining RENEC entities: Evaluation Centers (Centros), Sectors, and Committees (Comités). We'll also build the API layer and enhance the UI with search and visualization capabilities.

## Objectives

1. Complete extraction coverage for all RENEC entities
2. Map relationships between entities (centro-EC, EC-sector)
3. Provide API access to harvested data
4. Create user-friendly search and visualization tools
5. Implement automated daily monitoring

## Deliverables

### 1. Centros Driver (Evaluation Centers)
- **Goal**: Extract all evaluation centers with their metadata
- **Features**:
  - Center details (name, code, location)
  - Associated certificador (ECE/OC)
  - Contact information
  - Accredited EC standards
  - Geographic normalization
- **Acceptance Criteria**:
  - ≥500 centers extracted
  - Location data normalized to INEGI codes
  - Relationship with certificadores mapped

### 2. Sectores & Comités Drivers
- **Goal**: Extract sector and committee hierarchies
- **Features**:
  - Sector listings with IDs
  - Committee membership
  - Sector-committee relationships
  - EC standard associations
- **Acceptance Criteria**:
  - All sectors extracted (≥10)
  - All committees mapped (≥50)
  - Proper parent-child relationships

### 3. Relationship Mappings
- **Goal**: Create edge tables for entity relationships
- **Tables**:
  - `centro_ec`: Centers ↔ EC standards
  - `ec_sector`: EC standards ↔ Sectors
  - `ece_ec`: Already exists from Sprint 1
- **Features**:
  - Temporal tracking for relationships
  - Validation of referential integrity
  - Change detection for relationships

### 4. JSON Bundle Exports
- **Goal**: Structured JSON exports for downstream consumption
- **Features**:
  - Hierarchical JSON with relationships
  - Denormalized views for easy consumption
  - Metadata and versioning
  - Compressed bundles
- **Formats**:
  - `entities.json`: All entities with relationships
  - `graph.json`: Node-edge format for visualization
  - `denormalized.json`: Flattened view with embedded relations

### 5. FastAPI Endpoints
- **Goal**: RESTful API for data access
- **Endpoints**:
  ```
  GET /api/v1/ec-standards
  GET /api/v1/ec-standards/{ec_clave}
  GET /api/v1/certificadores
  GET /api/v1/certificadores/{cert_id}
  GET /api/v1/centros
  GET /api/v1/centros/{centro_id}
  GET /api/v1/sectores
  GET /api/v1/comites
  GET /api/v1/relationships/{type}
  GET /api/v1/search
  GET /api/v1/stats
  ```
- **Features**:
  - Pagination and filtering
  - Search across entities
  - Relationship traversal
  - OpenAPI documentation
  - Response caching

### 6. Next.js UI Enhancements
- **Goal**: User-friendly interface for data exploration
- **Features**:
  - **Search/Finder**: 
    - Full-text search across all entities
    - Faceted filtering (sector, state, type)
    - Autocomplete suggestions
  - **Visualizations**:
    - Geographic map of centers/certificadores
    - Network graph of EC-certificador relationships
    - Sector hierarchy tree view
  - **Data Tables**:
    - Sortable, filterable grids
    - Export functionality
    - Detail views with relationships

### 7. Daily Probe Workflow
- **Goal**: Automated monitoring for data freshness
- **Features**:
  - Daily crawl of sample pages
  - Change detection alerts
  - Health check dashboard
  - Slack/email notifications
- **GitHub Actions**:
  - Scheduled daily at 6 AM CST
  - Probe 10 random entities
  - Compare with baseline
  - Report changes

## Technical Approach

### Driver Architecture
```python
# src/drivers/centros_driver.py
class CentrosDriver(BaseDriver):
    ENDPOINTS = {
        'list': '/RENEC/controlador.do?comp=CENTROS',
        'detail': '/RENEC/controlador.do?comp=CENTRO&id={}'
    }
    
    def parse_centro(self, response):
        # Extract center details
        # Map to certificador
        # Extract EC standards
        pass
```

### API Structure
```python
# src/api/routers/ec_standards.py
@router.get("/ec-standards")
async def list_ec_standards(
    skip: int = 0,
    limit: int = 100,
    vigente: Optional[bool] = None,
    sector_id: Optional[int] = None
):
    # Implement pagination and filtering
    pass
```

### UI Components
```typescript
// ui/src/components/SearchFinder.tsx
export function SearchFinder() {
  // Multi-entity search
  // Faceted filtering
  // Real-time results
}

// ui/src/components/NetworkGraph.tsx
export function NetworkGraph() {
  // D3.js or vis.js integration
  // Interactive node exploration
  // Relationship highlighting
}
```

## Implementation Schedule

### Week 1 (Sep 8-12)
- Day 1-2: Centros driver implementation
- Day 3-4: Sectores & Comités drivers
- Day 5: Relationship mapping and validation

### Week 2 (Sep 15-19)
- Day 1-2: FastAPI implementation
- Day 3-4: UI enhancements
- Day 5: Daily probe setup and testing

## Dependencies

- **New Libraries**:
  - `fastapi[all]`: API framework
  - `uvicorn`: ASGI server
  - `d3` or `vis-network`: Graph visualization
  - `react-leaflet`: Map component
  - `tanstack-query`: API state management

## Risk Mitigation

1. **Centro-Certificador Mapping**: May require fuzzy matching
   - Mitigation: Build mapping table with manual corrections
   
2. **API Performance**: Large datasets may be slow
   - Mitigation: Implement caching, pagination, and indexes
   
3. **UI Complexity**: Visualizations may be resource-intensive
   - Mitigation: Lazy loading, virtualization, progressive enhancement

## Success Metrics

- **Coverage**: 100% of centros, sectores, comités extracted
- **API Performance**: p95 latency <200ms
- **UI Responsiveness**: Search results <500ms
- **Daily Probe**: 95% success rate
- **Documentation**: OpenAPI spec complete

## Next Steps

1. Review and finalize driver endpoints
2. Set up FastAPI project structure
3. Design API response schemas
4. Create UI mockups for new features
5. Configure GitHub Actions for daily probes

---
*Sprint 2 plan created on August 21, 2025*  
*Starting 18 days early to maintain momentum* 🚀