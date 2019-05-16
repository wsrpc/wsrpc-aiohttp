VENV = env

release: upload_doc
	python3 setup.py sdist bdist_wheel
	twine upload dist/*$(shell python3 setup.py --version)*

build_js:
	rm -fr build/js || true
	mkdir -p build/js/dist
	pandoc -s -w markdown --toc README.rst -o build/js/README.md

	cp -va \
		wsrpc_aiohttp/static/* \
		package.json \
		rollup.config.js \
		.browserslistrc \
		build/js/

	(cd build/js && \
		npm i && \
		npx typescript --strict wsrpc.d.ts && \
		npx rollup -c rollup.config.js && \
		npx uglify-js \
			-c --source-map --in-source-map dist/wsrpc.js.map \
			--overwrite -o dist/wsrpc.min.js dist/wsrpc.js && \
		rm -fr \
			node_modules \
			rollup.config.js \
			package-lock.json \
			.browserslistrc \
	)

	cp build/js/dist/*.min.* wsrpc_aiohttp/static

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
