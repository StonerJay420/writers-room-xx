# Writers Room XX Makefile

.PHONY: dev test clean build seed-data lint format

# Development environment
dev:
	@echo "Starting development environment..."
	docker compose -f docker-compose.fixed.yml up -d
	@echo "Services are starting. Check status with 'docker compose ps'"
	@echo "API will be available at http://localhost:8080"
	@echo "UI will be available at http://localhost:3000"

# Stop development environment
stop:
	@echo "Stopping development environment..."
	docker compose -f docker-compose.fixed.yml down

# Restart development environment
restart:
	@echo "Restarting development environment..."
	docker compose -f docker-compose.fixed.yml restart

# Show logs
logs:
	docker compose -f docker-compose.fixed.yml logs -f

# Run tests
test:
	@echo "Running tests..."
	cd api && python -m pytest -xvs tests/

# Clean up
clean:
	@echo "Cleaning up..."
	docker compose -f docker-compose.fixed.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Build containers
build:
	@echo "Building containers..."
	docker compose -f docker-compose.fixed.yml build

# Seed sample data
seed-data:
	@echo "Seeding sample data..."
	mkdir -p data/codex data/manuscript
	cp -n attached_assets/sample_codex.md data/codex/world.md || true
	cp -n attached_assets/sample_manuscript.md data/manuscript/chapter1.md || true
	@echo "Sample data seeded. You can now ingest these files through the API."

# Lint code
lint:
	@echo "Linting code..."
	cd api && ruff check .

# Format code
format:
	@echo "Formatting code..."
	cd api && ruff format .

# Run API locally (without Docker)
api-local:
	@echo "Running API locally..."
	cd api && uvicorn app.main:app --reload --port 8080

# Run UI locally (without Docker)
ui-local:
	@echo "Running UI locally..."
	cd frontend && npm run dev

# Install dependencies
install:
	@echo "Installing API dependencies..."
	cd api && pip install -r requirements.fixed.txt
	@echo "Installing UI dependencies..."
	cd frontend && npm install

# Create a new branch for changes
branch:
	@echo "Creating a new branch for changes..."
	git checkout -b fix/dependency-and-docker-issues

# Commit changes
commit:
	@echo "Committing changes..."
	git add .
	git commit -m "Fix dependency conflicts and Docker configuration"

# Push changes
push:
	@echo "Pushing changes..."
	git push https://x-access-token:$$GITHUB_TOKEN@github.com/StonerJay420/writers-room-xx fix/dependency-and-docker-issues

# Create a pull request
pr:
	@echo "Creating a pull request..."
	gh pr create --title "Fix dependency conflicts and Docker configuration" \
		--body "This PR fixes dependency conflicts between pydantic and spaCy, adds proper ChromaDB configuration, and improves Docker setup with healthchecks and service dependencies."