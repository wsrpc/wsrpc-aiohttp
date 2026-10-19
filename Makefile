.PHONY: sync test test-serializers test-docs linter typing docs build
sync:
	uv sync --locked
test:
	uv run --locked pytest --cov=wsrpc_aiohttp --cov-report=term-missing
test-serializers:
	uv run --locked --group serializers pytest
test-docs:
	uv run --locked pytest README.md docs/source
linter:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
typing:
	uv run --locked mypy wsrpc_aiohttp tests/typing_contracts.py
docs:
	uv run --locked sphinx-build -W --keep-going -b html docs/source docs/build/html
build:
	uv build
