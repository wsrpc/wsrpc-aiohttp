release:
	python3 setup.py sdist bdist_wheel upload

build_doc:
	make -C docs/ html

upload_doc: build_doc
	rsync -zav --delete docs/build/html/ root@wsrpc.info:/home/site-wsrpc/wsrpc-aiohttp-doc/
