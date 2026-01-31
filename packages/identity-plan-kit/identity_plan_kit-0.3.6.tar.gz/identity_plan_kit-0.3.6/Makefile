.PHONY: help install install-dev install-build lint format typecheck test clean clean-all build build-wheels publish bump-patch bump-minor bump-major

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
UV := uv
VENV_PYTHON := .venv/bin/python
PACKAGE_NAME := identity_plan_kit
SRC_DIR := src/identity_plan_kit
TESTS_DIR := tests

# Environment file (override with: make test ENV_FILE=path/to/.env)
# Searches: .env.local, .env, examples/playing/.env.local
ENV_FILE ?= $(shell \
	if [ -f .env.local ]; then echo ".env.local"; \
	elif [ -f .env ]; then echo ".env"; \
	elif [ -f examples/playing/.env.local ]; then echo "examples/playing/.env.local"; \
	else echo ""; \
	fi)

# PyPI config file (override with: make publish PYPIRC=path/to/.pypirc)
# Searches: .pypirc (local), ~/.pypirc (home)
PYPIRC ?= $(shell \
	if [ -f .pypirc ]; then echo ".pypirc"; \
	elif [ -f $(HOME)/.pypirc ]; then echo "$(HOME)/.pypirc"; \
	else echo ""; \
	fi)

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package dependencies using uv
	$(UV) pip install -e .

install-dev: ## Install package with development dependencies using uv
	$(UV) pip install -e ".[dev]"

install-build: ## Install build dependencies
	@echo "Installing build dependencies..."
	$(UV) pip install build twine
	@echo "✓ Build dependencies installed!"

lint: ## Run ruff linter
	@echo "Running ruff linter..."
	$(UV) run ruff check $(SRC_DIR)

lint-fix: ## Run ruff linter with auto-fix
	@echo "Running ruff linter with auto-fix..."
	$(UV) run ruff check --fix $(SRC_DIR)

format: ## Format code with ruff
	@echo "Formatting code with ruff..."
	$(UV) run ruff format $(SRC_DIR)

format-check: ## Check code formatting without making changes
	@echo "Checking code formatting..."
	$(UV) run ruff format --check $(SRC_DIR)

typecheck: ## Run mypy type checker
	@echo "Running mypy type checker..."
	$(UV) run mypy $(SRC_DIR) --explicit-package-bases

check: lint format-check typecheck ## Run all checks (lint, format, typecheck)
	@echo "All checks passed!"

test: ## Run tests with pytest (loads env from ENV_FILE)
	@echo "Running tests..."
ifneq ($(ENV_FILE),)
	@echo "Loading environment from $(ENV_FILE)"
	@set -a && . $(ENV_FILE) && set +a && $(UV) run pytest $(TESTS_DIR) -v
else
	@echo "No env file found, running without environment"
	@$(UV) run pytest $(TESTS_DIR) -v
endif

test-integration: ## Run integration tests with pytest (loads env from ENV_FILE)
	@echo "Running integration tests..."
ifneq ($(ENV_FILE),)
	@echo "Loading environment from $(ENV_FILE)"
	@set -a && . $(ENV_FILE) && set +a && $(UV) run pytest $(TESTS_DIR)/integration -v
else
	@echo "No env file found, running without environment"
	@$(UV) run pytest $(TESTS_DIR)/integration -v
endif

test-cov: ## Run tests with coverage report (loads env from ENV_FILE)
	@echo "Running tests with coverage..."
ifneq ($(ENV_FILE),)
	@echo "Loading environment from $(ENV_FILE)"
	@set -a && . $(ENV_FILE) && set +a && $(UV) run pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
else
	@echo "No env file found, running without environment"
	@$(UV) run pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
endif

clean: ## Clean up build artifacts and cache
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean ## Clean all build artifacts
	@echo "✓ All artifacts cleaned!"

build: clean ## Build package distribution (source + wheel)
	@echo "Building package..."
	$(UV) build

build-wheels: ## Build binary wheels for distribution
	@echo "Building binary wheels..."
	$(UV) build --wheel
	@echo "✓ Wheels built in dist/"
	@ls -lh dist/*.whl

publish-test: build ## Publish package to TestPyPI (uses ~/.pypirc if present)
	@echo "Publishing to TestPyPI..."
ifeq ($(wildcard $(PYPIRC)),)
	$(UV) publish --index testpypi
else
	@echo "Using credentials from $(PYPIRC)"
	@TOKEN=$$(awk '/^\[testpypi\]/{found=1} found && /^password/{print $$3; exit}' $(PYPIRC)); \
	if [ -n "$$TOKEN" ]; then \
		$(UV) publish --index testpypi --token "$$TOKEN"; \
	else \
		$(UV) publish --index testpypi; \
	fi
endif

publish: build ## Publish package to PyPI (uses ~/.pypirc if present)
	@echo "Publishing to PyPI..."
ifeq ($(wildcard $(PYPIRC)),)
	$(UV) publish
else
	@echo "Using credentials from $(PYPIRC)"
	@TOKEN=$$(awk '/^\[pypi\]/{found=1} found && /^password/{print $$3; exit}' $(PYPIRC)); \
	if [ -n "$$TOKEN" ]; then \
		$(UV) publish --token "$$TOKEN"; \
	else \
		$(UV) publish; \
	fi
endif

ci: check test-cov ## Run all CI checks (lint, format, typecheck, tests with coverage)
	@echo "✓ All CI checks passed!"

pre-commit: check test ## Run all pre-commit checks
	@echo "Pre-commit checks passed!"

version: ## Show current version
	@$(UV) run bump-my-version show current_version

bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@echo "Bumping patch version..."
	$(UV) run bump-my-version bump patch
	@echo "✓ Version bumped!"

bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@echo "Bumping minor version..."
	$(UV) run bump-my-version bump minor
	@echo "✓ Version bumped!"

bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	@echo "Bumping major version..."
	$(UV) run bump-my-version bump major
	@echo "✓ Version bumped!"

bump-patch-dry: ## Preview patch version bump
	@$(UV) run bump-my-version bump patch --dry-run --verbose

bump-minor-dry: ## Preview minor version bump
	@$(UV) run bump-my-version bump minor --dry-run --verbose

bump-major-dry: ## Preview major version bump
	@$(UV) run bump-my-version bump major --dry-run --verbose