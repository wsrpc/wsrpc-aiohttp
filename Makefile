.PHONY: static
static:
	poetry run build_static

.PHONY: docs
docs:
	poetry run build_docs


.PHONY: build
build: static
	poetry build
