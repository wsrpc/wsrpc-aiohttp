VENV = env

release: upload_doc
	python3 setup.py sdist bdist_wheel upload

build_js:
	(cd wsrpc_aiohttp/static/ && \
			npx typescript --strict wsrpc.d.ts && \
			npx uglify-js -c --source-map --overwrite -o wsrpc.min.js wsrpc.js \
	)

build_doc:
	make -C docs/ html

upload_doc: build_doc
	rsync -zav --delete docs/build/html/ root@wsrpc.info:/home/site-wsrpc/wsrpc-aiohttp-doc/

doc: upload_doc

develop:
	virtualenv $(VENV)
	$(VENV)/bin/pip install -Ue ".[develop]"

npm_release: build_js
	rm -fr build/js || true
	mkdir -p build/js
	pandoc -s -w markdown --toc README.rst -o build/js/README.md
	cp -va wsrpc_aiohttp/static/* build/js/
	cp -va package.json build/js/
	cd build/js && npm publish
	rm -fr build/js || true
