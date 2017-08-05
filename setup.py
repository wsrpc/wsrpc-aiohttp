# encoding: utf-8
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = '0.1.0'
__author__ = 'Dmitry Orlov <me@mosquito.su>'


requirements = ['aiohttp']

if sys.version_info < (3,):
    requirements.append('futures')


setup(
    name='wsrpc-aiohttp',
    version=__version__,
    author=__author__,
    author_email='me@mosquito.su',
    license="Apache 2",
    description="WSRPC WebSocket RPC for aiohttp",
    platforms="all",
    url="https://github.com/wsrpc/wsrpc-tornado",
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Internet',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Microsoft',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    long_description=open('README.rst').read(),
    packages=[
        'wsrpc_aiohttp',
        'wsrpc_aiohttp.websocket',
    ],
    package_data={
        'wsrpc_aiohttp': [
            'static/*'
        ],
    },
    install_requires=requirements,
)
