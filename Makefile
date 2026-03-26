# Makefile for Simulation Trajectoire project

.PHONY: help install test lint format docs clean build

# Help message
help:
	@echo "Simulation Trajectoire Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help          Show this help message"
	@echo "  install       Install the package in development mode"
	@echo "  install-dev   Install with development dependencies"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black"
	@echo "  type-check    Run type checking with mypy"
	@echo "  docs          Build documentation"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build the package"
	@echo "  run           Run the application"
	@echo "  all           Run lint, type-check, and tests"

# Install the package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src/ --max-line-length=88

# Format code
format:
	black src/

# Type checking
type-check:
	mypy src/ --ignore-missing-imports

# Build documentation
docs:
	cd docs && make html

# Clean build artifacts
clean:
	rm -rf build/ dist/ __pycache__/ .pytest_cache/ .mypy_cache/
	rm -rf src/**/__pycache__/
	rm -rf docs/_build/

# Build the package
build:
	python -m build

# Run the application
run:
	python main.py

# Run all checks
all: lint type-check test