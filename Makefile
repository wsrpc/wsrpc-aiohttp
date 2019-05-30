VENV = env

sdist:
	python3 setup.py sdist bdist_wheel

release: build_js sdist upload_doc
	twine upload dist/*$(shell python3 setup.py --version)*

build_js:
	for fname in wsrpc.d.ts wsrpc.es6.js; do \
		curl --compressed -L \
			https://unpkg.com/@wsrpc/client/$$fname \
			-o wsrpc_aiohttp/static/$$fname ;\
	done

	for fname in wsrpc.js wsrpc.min.js wsrpc.min.js.map; do \
		curl --compressed -L \
			https://unpkg.com/@wsrpc/client/dist/$$fname \
			-o wsrpc_aiohttp/static/$$fname ;\
	done

build_doc:
	make -C docs/ html

upload_doc: build_doc
	rsync -zav --delete docs/build/html/ \
		root@wsrpc.info:/home/site-wsrpc/wsrpc-aiohttp-doc/

doc: upload_doc

develop:
	virtualenv $(VENV)
	$(VENV)/bin/pip install -Ue ".[develop]"
