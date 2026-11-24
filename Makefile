.PHONY: help setup lint fmt typecheck test check

help: ## list targets
	@grep -E '^[a-z-]+:.*## ' Makefile | awk -F ':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

setup: ## install locked dependencies
	uv sync --frozen

lint: ## lint and check formatting
	uv run --frozen ruff check .
	uv run --frozen ruff format --check .

fmt: ## format the code
	uv run --frozen ruff format .
	uv run --frozen ruff check --fix .

typecheck: ## strict type check
	uv run --frozen mypy

test: ## run the tests
	uv run --frozen pytest

check: lint typecheck test ## everything
