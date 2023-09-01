.PHONY: build
static:
	poetry run build_static

.PHONY: build
docs:
	poetry run build_docs


.PHONY: build
build: static
	poetry build
