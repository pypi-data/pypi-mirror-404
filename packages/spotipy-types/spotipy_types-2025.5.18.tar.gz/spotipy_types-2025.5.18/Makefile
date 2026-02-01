.PHONY: all install generate test lint build publish clean help

PYTHON := python3
PIP := pip3

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

all: install generate test lint ## Full setup and validation

install: ## Install package and dependencies
	$(PIP) install -e ".[dev]"

generate: ## Generate Pydantic models from OpenAPI schema
	$(PYTHON) scripts/generate_models.py

test: ## Run pytest test suite
	$(PYTHON) -m pytest tests/ -v

lint: ## Run ruff and mypy
	ruff check src/ tests/
	mypy src/spotipy_types/

build: ## Build wheel and sdist
	$(PYTHON) -m build

publish: ## Publish to PyPI (requires credentials)
	$(PYTHON) -m twine upload dist/*

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

regenerate: clean generate lint test ## Full regeneration pipeline
