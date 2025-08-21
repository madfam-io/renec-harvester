# Changelog

All notable changes to the RENEC Harvester project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with unit, integration, and E2E tests
- Performance optimization module with caching and connection pooling
- Kubernetes deployment configurations
- Terraform infrastructure as code
- CI/CD pipeline with GitHub Actions
- Monitoring stack with Prometheus and Grafana
- Daily probe scheduler with Celery
- Graph and denormalized JSON export formats

### Changed
- Enhanced API with full CRUD operations for all entities
- Improved spider performance with parallel processing
- Upgraded to PostgreSQL for better concurrent write support

### Fixed
- Resolved 404 errors in RENEC spider
- Fixed database model conflicts with table naming
- Improved error handling and retry logic

## [2.0.0] - 2024-01-22

### Added
- Sprint 3: Production Readiness features
- Kubernetes deployment manifests
- Terraform infrastructure modules
- Comprehensive monitoring with Prometheus/Grafana
- Performance optimization with Redis caching
- Security hardening configurations
- Backup and recovery procedures

### Changed
- Migrated from SQLite to PostgreSQL for production use
- Enhanced API with response caching
- Improved spider with circuit breaker patterns

## [1.2.0] - 2024-01-21

### Added
- Sprint 2: Extended Entity Extraction
- Centros (Evaluation Centers) driver and models
- Sectores (Sectors) and Comités (Committees) support
- Enhanced relationships between entities
- Graph export format for visualization
- Denormalized JSON export for analytics
- Next.js UI components (EntityFinder, NetworkVisualization)

### Changed
- Renamed database tables to avoid conflicts (v2 suffix)
- Enhanced export system with multiple formats
- Improved API with relationship traversal

## [1.1.0] - 2024-01-20

### Added
- Sprint 1: Core functionality implementation
- Database models with SQLAlchemy ORM
- RESTful API with FastAPI
- Basic export functionality (JSON, CSV, SQLite)
- Next.js UI for monitoring and control
- Docker Compose setup for local development

### Changed
- Refactored spider for better modularity
- Implemented driver pattern for entity extraction
- Added temporal tracking to all models

## [1.0.0] - 2024-01-19

### Added
- Sprint 0: Foundation and reconnaissance
- Working RENEC spider with crawl and harvest modes
- Basic project structure and repository setup
- Local testing framework
- Development workflow documentation

### Fixed
- Resolved all 404 errors with RENEC endpoints
- Fixed SSL certificate issues for local development

## [0.1.0] - 2024-01-15

### Added
- Initial project setup
- Basic Scrapy spider framework
- Project documentation (README, ROADMAP, SOFTWARE_SPEC)
- Development environment configuration

[Unreleased]: https://github.com/your-org/renec-harvester/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/your-org/renec-harvester/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/your-org/renec-harvester/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/your-org/renec-harvester/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/your-org/renec-harvester/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/your-org/renec-harvester/releases/tag/v0.1.0