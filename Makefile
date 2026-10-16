.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
APP := app.main:app

.PHONY: help venv install lint format test check run docker-build docker-up docker-down docker-logs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

$(VENV): ## Create the virtual environment
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

venv: $(VENV) ## Create the virtual environment

install: venv ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

lint: ## Run ruff lint and format checks
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

format: ## Auto-fix lint issues and format code
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

test: ## Run the test suite
	$(VENV)/bin/pytest -q

check: lint test ## Run lint and tests

run: ## Run the app locally with auto-reload
	$(VENV)/bin/uvicorn $(APP) --reload

docker-build: ## Build the Docker image
	docker compose build

docker-up: ## Start the service in Docker (detached)
	docker compose up -d

docker-down: ## Stop and remove the Docker container
	docker compose down

docker-logs: ## Tail the Docker container logs
	docker compose logs -f

clean: ## Remove the virtual environment and caches
	rm -rf $(VENV) .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
