# RENEC Harvester - Next Steps & Implementation Plan

**Updated**: August 21, 2025  
**Current Status**: ✅ Sprint 0 Complete  
**Next Phase**: 🚀 Sprint 1 Implementation  

---

## 🎯 Immediate Priorities (Next 48 Hours)

### 1. Sprint 1 Kickoff (Aug 25, 2025)
- [ ] **Review Sprint 0 achievements** with stakeholders
- [ ] **Plan Sprint 1 development tasks** and resource allocation
- [ ] **Set up development environment** for enhanced data extraction
- [ ] **Define acceptance criteria** for Sprint 1 deliverables

### 2. Technical Deep Dive Preparation
- [ ] **Analyze discovered RENEC components** for data extraction patterns
- [ ] **Design PostgreSQL schema** based on component relationships
- [ ] **Plan component driver architecture** for scalable extraction
- [ ] **Set up monitoring and logging** infrastructure

---

## 🔧 Sprint 1 Implementation Roadmap (Aug 25 - Sep 5)

### Week 1: Foundation & Core Drivers (Aug 25-29)

#### Day 1-2: Database Infrastructure
**Priority: HIGH**
- [ ] **Implement PostgreSQL models** with SQLAlchemy ORM
  - `ECStandard`, `Certificador`, `Centro`, `Sector`, `Comite` entities
  - Relationship tables: `ece_ec`, `centro_ec`, `ec_sector`
  - Temporal tracking: `first_seen`, `last_seen`, `run_id`
- [ ] **Set up Alembic migrations** for schema versioning
- [ ] **Create database initialization** scripts and seed data
- [ ] **Test database operations** with sample data

#### Day 3-4: EC Standards Driver
**Priority: HIGH**
- [ ] **Implement EC standards extraction** from discovered endpoints:
  - `ESLACT` (Active Standards)
  - `ESLNORMTEC` (Technical Standards) 
  - `ESLHIST` (Historical Standards)
  - `ECNew` (New Standards)
- [ ] **Build detail page parsing** for individual EC records
- [ ] **Extract metadata**: titles, codes, sectors, publication dates
- [ ] **Implement pagination handling** for complete coverage

#### Day 5: Certificadores Driver Foundation
**Priority: HIGH** 
- [ ] **Start ECE/OC component driver** development
- [ ] **Research modal interaction patterns** for contact/standards data
- [ ] **Design data extraction workflow** for certificador entities
- [ ] **Test basic entity extraction** from known endpoints

### Week 2: Integration & Quality (Sep 1-5)

#### Day 1-2: Certificadores Completion
**Priority: HIGH**
- [ ] **Complete ECE/OC data extraction** with modal handling
- [ ] **Extract contact information**: phone, email, address, websites
- [ ] **Build ECE-EC relationship mapping** for accreditation data
- [ ] **Implement certificador detail pages** parsing

#### Day 3-4: Data Pipeline & Validation
**Priority: MEDIUM**
- [ ] **Create validation pipeline** for extracted data
  - EC code regex validation (`^EC\d{4}$`)
  - State name → INEGI code mapping
  - Contact information normalization
- [ ] **Implement deduplication logic** for entities and relationships
- [ ] **Build diff engine foundation** for change detection
- [ ] **Set up data quality metrics** and reporting

#### Day 5: Export & CI Integration  
**Priority: MEDIUM**
- [ ] **Implement CSV export functionality** for all entity types
- [ ] **Create JSON export pipeline** for API consumption
- [ ] **Set up CI smoke tests** with limited page crawling
- [ ] **Generate first complete dataset** artifacts

---

## 🎯 Sprint 1 Success Criteria

### Functional Requirements
- [ ] **EC Standards Dataset**: Complete extraction of EC standards with metadata
- [ ] **Certificadores Dataset**: ECE/OC entities with contact and accreditation info
- [ ] **Relationship Data**: ECE-EC mappings with temporal tracking
- [ ] **Data Validation**: ≥95% EC code validation pass rate
- [ ] **Export Formats**: CSV, JSON, and SQLite database outputs

### Performance Targets
- [ ] **Extraction Speed**: ≤20 minutes for full harvest run
- [ ] **Data Quality**: ≥99% coverage vs manual UI verification
- [ ] **Error Rate**: ≤1% failed extractions per component
- [ ] **CI Integration**: Green smoke tests with sample data

### Deliverable Artifacts
```
artifacts/runs/sprint1_YYYYMMDD/
├── ec.csv                     # EC Standards dataset
├── certificadores.csv         # ECE/OC entities
├── ece_ec.csv                 # Relationships
├── renec_v2.sqlite           # Full database
├── diff_YYYYMMDD.md          # Change report
├── validation_report.json    # Quality metrics
└── logs/                     # Execution logs
```

---

## 🔍 Detailed Technical Tasks

### Database Schema Implementation
```python
# Priority models to implement
class ECStandard(Base):
    id = Column(UUID, primary_key=True)
    ec_clave = Column(String(10), unique=True, nullable=False)
    titulo = Column(Text)
    sector_id = Column(String(50))
    vigente = Column(Boolean, default=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class Certificador(Base):
    id = Column(UUID, primary_key=True) 
    tipo = Column(Enum('ECE', 'OC'), nullable=False)
    nombre_legal = Column(Text, nullable=False)
    estado_inegi = Column(String(2))  # INEGI state code
    # ... additional fields
```

### Component Driver Architecture
```python
# Driver interface pattern
class ComponentDriver(ABC):
    @abstractmethod
    def discover_urls(self) -> List[str]:
        """Discover URLs for this component type"""
        
    @abstractmethod
    def extract_entities(self, response) -> List[Dict]:
        """Extract entities from response"""
        
    @abstractmethod
    def extract_relationships(self, response) -> List[Dict]:
        """Extract relationships from response"""
```

### Validation Pipeline Design
```python
# Validation framework structure
def validate_ec_code(code: str) -> ValidationResult:
    """Validate EC code format"""
    
def normalize_contact_info(contact: Dict) -> Dict:
    """Normalize phone/email/address data"""
    
def map_state_to_inegi(state_name: str) -> str:
    """Convert state name to INEGI code"""
```

---

## 🚦 Risk Management & Mitigation

### High Risk Items
1. **Modal Interaction Complexity**: ECE/OC contact data may require complex browser automation
   - **Mitigation**: Start with simple DOM parsing, add Playwright gradually
   - **Fallback**: Focus on publicly visible data first

2. **Data Volume Performance**: Large datasets may impact extraction speed
   - **Mitigation**: Implement pagination and chunked processing
   - **Monitoring**: Track extraction rates and optimize bottlenecks

3. **Site Structure Changes**: RENEC endpoints may change during development
   - **Mitigation**: Robust error handling and fallback patterns
   - **Monitoring**: Daily endpoint health checks

### Medium Risk Items
1. **State Name Normalization**: Complex address parsing requirements
   - **Mitigation**: Build comprehensive state mapping table
   - **Testing**: Validate against known address datasets

2. **Relationship Data Quality**: ECE-EC mappings may be incomplete
   - **Mitigation**: Multiple data source validation
   - **Quality Gates**: Coverage percentage thresholds

---

## 📊 Monitoring & Success Metrics

### Development KPIs
- **Daily Progress**: Tasks completed vs planned
- **Code Quality**: Test coverage ≥85% for new components
- **Data Quality**: Validation pass rates by component type
- **Performance**: Extraction speed trends over time

### Sprint 1 Gates
- [ ] **Week 1 Gate**: Database models and EC driver functional
- [ ] **Week 2 Gate**: Certificadores driver and validation pipeline complete
- [ ] **Sprint End Gate**: All deliverables produced and validated

### Quality Checkpoints
```bash
# Daily validation commands
make test                    # Run full test suite
make validate-data           # Check data quality metrics  
make lint                    # Code quality verification
python -m src.cli diff       # Generate change reports
```

---

## 🎯 Post-Sprint 1 Preview

### Sprint 2 Preparation (Sep 8-19)
- **Centros driver**: Evaluation centers data extraction
- **Sectores/Comités**: Taxonomy and classification data
- **FastAPI development**: Read-only API implementation
- **Next.js UI foundation**: Basic finder and visualization

### Long-term Vision (Oct 3, 2025)
- **Production deployment**: Automated weekly harvests
- **Public API launch**: Read-only access for researchers
- **Data visualization**: Interactive dashboards and maps
- **Community engagement**: Open data publication

---

## 🤝 Team Coordination

### Sprint 1 Team Structure
- **Product Owner**: Aldo Ruiz Luna (final approvals)
- **Tech Lead**: Senior Data Engineer (architecture decisions)
- **Backend Developer**: Data extraction and pipeline implementation
- **QA Engineer**: Validation framework and testing
- **DevOps**: CI/CD and infrastructure support

### Communication Cadence  
- **Daily standups**: 15 minutes (async updates preferred)
- **Mid-sprint check**: Wednesday demo and blockers review
- **Sprint review**: Friday demo with stakeholders
- **Retrospective**: Sprint end lessons learned and improvements

---

## 💡 Implementation Tips

### Development Best Practices
1. **Start simple**: Basic DOM parsing before complex browser automation
2. **Test continuously**: Validate data quality at each step
3. **Document discoveries**: Update selectors and endpoints as you learn
4. **Monitor performance**: Track extraction speeds and optimize bottlenecks
5. **Handle errors gracefully**: Robust retry and fallback mechanisms

### Code Organization
```
src/
├── drivers/
│   ├── ec_standards.py       # EC standards extraction
│   ├── certificadores.py     # ECE/OC extraction  
│   └── base_driver.py        # Common functionality
├── models/
│   ├── entities.py           # SQLAlchemy models
│   └── relationships.py      # Association tables
├── validation/
│   ├── validators.py         # Data validation logic
│   └── normalizers.py        # Data normalization
└── exports/
    ├── csv_exporter.py       # CSV generation
    └── json_exporter.py      # JSON bundle creation
```

---

**Ready to start Sprint 1!** 🚀  

*Next update: Sprint 1 completion (September 5, 2025)*