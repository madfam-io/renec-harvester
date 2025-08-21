# Developer Guide

## Getting Started

This guide provides comprehensive information for developers working on the RENEC Harvester project.

## Development Environment Setup

### Prerequisites

1. **Python 3.8+** with pip and virtualenv
2. **Node.js 18+** and npm
3. **Docker** and Docker Compose
4. **Git** for version control
5. **PostgreSQL client** (psql)
6. **Redis client** (redis-cli)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/renec-harvester.git
cd renec-harvester

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Playwright browsers
playwright install --with-deps

# Start services with Docker
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Install UI dependencies
cd ui && npm install
```

## Project Structure

```
renec-harvester/
├── src/                    # Source code
│   ├── api/               # FastAPI application
│   ├── cli/               # CLI commands
│   ├── discovery/         # Scrapy spiders
│   ├── drivers/           # Entity-specific drivers
│   ├── models/            # Database models
│   ├── optimization/      # Performance modules
│   └── export/            # Export functionality
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── ui/                     # Next.js frontend
├── k8s/                    # Kubernetes configs
├── terraform/              # Infrastructure as code
└── docs/                   # Documentation
```

## Core Components

### 1. Spider Development

#### Creating a New Spider

```python
# src/discovery/spiders/custom_spider.py
import scrapy
from scrapy_playwright.page import PageMethod
from src.discovery.items import RenecItem

class CustomSpider(scrapy.Spider):
    name = 'custom'
    
    def start_requests(self):
        yield scrapy.Request(
            url='https://example.com',
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_selector', 'div.content')
                ]
            }
        )
    
    def parse(self, response):
        # Extract data
        item = RenecItem()
        item['type'] = 'custom'
        item['data'] = response.css('div.content::text').get()
        yield item
```

#### Spider Best Practices

1. **Rate Limiting**: Always respect robots.txt and implement delays
2. **Error Handling**: Use try-except blocks and log errors
3. **Retries**: Configure automatic retries with backoff
4. **Caching**: Enable HTTP cache for development

### 2. Driver Development

Drivers handle entity-specific extraction logic:

```python
# src/drivers/custom_driver.py
from src.drivers.base_driver import BaseDriver
from typing import Generator, Dict, Any

class CustomDriver(BaseDriver):
    """Driver for custom entity extraction."""
    
    ENDPOINTS = {
        'list': '/path/to/list',
        'detail': '/path/to/detail/{id}'
    }
    
    def parse_list(self, response) -> Generator[Dict[str, Any], None, None]:
        """Parse list page."""
        for item in response.css('div.item'):
            yield {
                'id': item.css('::attr(data-id)').get(),
                'name': item.css('h3::text').get(),
                'url': self.build_detail_url(item.css('::attr(data-id)').get())
            }
    
    def parse_detail(self, response) -> Dict[str, Any]:
        """Parse detail page."""
        return {
            'id': response.meta['item_id'],
            'name': response.css('h1::text').get(),
            'description': response.css('div.description::text').get(),
            'metadata': self.extract_metadata(response)
        }
```

### 3. Model Development

#### Creating Database Models

```python
# src/models/custom.py
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from src.models.base import Base

class CustomEntity(Base):
    __tablename__ = 'custom_entities'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # related_items = relationship('RelatedItem', back_populates='custom_entity')
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'name': self.name,
            'description': self.description,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
```

#### Creating Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add custom entity table"

# Review and edit migration
nano alembic/versions/xxx_add_custom_entity_table.py

# Apply migration
alembic upgrade head
```

### 4. API Development

#### Creating API Endpoints

```python
# src/api/routers/custom.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.api.dependencies import get_session
from src.models.custom import CustomEntity
from src.api.schemas.custom import CustomSchema, CustomDetailSchema

router = APIRouter(prefix="/custom", tags=["custom"])

@router.get("/", response_model=List[CustomSchema])
async def list_custom_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """List custom entities with pagination and search."""
    query = db.query(CustomEntity)
    
    if search:
        query = query.filter(CustomEntity.name.ilike(f"%{search}%"))
    
    entities = query.offset(skip).limit(limit).all()
    return entities

@router.get("/{entity_id}", response_model=CustomDetailSchema)
async def get_custom_entity(
    entity_id: str,
    db: Session = Depends(get_session)
):
    """Get custom entity details."""
    entity = db.query(CustomEntity).filter(
        CustomEntity.external_id == entity_id
    ).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity
```

#### API Schemas

```python
# src/api/schemas/custom.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class CustomSchema(BaseModel):
    external_id: str
    name: str
    description: Optional[str] = None
    last_seen: datetime
    
    class Config:
        orm_mode = True

class CustomDetailSchema(CustomSchema):
    first_seen: datetime
    metadata: Optional[dict] = None
    related_items: List[dict] = []
```

### 5. Testing

#### Unit Tests

```python
# tests/unit/test_custom_driver.py
import pytest
from unittest.mock import Mock
from src.drivers.custom_driver import CustomDriver

class TestCustomDriver:
    @pytest.fixture
    def driver(self):
        return CustomDriver()
    
    def test_parse_list(self, driver):
        # Mock response
        mock_response = Mock()
        mock_response.css.return_value = [
            Mock(css=lambda s: Mock(get=lambda: 'item1' if 'data-id' in s else 'Item 1'))
        ]
        
        # Test parsing
        results = list(driver.parse_list(mock_response))
        assert len(results) == 1
        assert results[0]['id'] == 'item1'
        assert results[0]['name'] == 'Item 1'
```

#### Integration Tests

```python
# tests/integration/test_custom_workflow.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.custom import CustomEntity

class TestCustomWorkflow:
    @pytest.fixture
    def db_session(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
    
    def test_entity_creation(self, db_session):
        # Create entity
        entity = CustomEntity(
            external_id='test1',
            name='Test Entity',
            description='Test description'
        )
        db_session.add(entity)
        db_session.commit()
        
        # Verify
        retrieved = db_session.query(CustomEntity).filter_by(
            external_id='test1'
        ).first()
        assert retrieved is not None
        assert retrieved.name == 'Test Entity'
```

## Development Workflows

### 1. Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-entity-type

# 2. Implement feature
# - Create model
# - Create driver
# - Add API endpoints
# - Write tests

# 3. Run tests
pytest tests/unit/test_new_feature.py
pytest tests/integration/

# 4. Check code quality
black src tests
ruff check src tests
mypy src

# 5. Commit and push
git add .
git commit -m "feat: Add new entity type support"
git push origin feature/new-entity-type
```

### 2. Debugging

#### Local Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use IPython for interactive debugging
import IPython; IPython.embed()

# Use debugger
import pdb; pdb.set_trace()
```

#### Spider Debugging

```bash
# Run spider with debug settings
scrapy crawl renec -s LOG_LEVEL=DEBUG -s HTTPCACHE_ENABLED=False

# Use Scrapy shell
scrapy shell "https://conocer.gob.mx/RENEC/controlador.do?comp=IR"
```

### 3. Performance Optimization

#### Profiling

```python
# Use cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
expensive_operation()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

#### Database Query Optimization

```python
# Use query explanation
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("EXPLAIN ANALYZE SELECT ..."))
    for row in result:
        print(row)
```

## Best Practices

### 1. Code Style

- Follow PEP 8 conventions
- Use type hints for all functions
- Write docstrings for all public methods
- Keep functions small and focused
- Use meaningful variable names

### 2. Error Handling

```python
# Good error handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    # Handle gracefully
    return default_value
except Exception as e:
    logger.exception("Unexpected error")
    raise
finally:
    # Cleanup
    cleanup_resources()
```

### 3. Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General information")
logger.warning("Warning about potential issues")
logger.error("Error that needs attention")
logger.critical("Critical error that stops execution")
```

### 4. Configuration

```python
# Use environment variables
import os
from typing import Optional

class Config:
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://localhost/renec')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    API_KEY: Optional[str] = os.getenv('API_KEY')
    
    # Validation
    def validate(self):
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
```

### 5. Security

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Validate all user input
- Use parameterized queries
- Implement rate limiting
- Keep dependencies updated

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        playwright install --with-deps
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=html
    
    - name: Check code quality
      run: |
        black --check src tests
        ruff check src tests
        mypy src
```

## Deployment

### Building Docker Images

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: renec-harvester-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: renec-harvester-api
  template:
    metadata:
      labels:
        app: renec-harvester-api
    spec:
      containers:
      - name: api
        image: renec-harvester:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: renec-secrets
              key: database-url
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH includes project root
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps
   
   # Check connection string
   psql $DATABASE_URL
   ```

3. **Spider Not Finding Elements**
   ```python
   # Use Scrapy shell to debug selectors
   scrapy shell "URL"
   >>> response.css('selector').get()
   ```

4. **Memory Issues**
   ```python
   # Use generators instead of lists
   def process_large_dataset():
       for item in query.yield_per(1000):
           yield process_item(item)
   ```

## Resources

- [Scrapy Documentation](https://docs.scrapy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Project Wiki](https://github.com/your-org/renec-harvester/wiki)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Commit with conventional commits
7. Push and create a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.