.. _wsrpc-aiohttp: https://github.com/wsrpc/wsrpc-aiohttp
.. _asyncio: https://docs.python.org/3/library/asyncio.html


Welcome to wsrpc-aiohttp's documentation!
=========================================

.. image:: https://coveralls.io/repos/github/wsrpc/wsrpc-aiohttp/badge.svg?branch=master
    :target: https://coveralls.io/github/wsrpc/wsrpc-aiohttp
    :alt: Coveralls

.. image:: https://travis-ci.org/mosquito/wsrpc-aiohttp.svg
    :target: https://travis-ci.org/mosquito/wsrpc-aiohttp
    :alt: Travis CI

.. image:: https://img.shields.io/pypi/v/wsrpc-aiohttp.svg
    :target: https://pypi.python.org/pypi/wsrpc-aiohttp/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/wsrpc-aiohttp.svg
    :target: https://pypi.python.org/pypi/wsrpc-aiohttp/

.. image:: https://img.shields.io/pypi/pyversions/wsrpc-aiohttp.svg
    :target: https://pypi.python.org/pypi/wsrpc-aiohttp/

.. image:: https://img.shields.io/pypi/l/wsrpc-aiohttp.svg
    :target: https://pypi.python.org/pypi/wsrpc-aiohttp/


`wsrpc-aiohttp`_ it's library for writing live web applications with websockets.


Installation
++++++++++++

Installation with pip:

.. code-block:: shell

    pip install wsrpc-aiohttp


Installation from git:

.. code-block:: shell

    # via pip
    pip install https://github.com/wsrpc/wsrpc-aiohttp/archive/master.zip

    # manually
    git clone https://github.com/wsrpc/wsrpc-aiohttp.git
    cd wsrpc-aiohttp
    python setup.py install


Usage example
+++++++++++++

Let's try to write simple http server with WSRPC handler.

.. literalinclude:: examples/main/server.py
   :language: python

Next you have two options:

    1. Browser WSRPC client.
    2. Python WSRPC client.

Browser client
~~~~~~~~~~~~~~

.. literalinclude:: examples/main/web-client.html
   :language: html

You can try it on http://localhost:8000/web-client.html (required running server.py).

.. image:: _static/web-client-demo.gif


Python client
~~~~~~~~~~~~~

.. literalinclude:: examples/main/client.py
   :language: python

This is so useful for testing and shell scripts for your services.

Development
+++++++++++

Clone the project:

.. code-block:: shell

    git clone https://github.com/mosquito/wsrpc-aiohttp.git
    cd wsrpc-aiohttp


Create a new virtualenv for `wsrpc-aiohttp`_:

.. code-block:: shell

    virtualenv -p python3.5 env

Install all requirements for `wsrpc-aiohttp`_:

.. code-block:: shell

    env/bin/pip install -e '.[develop]'


Thanks for contributing
+++++++++++++++++++++++

* `@mosquito`_ (author)

.. _@mosquito: https://github.com/mosquito
