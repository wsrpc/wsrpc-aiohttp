VENV = env

release: upload_doc
	python3 setup.py sdist bdist_wheel
	twine upload dist/*$(shell python3 setup.py --version)*

build_js:
	rm -fr build/js || true
	mkdir -p build/js/dist
	pandoc -s -w markdown --toc README.rst -o build/js/README.md

	cp -va wsrpc_aiohttp/static/* build/js/
	cp -va package.json build/js/
	cp -va rollup.config.js build/js/
	cp -va .browserslistrc build/js/

	(cd build/js && \
		npm i && \
		npx rollup -c rollup.config.js && \
		npx typescript --strict wsrpc.d.ts && \
		npx uglify-js \
			-c --source-map --in-source-map dist/wsrpc.js.map \
			--overwrite -o dist/wsrpc.min.js dist/wsrpc.js && \
		rm -fr node_modules rollup.config.js package-lock.json \
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
	cd build/js && npm publish
	rm -fr build/js || true
