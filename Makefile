.PHONY: help install setup start stop clean test lint crawl harvest build-ui

# Default target
help:
	@echo "RENEC Harvester - Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make setup      - Set up development environment"
	@echo "  make start      - Start Docker services"
	@echo "  make stop       - Stop Docker services"
	@echo "  make clean      - Clean up artifacts and cache"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting and formatting"
	@echo "  make crawl      - Run crawler in mapping mode"
	@echo "  make harvest    - Run crawler in harvest mode"
	@echo "  make build-ui   - Build Next.js UI"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	playwright install --with-deps

# Setup development environment
setup: install
	docker-compose up -d
	@echo "Waiting for services to start..."
	sleep 10
	python -m src.cli db init || true
	@echo "Setup complete! Services running at:"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis: localhost:6379"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000"

# Start services
start:
	docker-compose up -d

# Stop services
stop:
	docker-compose down

# Clean artifacts
clean:
	rm -rf artifacts/*
	rm -rf .scrapy/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run tests
test:
	pytest -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term

# Linting and formatting
lint:
	black src tests
	ruff check src tests --fix
	mypy src --ignore-missing-imports

# Run crawler in mapping mode
crawl:
	scrapy crawl renec -a mode=crawl -a max_depth=5

# Run crawler in harvest mode
harvest:
	scrapy crawl renec -a mode=harvest

# Build UI (placeholder for Sprint 2)
build-ui:
	@echo "UI build will be implemented in Sprint 2"
	# cd ui && npm install && npm run build

# Database operations
db-migrate:
	alembic upgrade head

db-reset:
	docker exec -it renec-postgres psql -U renec -d postgres -c "DROP DATABASE IF EXISTS renec_harvester;"
	docker exec -it renec-postgres psql -U renec -d postgres -c "CREATE DATABASE renec_harvester;"
	$(MAKE) db-migrate

# Development helpers
shell:
	ipython

redis-cli:
	docker exec -it renec-redis redis-cli -a renec_redis_pass

psql:
	docker exec -it renec-postgres psql -U renec -d renec_harvester

# Performance monitoring
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/renec_grafana_pass)"
	@echo "Flower: http://localhost:5555 (admin/renec_flower_pass)"
	@echo "pgAdmin: http://localhost:5050 (admin@renec.local/renec_pgadmin_pass)"