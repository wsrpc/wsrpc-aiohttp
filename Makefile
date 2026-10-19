.PHONY: sync test test-serializers test-readme linter typing build
sync:
	uv sync --locked
test:
	uv run --locked pytask -k tests
test-serializers:
	uv run --locked --group serializers pytask -k tests
test-readme:
	uv run --locked pytask -k test_readme
linter:
	uv run --locked pytask -k lint
typing:
	uv run --locked pytask -k typing
build:
	uv run --locked pytask -k build
