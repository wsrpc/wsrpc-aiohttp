.PHONY: sync test test-serializers test-docs linter typing docs build
sync:
	uv sync --locked
test:
	uv run --locked pytask -k tests
test-serializers:
	uv run --locked --group serializers pytask -k tests
test-docs:
	uv run --locked pytask -k test_docs
linter:
	uv run --locked pytask -k lint
typing:
	uv run --locked pytask -k typing
docs:
	uv run --locked pytask -k "docs and not test_docs"
build:
	uv run --locked pytask -k build
