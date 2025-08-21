# RENEC Harvester Documentation

## Overview

This directory contains comprehensive documentation for the RENEC Harvester project. The documentation is organized to serve different audiences: users, developers, operators, and contributors.

## Table of Contents

### Getting Started
1. [**Installation Guide**](./installation.md) - Complete setup and configuration instructions
2. [**User Guide**](./user-guide.md) - End-user documentation for the web interface
3. [**CLI Reference**](./cli-reference.md) - Command-line interface documentation

### Technical Documentation
4. [**Architecture Overview**](./architecture.md) - System design, components, and data flow
5. [**API Reference**](./api-reference.md) - Complete REST API documentation with examples
6. [**Database Schema**](./database-schema.md) - Data models, relationships, and queries
7. [**Developer Guide**](./developer-guide.md) - Development setup, workflows, and best practices

### Operations & Deployment
8. [**Operations Guide**](./operations.md) - Production operations, monitoring, and maintenance
9. [**Deployment Guide**](./deployment-guide.md) - Deployment instructions for various environments
10. [**Performance Tuning**](./performance.md) - Optimization strategies and benchmarks

### Reference & Support
11. [**Troubleshooting**](./troubleshooting.md) - Common issues and solutions
12. [**Changelog**](./changelog.md) - Version history and release notes

## Quick Start Guides

### For Users
1. Start with the [Installation Guide](./installation.md) to set up the system
2. Read the [User Guide](./user-guide.md) to understand the web interface
3. Learn [CLI commands](./cli-reference.md) for automation

### For Developers
1. Follow the [Developer Guide](./developer-guide.md) for development setup
2. Understand the [Architecture](./architecture.md) before making changes
3. Review the [Database Schema](./database-schema.md) for data models
4. Check the [API Reference](./api-reference.md) for endpoint details

### For Operators
1. Use the [Operations Guide](./operations.md) for production management
2. Follow [Deployment Guide](./deployment-guide.md) for setup procedures
3. Apply [Performance Tuning](./performance.md) for optimization
4. Keep [Troubleshooting](./troubleshooting.md) guide handy

## Documentation Structure

```
docs/
├── README.md                    # This file - Documentation index
├── architecture.md              # System architecture and design
├── installation.md              # Installation and setup guide
├── user-guide.md               # End-user documentation
├── api-reference.md            # Complete API documentation
├── developer-guide.md          # Developer documentation
├── operations.md               # Operations and maintenance guide
├── database-schema.md          # Database structure and queries
├── performance.md              # Performance tuning guide
├── troubleshooting.md          # Common issues and solutions
├── changelog.md                # Version history
├── cli-reference.md            # CLI command reference
├── deployment-guide.md         # Deployment instructions
└── legacy/                     # Previous documentation versions
    ├── API_DOCUMENTATION.md
    ├── OPERATIONS_MANUAL.md
    └── sprint-docs/
```

## Key Features Documentation

### Web Scraping
- [Spider Architecture](./architecture.md#discovery-layer) - How spiders work
- [Driver Development](./developer-guide.md#driver-development) - Creating entity drivers
- [Performance](./performance.md#web-scraping-optimization) - Scraping optimization

### Data Management
- [Data Models](./database-schema.md#core-tables) - Entity definitions
- [Relationships](./database-schema.md#relationship-tables) - Entity connections
- [Export Formats](./user-guide.md#exporting-data) - Available formats

### API & Integration
- [RESTful API](./api-reference.md#endpoints) - All endpoints
- [Authentication](./api-reference.md#authentication) - Security setup
- [SDKs](./api-reference.md#sdk-examples) - Language examples

### Deployment & Operations
- [Docker](./installation.md#quick-start-with-docker) - Container deployment
- [Kubernetes](./operations.md#deployment) - Production orchestration
- [Monitoring](./operations.md#monitoring) - Metrics and alerts

## Documentation Standards

### Writing Guidelines
- Use clear, concise language
- Include working code examples
- Add diagrams for complex concepts
- Keep synchronized with code changes

### Code Examples
```python
# Always include context
from src.api.main import app
from src.models import ECStandard

# Show practical usage
@app.get("/api/v1/ec-standards")
async def list_standards(skip: int = 0, limit: int = 100):
    """List EC standards with pagination."""
    return db.query(ECStandard).offset(skip).limit(limit).all()
```

### Formatting
- Use Markdown for all documentation
- Include table of contents for long documents
- Use semantic headers (H1, H2, H3)
- Add navigation links between related docs

## Contributing to Documentation

1. **Keep Updated**: Update docs with any code changes
2. **Be Complete**: Document all features and edge cases
3. **Add Examples**: Include runnable code samples
4. **Test Instructions**: Verify all commands work
5. **Peer Review**: Have documentation reviewed

## Additional Resources

- **GitHub Repository**: [renec-harvester](https://github.com/your-org/renec-harvester)
- **Issue Tracker**: [GitHub Issues](https://github.com/your-org/renec-harvester/issues)
- **API Playground**: http://localhost:8000/docs
- **Support**: support@your-org.com

---

Last updated: January 22, 2025