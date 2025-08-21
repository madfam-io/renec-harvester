# Sprint 1 Implementation Plan

**Project**: RENEC Harvester v02  
**Sprint**: Sprint 1  
**Duration**: August 25 - September 5, 2025 (2 weeks)  
**Status**: 🚀 **INITIATED**

---

## 🎯 Sprint 1 Objectives

Based on the ROADMAP and successful Sprint 0 completion, Sprint 1 focuses on **core data extraction and storage** with the following key deliverables:

1. **EC Standards Driver** - Complete extraction with detail pages
2. **Certificadores Driver** - ECE/OC extraction with modal data
3. **Database Schema** - PostgreSQL models and relationships
4. **Data Validation** - Quality assurance pipeline
5. **Export Capabilities** - CSV and database outputs

## 📅 Sprint Timeline

### Week 1: Core Extraction (Aug 25-29)
- **Mon-Tue**: EC Standards driver implementation
- **Wed-Thu**: Certificadores driver with modal handling
- **Fri**: Database schema setup and testing

### Week 2: Integration & QA (Sep 1-5)
- **Mon**: Data validation pipeline
- **Tue-Wed**: Diff engine implementation
- **Thu**: CSV/JSON export functionality
- **Fri**: Integration testing and CI setup

## 🏗️ Technical Implementation Plan

### 1. EC Standards Driver (`src/drivers/ec_driver.py`)

**Objectives**:
- Extract all EC standards from discovered endpoints
- Parse detail pages for complete metadata
- Handle pagination and dynamic content
- Extract sector and committee relationships

**Key Endpoints**:
- `/controlador.do?comp=ESLACT` - Active standards
- `/controlador.do?comp=ESLINACT` - Inactive standards  
- `/controlador.do?comp=ESLHIST` - Historical standards
- `/controlador.do?comp=EC&ec={code}` - Detail pages

**Data Fields**:
```python
class ECStandard:
    ec_clave: str          # EC0001 format
    titulo: str            # Standard title
    version: str           # Version number
    vigente: bool          # Active status
    sector_id: str         # Sector reference
    comite_id: str         # Committee reference
    descripcion: str       # Full description
    competencias: List[str] # Competency list
    nivel: str             # Competency level
    duracion_horas: int    # Duration in hours
    tipo_norma: str        # Standard type
    fecha_publicacion: date # Publication date
    fecha_vigencia: date   # Validity date
    renec_url: str         # Source URL
```

### 2. Certificadores Driver (`src/drivers/certificadores_driver.py`)

**Objectives**:
- Extract ECE and OC entities
- Handle JavaScript-rendered modals
- Extract contact information
- Map EC standard relationships

**Key Features**:
- Modal detection and extraction
- Contact data normalization
- State/municipality parsing
- Accreditation relationship mapping

**Data Fields**:
```python
class Certificador:
    cert_id: str           # Unique identifier
    tipo: str              # ECE or OC
    nombre_legal: str      # Legal name
    siglas: str            # Abbreviation
    estatus: str           # Active/Inactive
    domicilio_texto: str   # Full address
    estado: str            # State name
    estado_inegi: str      # INEGI code
    municipio: str         # Municipality
    cp: str                # Postal code
    telefono: str          # Phone (normalized)
    correo: str            # Email
    sitio_web: str         # Website
    estandares_acreditados: List[str]  # EC codes
```

### 3. Database Schema (`src/models/`)

**PostgreSQL Schema Design**:

```sql
-- Core entities
CREATE TABLE ec_standards (
    id SERIAL PRIMARY KEY,
    ec_clave VARCHAR(10) UNIQUE NOT NULL,
    titulo TEXT NOT NULL,
    version VARCHAR(10),
    vigente BOOLEAN DEFAULT true,
    sector_id INTEGER,
    comite_id INTEGER,
    descripcion TEXT,
    competencias JSONB,
    nivel VARCHAR(50),
    duracion_horas INTEGER,
    tipo_norma VARCHAR(50),
    fecha_publicacion DATE,
    fecha_vigencia DATE,
    renec_url TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    content_hash VARCHAR(64)
);

CREATE TABLE certificadores (
    id SERIAL PRIMARY KEY,
    cert_id VARCHAR(50) UNIQUE NOT NULL,
    tipo VARCHAR(3) CHECK (tipo IN ('ECE', 'OC')),
    nombre_legal TEXT NOT NULL,
    siglas VARCHAR(50),
    estatus VARCHAR(20),
    domicilio_texto TEXT,
    estado VARCHAR(50),
    estado_inegi CHAR(2),
    municipio VARCHAR(100),
    cp VARCHAR(5),
    telefono VARCHAR(20),
    correo VARCHAR(100),
    sitio_web VARCHAR(200),
    src_url TEXT NOT NULL,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    row_hash VARCHAR(64)
);

-- Relationships
CREATE TABLE ece_ec (
    id SERIAL PRIMARY KEY,
    cert_id VARCHAR(50) REFERENCES certificadores(cert_id),
    ec_clave VARCHAR(10) REFERENCES ec_standards(ec_clave),
    acreditado_desde DATE,
    run_id VARCHAR(50),
    UNIQUE(cert_id, ec_clave)
);

-- Indexes for performance
CREATE INDEX idx_ec_standards_sector ON ec_standards(sector_id);
CREATE INDEX idx_ec_standards_vigente ON ec_standards(vigente);
CREATE INDEX idx_certificadores_tipo ON certificadores(tipo);
CREATE INDEX idx_certificadores_estado ON certificadores(estado_inegi);
```

### 4. Data Validation Pipeline (`src/qa/validator.py`)

**Validation Rules**:
```python
class ECValidator:
    def validate_ec_code(self, code: str) -> bool:
        """EC code must match EC\d{4} pattern"""
        return bool(re.match(r'^EC\d{4}$', code))
    
    def validate_completeness(self, record: dict) -> ValidationResult:
        """Check required fields are present"""
        required = ['ec_clave', 'titulo', 'renec_url']
        missing = [f for f in required if not record.get(f)]
        return ValidationResult(
            valid=len(missing) == 0,
            errors=missing,
            warnings=[]
        )

class CertificadorValidator:
    def validate_phone(self, phone: str) -> str:
        """Normalize Mexican phone numbers"""
        # Remove non-digits, add country code
        clean = re.sub(r'\D', '', phone)
        if len(clean) == 10:
            return f"+52{clean}"
        return phone
    
    def validate_state(self, state: str) -> tuple[str, str]:
        """Map state name to INEGI code"""
        # Use state mapping table
        return normalize_state(state)
```

### 5. Diff Engine (`src/qa/diff_engine.py`)

**Change Detection**:
```python
class DiffEngine:
    def compute_changes(self, 
                       current_run: str, 
                       previous_run: str) -> DiffReport:
        """Compare two harvest runs"""
        
        # New records
        new_records = current - previous
        
        # Removed records  
        removed_records = previous - current
        
        # Modified records (content hash changed)
        modified = self.detect_modifications(current, previous)
        
        return DiffReport(
            run_id=current_run,
            compared_to=previous_run,
            new_count=len(new_records),
            removed_count=len(removed_records),
            modified_count=len(modified),
            details=self.generate_details(new, removed, modified)
        )
```

## 🔧 Development Tasks

### High Priority Tasks

1. **EC Standards Driver** (2 days)
   - Implement pagination handling
   - Parse detail pages
   - Extract all metadata fields
   - Handle edge cases

2. **Certificadores Driver** (2 days)  
   - Modal detection and extraction
   - Contact normalization
   - Relationship mapping
   - Error handling

3. **Database Schema** (1 day)
   - Create migrations
   - Setup models
   - Test relationships
   - Performance optimization

### Medium Priority Tasks

4. **Data Validation** (1 day)
   - Implement validators
   - Create test cases
   - Generate reports
   - Handle exceptions

5. **Diff Engine** (1.5 days)
   - Change detection logic
   - Report generation
   - Performance optimization
   - Testing

6. **Export Functions** (1 day)
   - CSV generation
   - Database dumps
   - Metadata inclusion
   - Compression

### Low Priority Tasks

7. **CI/CD Setup** (0.5 days)
   - GitHub Actions config
   - Smoke tests
   - Automated validation
   - Deployment pipeline

## 📊 Success Metrics

### Coverage Targets
- **EC Standards**: ≥99% of all standards
- **Certificadores**: ≥95% of ECE/OC entities
- **Relationships**: ≥90% of EC-ECE mappings
- **Data Quality**: <1% validation errors

### Performance Targets
- **Extraction Speed**: 50+ pages/minute
- **Validation Speed**: 1000+ records/second
- **Export Time**: <30 seconds for full dataset
- **Memory Usage**: <2GB for full harvest

## 🧪 Testing Strategy

### Unit Tests
```python
# test_ec_driver.py
def test_ec_code_extraction():
    """Test EC code parsing from HTML"""
    html = '<div class="ec-code">EC0221</div>'
    result = extract_ec_code(html)
    assert result == "EC0221"

def test_pagination_detection():
    """Test pagination link discovery"""
    # Test multiple page scenarios
```

### Integration Tests
```python
# test_full_pipeline.py
def test_ec_extraction_pipeline():
    """Test complete EC extraction flow"""
    # 1. Crawl EC listing page
    # 2. Extract EC codes
    # 3. Fetch detail pages
    # 4. Validate data
    # 5. Store in database
    # 6. Export to CSV
```

## 🚦 Quality Gates

### Sprint 1 Exit Criteria
- [ ] All EC standards extracted and validated
- [ ] All Certificadores with modal data extracted
- [ ] Database schema implemented and tested
- [ ] Validation pipeline catching >95% of errors
- [ ] Diff engine detecting all changes
- [ ] CSV exports passing QA checks
- [ ] CI pipeline running smoke tests
- [ ] Documentation updated

## 📝 Daily Standup Template

```markdown
### Date: [Date]

**Yesterday**:
- Completed: [tasks]
- Blockers: [issues]

**Today**:
- Working on: [tasks]
- Goal: [specific outcomes]

**Metrics**:
- Records extracted: X
- Validation errors: Y
- Test coverage: Z%
```

## 🎯 Risk Management

### Identified Risks
1. **Modal extraction complexity** - Mitigation: Playwright automation
2. **Data quality issues** - Mitigation: Comprehensive validation
3. **Performance bottlenecks** - Mitigation: Concurrent processing
4. **Schema changes** - Mitigation: Flexible parsing

### Contingency Plans
- If modal extraction fails: Fallback to API discovery
- If performance is slow: Increase concurrency
- If data quality is poor: Enhanced validation rules
- If deadlines slip: Prioritize core features

## 🏁 Sprint 1 Deliverables

### Week 1 Deliverables
- ✅ EC Standards driver implementation
- ✅ Certificadores driver with modals
- ✅ Database schema and migrations
- ✅ Basic validation framework

### Week 2 Deliverables  
- ✅ Complete validation pipeline
- ✅ Diff engine and reporting
- ✅ CSV/JSON export functions
- ✅ CI/CD smoke tests

### Final Artifacts
- `ec.csv` - Complete EC standards dataset
- `certificadores.csv` - All ECE/OC entities
- `ece_ec.csv` - Relationship mappings
- `renec_v2.sqlite` - Populated database
- `diff_YYYYMMDD.md` - Change report
- `validation_report.json` - Quality metrics

---

**Sprint 1 is officially initiated!** 🚀

Let's build the core data extraction engine that will power the RENEC Harvester system.