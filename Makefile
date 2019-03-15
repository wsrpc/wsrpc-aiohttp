VENV = env

release: upload_doc
	python3 setup.py sdist bdist_wheel upload

build_doc:
	make -C docs/ html

upload_doc: build_doc
	rsync -zav --delete docs/build/html/ root@wsrpc.info:/home/site-wsrpc/wsrpc-aiohttp-doc/

doc: upload_doc

develop:
	virtualenv $(VENV)
	$(VENV)/bin/pip install -Ue ".[develop]"

npm_release:
	pandoc -s -w markdown --toc README.rst -o README.md
	npm publish
