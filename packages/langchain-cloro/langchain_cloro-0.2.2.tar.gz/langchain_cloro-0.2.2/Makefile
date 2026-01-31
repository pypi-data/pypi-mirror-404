.PHONY: help test lint format typing clean

help:
	@echo "Available commands:"
	@echo "  make test       - Run unit tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make typing     - Run type checker"
	@echo "  make clean      - Clean build artifacts"

test:
	pytest tests/unit_tests -v

lint:
	ruff check .

format:
	ruff format .

typing:
	mypy langchain_cloro

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
