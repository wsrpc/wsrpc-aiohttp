.. _wsrpc-aiohttp: https://github.com/wsrpc/wsrpc-aiohttp
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _ujson: https://pypi.python.org/pypi/ujson


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

Table Of Contents
+++++++++++++++++

.. toctree::
   :glob:
   :maxdepth: 3

   *-*
   apidoc

Features
++++++++

* Two-way RPC
    * Initiating call client function from server side.
    * Calling the server method from the client.
    * Asynchronous connection protocol. Server or client can call
      multiple methods with unpredictable ordering of answers.
* Transferring any exceptions from a client side to
  the server side and vise versa.
* The frontend-library are well done for usage without any modification.
* Fully asynchronous server-side functions.
* Thread-based websocket handler for writing synchronous code
  (for synchronous database drivers etc.)
* Protected server-side methods (starts with underline never will be call
  from clients-side directly)
* If `ujson`_ is installed messages will be serialize/deserialize with it.


How it works
++++++++++++

The following sequence diagram probably to explain some high level of the data-flow.

.. uml::

    @startuml

    title How it works - Sequence Diagram


    participant Browser as browser
    participant "Javascript\nlibrary" as jslib
    participant WebSocket as ws
    participant "Python\nBackend" as backend

    browser -> jslib: Browser makes\nfuncion call
    jslib -> ws: Sending json

    note right of ws
        {
            "serial": 1,
            "call": "jokes.get",
            "arguments": {
                "count": 1,
                "rate": 10
            },
            "type": "call"
        }
    end note

    ws -> backend: Parsing json
    backend -->> backend: Call python function

    backend -> ws: Sending json

    note left of backend
        {
            "serial": 1,
            "data": [
                [
                    "Q: Why do programmers always mix up Halloween and Christmas?",
                    "A: Because Oct 31 == Dec 25!"
                ]
            ],
            "type": "callback"
        }
    end note

    ws -> jslib: Sending through Websocket
    jslib -> browser: Call JS function on client-side


    @enduml


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


Development
+++++++++++

Clone the project:

.. code-block:: shell

    git clone https://github.com/wsrpc/wsrpc-aiohttp.git
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
