# Product Catalog Service Makefile

.PHONY: help install dev-install format lint test test-cov clean docker-build docker-up docker-down dev-up dev-down run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install --upgrade pip
	pip install -e .

dev-install: ## Install development dependencies
	pip install --upgrade pip
	pip install -e ".[dev]"

format: ## Format code with black
	black src tests
	ruff check --fix src tests

lint: ## Lint code with ruff and mypy
	ruff check src tests
	mypy src

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-integration: ## Run integration tests
	pytest tests/ -v -m integration

clean: ## Clean up build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

docker-build: ## Build Docker image
	docker build -t product-catalog-service .

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop services with Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f product-catalog-service

dev-up: ## Start development services
	docker-compose -f docker-compose.dev.yml up -d

dev-down: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## View development logs
	docker-compose -f docker-compose.dev.yml logs -f product-catalog-service

run: ## Run the service locally
	uvicorn src.main:app --host 0.0.0.0 --port 8082 --reload

run-prod: ## Run the service in production mode
	uvicorn src.main:app --host 0.0.0.0 --port 8082

db-upgrade: ## Run database migrations (placeholder for Alembic)
	@echo "Database migrations not implemented yet (use Alembic in production)"

db-downgrade: ## Rollback database migrations (placeholder for Alembic)
	@echo "Database rollback not implemented yet (use Alembic in production)"

# Health check targets
health: ## Check service health
	curl -f http://localhost:8082/health || exit 1

ready: ## Check service readiness
	curl -f http://localhost:8082/health/ready || exit 1

# Monitoring targets
metrics: ## View Prometheus metrics
	curl http://localhost:8082/metrics

# Development workflow targets
dev-setup: dev-install dev-up ## Set up development environment
	@echo "Waiting for database to be ready..."
	sleep 10
	@echo "Development environment ready!"
	@echo "Service: http://localhost:8082"
	@echo "API Docs: http://localhost:8082/docs"
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9091"

dev-test: format lint test ## Run full development test suite

dev-reset: dev-down clean dev-up ## Reset development environment

# Docker cleanup targets
docker-clean: ## Clean up Docker containers and images
	docker-compose down -v
	docker system prune -f

docker-reset: docker-clean docker-build docker-up ## Reset Docker environment

# Production targets
prod-check: ## Check production readiness
	@echo "Checking production readiness..."
	ruff check src tests
	mypy src
	pytest tests/ --cov=src --cov-fail-under=80
	@echo "Production checks passed!"

# Utility targets
logs-tail: ## Tail application logs (if using file logging)
	tail -f logs/app.log

db-shell: ## Connect to database shell (development)
	docker-compose exec product-catalog-db-dev psql -U catalog_user -d product_catalog_db

# API testing targets
api-test: ## Run basic API tests against running service
	@echo "Testing API endpoints..."
	curl -f http://localhost:8082/health
	curl -f http://localhost:8082/health/ready
	curl -f http://localhost:8082/
	@echo "\nAPI tests passed!"