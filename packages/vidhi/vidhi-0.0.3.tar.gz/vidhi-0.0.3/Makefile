# -*- makefile -*-
# Vidhi Project Makefile
# This Makefile provides a clean interface for development tasks

# Default shell
SHELL := bash

# Default target
.DEFAULT_GOAL := help

# === HELP ===
.PHONY: help
help: ## show this help message
	@echo "Vidhi Development Tools"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# === SETUP ===
##@ Setup

.PHONY: install install-dev
install: ## install the package
	pip install .

install-dev: ## install the package in development mode
	pip install -e ".[dev]"

# === LINTING ===
##@ Linting

.PHONY: lint lint/black lint/isort lint/autoflake lint/pyright lint/codespell format format/black format/isort format/autoflake
lint: lint/black lint/isort lint/autoflake lint/pyright lint/codespell ## run all linters

lint/black: ## check python style with black
	black --check vidhi tests

lint/isort: ## check python import order
	isort --check-only vidhi tests

lint/autoflake: ## check for unused python imports
	autoflake --recursive --remove-all-unused-imports --check vidhi tests

lint/pyright: ## run python type checking
	pyright

lint/codespell: ## check for common misspellings
	codespell vidhi tests

format: format/autoflake format/isort format/black ## format all code

format/black: ## format python code with black
	black vidhi tests

format/isort: ## format python imports with isort
	isort vidhi tests

format/autoflake: ## remove unused python imports
	autoflake --recursive --remove-all-unused-imports --in-place vidhi tests

# === TESTING ===
##@ Testing

.PHONY: test test/unit test/coverage test/failed-only
test: test/unit ## run all tests

test/unit: ## run unit tests  
	pytest tests/ -v --tb=short

test/coverage: ## run tests with coverage reports
	mkdir -p test_reports
	pytest --cov=vidhi --cov-report=html:test_reports/coverage_html --cov-report=xml:test_reports/coverage.xml --cov-report=term-missing

test/failed-only: ## rerun only failed tests from last run
	pytest --lf --tb=short

# === BUILDING ===
##@ Building

.PHONY: build clean build/wheel build/sdist
build: clean build/wheel build/sdist ## build the package

build/wheel: ## build wheel distribution
	python -m build --wheel

build/sdist: ## build source distribution
	python -m build --sdist

clean: ## clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf test_reports/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# === RELEASE ===
##@ Release

.PHONY: version
version: ## show current version
	python -c "import vidhi; print(vidhi.__version__)"
