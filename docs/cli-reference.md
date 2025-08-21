# RENEC Harvester CLI Reference

## 🖥️ Command Overview

The RENEC Harvester CLI provides comprehensive command-line access to all harvesting operations. The CLI is built with Typer and provides rich output formatting and interactive features.

```bash
python -m src.cli [COMMAND] [OPTIONS]
```

## 📋 Available Commands

### Core Commands
- **`crawl`** - Site crawling and mapping
- **`harvest`** - Data extraction operations  
- **`validate`** - Data validation and quality checks
- **`db`** - Database management

### Utility Commands
- **`info`** - Show system information
- **`status`** - Check system status and health
- **`version`** - Display version information
- **`init`** - Initialize harvester environment

## 🕷️ Crawl Command

Discover and map the RENEC site structure.

### Usage
```bash
python -m src.cli crawl [OPTIONS]
```

### Options
- `--mode` - Crawling mode (`discover`, `map`, `full`) [default: `discover`]
- `--max-depth INTEGER` - Maximum crawl depth [default: 5]
- `--max-pages INTEGER` - Limit number of pages to crawl
- `--output PATH` - Output file for crawl results [default: `artifacts/crawl_map.json`]
- `--headless/--headful` - Browser visibility [default: headless]
- `--respect-robots/--ignore-robots` - Respect robots.txt [default: respect]

### Examples
```bash
# Basic site discovery
python -m src.cli crawl

# Deep crawl with visible browser
python -m src.cli crawl --max-depth 8 --headful

# Limited crawl for testing
python -m src.cli crawl --max-pages 50 --output test_crawl.json

# Full site mapping
python -m src.cli crawl --mode full --max-depth 10
```

### Output
```json
{
  "crawl_id": "crawl_20240821_101530",
  "start_time": "2024-08-21T10:15:30Z",
  "end_time": "2024-08-21T10:45:12Z",
  "total_pages": 1247,
  "components_found": 13,
  "endpoints": {
    "ec_standards": "https://conocer.gob.mx/RENEC/controlador.do?comp=EC",
    "certificadores": "https://conocer.gob.mx/RENEC/controlador.do?comp=CERT",
    "evaluation_centers": "https://conocer.gob.mx/RENEC/controlador.do?comp=CE"
  }
}
```

## 🌾 Harvest Command

Extract data from discovered RENEC components.

### Usage
```bash
python -m src.cli harvest [OPTIONS]
```

### Options
- `--components TEXT` - Comma-separated list of components to harvest
- `--mode` - Harvest mode (`incremental`, `full`, `refresh`) [default: `incremental`]
- `--concurrent INTEGER` - Number of concurrent workers [default: 8]
- `--delay FLOAT` - Delay between requests in seconds [default: 0.5]
- `--retry INTEGER` - Number of retry attempts [default: 3]
- `--output-format` - Output format (`json`, `csv`, `database`, `all`) [default: `all`]
- `--dry-run` - Validate operations without making changes

### Available Components
- `ec_standards` - Competency standards (EC)
- `certificadores` - Certification entities (ECE/OC)
- `evaluation_centers` - Evaluation centers
- `courses` - Training courses
- `sectors` - Industry sectors
- `committees` - Technical committees

### Examples
```bash
# Harvest all components
python -m src.cli harvest

# Harvest specific components
python -m src.cli harvest --components "ec_standards,certificadores"

# Full refresh with higher concurrency
python -m src.cli harvest --mode full --concurrent 12

# Conservative harvest with longer delays
python -m src.cli harvest --delay 1.5 --retry 5

# Dry run to test configuration
python -m src.cli harvest --dry-run --components "ec_standards"

# Export only to CSV
python -m src.cli harvest --output-format csv
```

### Output
Harvest operations produce multiple artifacts:

**Database Records**: Stored in PostgreSQL with full relationships
**CSV Exports**: Located in `artifacts/exports/`
- `ec_standards.csv`
- `certificadores.csv` 
- `evaluation_centers.csv`
- `courses.csv`
- `sectors.csv`

**JSON Bundles**: Located in `artifacts/harvests/`
- `harvest_YYYYMMDD_HHMMSS.json`

## ✅ Validate Command

Validate harvested data quality and consistency.

### Usage
```bash
python -m src.cli validate [OPTIONS]
```

### Options
- `--data-source PATH` - Path to data file or database connection
- `--rules PATH` - Custom validation rules file [default: built-in rules]
- `--output PATH` - Validation report output path
- `--format` - Report format (`json`, `html`, `text`) [default: `json`]
- `--strict` - Fail on any validation errors
- `--components TEXT` - Validate specific components only

### Validation Rules
The validator checks for:
- **Data Completeness**: Required fields present
- **Format Validation**: EC codes, phone numbers, emails
- **Consistency Checks**: Cross-references between entities
- **Quality Metrics**: Duplicate detection, data freshness
- **Coverage Analysis**: Completeness vs. expected totals

### Examples
```bash
# Validate all harvested data
python -m src.cli validate

# Validate specific harvest file
python -m src.cli validate --data-source artifacts/harvests/harvest_20240821.json

# Generate HTML report
python -m src.cli validate --format html --output validation_report.html

# Strict validation for CI/CD
python -m src.cli validate --strict --components "ec_standards"

# Custom validation rules
python -m src.cli validate --rules custom_validation_rules.yaml
```

### Sample Validation Report
```json
{
  "validation_id": "val_20240821_103045",
  "timestamp": "2024-08-21T10:30:45Z",
  "data_source": "database",
  "summary": {
    "total_records": 4765,
    "valid_records": 4623,
    "invalid_records": 142,
    "warnings": 87,
    "errors": 55
  },
  "by_component": {
    "ec_standards": {
      "total": 1250,
      "valid": 1234,
      "errors": ["Invalid EC code format: EC99999"],
      "warnings": ["Missing sector classification: EC0145"]
    }
  },
  "quality_metrics": {
    "completeness": 97.2,
    "consistency": 94.8,
    "freshness": 89.5
  }
}
```

## 🗄️ Database Command

Manage database operations and schema.

### Usage
```bash
python -m src.cli db [SUBCOMMAND] [OPTIONS]
```

### Subcommands

#### Initialize Database
```bash
python -m src.cli db init [OPTIONS]
```
- `--drop-existing` - Drop existing tables before creation
- `--sample-data` - Load sample data after initialization

#### Run Migrations
```bash
python -m src.cli db migrate [OPTIONS]
```
- `--target TEXT` - Target migration version
- `--dry-run` - Show migration plan without executing

#### Database Status
```bash
python -m src.cli db status
```

#### Backup Database
```bash
python -m src.cli db backup [OPTIONS]
```
- `--output PATH` - Backup file location
- `--compress` - Compress backup file
- `--include-data/--schema-only` - Include data or schema only

#### Restore Database
```bash
python -m src.cli db restore [OPTIONS] BACKUP_FILE
```
- `--force` - Force restore even if data exists

### Examples
```bash
# Initialize fresh database
python -m src.cli db init --drop-existing

# Run pending migrations
python -m src.cli db migrate

# Check database status
python -m src.cli db status

# Create backup
python -m src.cli db backup --output backup_20240821.sql --compress

# Restore from backup
python -m src.cli db restore backup_20240821.sql.gz --force
```

## ℹ️ Info Command

Display system information and configuration.

### Usage
```bash
python -m src.cli info [OPTIONS]
```

### Options
- `--format` - Output format (`json`, `yaml`, `table`) [default: `table`]
- `--verbose` - Include detailed system information

### Example Output
```
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component        ┃ Status                          ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python Version   │ 3.9.6                           │
│ Scrapy           │ 2.11.0                          │
│ Playwright       │ 1.40.0 (browsers installed)    │
│ PostgreSQL       │ Connected (version 16.1)        │
│ Redis            │ Connected (version 7.2.3)       │
│ System Memory    │ 16.0 GB (45% used)             │
│ Disk Space       │ 512 GB (23% used)              │
│ Last Harvest     │ 2024-08-21 08:30:15 (2h ago)   │
└──────────────────┴─────────────────────────────────┘
```

## 📊 Status Command

Check system health and current operations.

### Usage
```bash
python -m src.cli status [OPTIONS]
```

### Options
- `--watch` - Continuously monitor status (update every 5 seconds)
- `--json` - Output in JSON format
- `--services` - Check external service health only

### Example Output
```
RENEC Harvester System Status

🟢 Overall Status: HEALTHY

Core Services:
  🟢 Database: Connected (16ms latency)
  🟢 Redis: Connected (2ms latency)  
  🟢 Scrapy: Ready (3 spiders available)
  🟡 Playwright: Ready (browsers need update)

Current Operations:
  🔵 Spider Status: IDLE
  📊 Last Activity: 2024-08-21 10:15:30
  📈 Items in Database: 4,765 records

System Resources:
  💾 Memory Usage: 45% (7.2GB / 16GB)
  💿 Disk Usage: 23% (118GB / 512GB)
  🌐 Network: Connected

Recommendations:
  ⚠️  Update Playwright browsers: playwright install
  ℹ️  Schedule next harvest: Due in 3 days
```

## 🔧 Version Command

Display version information for all components.

### Usage
```bash
python -m src.cli version [OPTIONS]
```

### Options
- `--check-updates` - Check for available updates
- `--components` - Show individual component versions

### Example Output
```
RENEC Harvester v2.0.0

Component Versions:
├── Core Harvester: 2.0.0
├── CLI Interface: 2.0.0  
├── Web API: 0.1.0
├── Web UI: 0.1.0
├── Scrapy: 2.11.0
├── Playwright: 1.40.0
├── FastAPI: 0.104.1
├── Next.js: 15.5.0
└── Python: 3.9.6

Build Information:
├── Build Date: 2024-08-21
├── Git Commit: a1b2c3d4
├── Environment: development
└── Platform: darwin-arm64
```

## 🚀 Init Command

Initialize the harvester environment and configuration.

### Usage
```bash
python -m src.cli init [OPTIONS]
```

### Options
- `--interactive` - Interactive setup wizard
- `--config-template` - Generate configuration template
- `--install-deps` - Install required dependencies
- `--setup-env` - Setup environment files

### Example
```bash
# Interactive setup
python -m src.cli init --interactive

# Quick setup with defaults
python -m src.cli init --config-template --setup-env

# Full installation
python -m src.cli init --install-deps --interactive
```

## 🎛️ Global Options

These options are available for all commands:

- `--verbose, -v` - Enable verbose output
- `--quiet, -q` - Suppress output (errors only)
- `--log-level` - Set logging level (`DEBUG`, `INFO`, `WARN`, `ERROR`)
- `--config PATH` - Custom configuration file path
- `--help` - Show help message

## 📝 Configuration Files

### Main Configuration
Default location: `config.yaml`

```yaml
# Database settings
database:
  url: "postgresql://renec:password@localhost:5432/renec_harvester"
  
# Redis settings  
redis:
  url: "redis://localhost:6379/0"
  
# Spider settings
spider:
  concurrent_requests: 8
  download_delay: 0.5
  retry_times: 3
  respect_robots_txt: true
  
# Output settings
output:
  base_dir: "./artifacts"
  formats: ["json", "csv", "database"]
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/harvester.log

# Spider settings
SCRAPY_SETTINGS_MODULE=src.discovery.settings
CONCURRENT_REQUESTS=8
DOWNLOAD_DELAY=0.5
```

## 🔗 Command Chaining

Commands can be chained for complete workflows:

```bash
# Complete harvest workflow
python -m src.cli crawl && \
python -m src.cli harvest && \
python -m src.cli validate --strict

# CI/CD pipeline
python -m src.cli status --services && \
python -m src.cli harvest --dry-run && \
python -m src.cli harvest && \
python -m src.cli validate --format json --output validation.json
```

## 🏃‍♂️ Performance Tips

1. **Concurrent Processing**: Increase `--concurrent` for faster harvesting
2. **Request Delays**: Decrease `--delay` for speed, increase for politeness  
3. **Component Selection**: Use `--components` to harvest only needed data
4. **Dry Runs**: Use `--dry-run` to test configurations
5. **Output Formats**: Choose specific formats to reduce processing time

## 🐛 Debugging Options

```bash
# Debug mode with verbose logging
python -m src.cli harvest --verbose --log-level DEBUG

# Visible browser for debugging
python -m src.cli crawl --headful --max-pages 10

# Dry run with detailed output
python -m src.cli harvest --dry-run --verbose

# Single component testing
python -m src.cli harvest --components "ec_standards" --max-pages 5
```

## 📚 Examples and Recipes

### Daily Harvest Automation
```bash
#!/bin/bash
# daily_harvest.sh

# Check system status
python -m src.cli status --services || exit 1

# Run incremental harvest  
python -m src.cli harvest --mode incremental

# Validate results
python -m src.cli validate --strict

# Send notification (custom script)
./notify_completion.sh $?
```

### Quality Assurance Workflow
```bash
#!/bin/bash
# qa_workflow.sh

# Test crawl
python -m src.cli crawl --max-pages 50 --output qa_crawl.json

# Test harvest
python -m src.cli harvest --dry-run --components "ec_standards"

# Full validation
python -m src.cli validate --format html --output qa_report.html

echo "QA workflow complete. Review qa_report.html"
```

This CLI reference provides comprehensive coverage of all available commands and options in the RENEC Harvester system.