# encoding: utf-8
import os
from importlib.machinery import SourceFileLoader

from setuptools import find_packages, setup


module = SourceFileLoader(
    "version", os.path.join("wsrpc_aiohttp", "version.py")
).load_module()


setup(
    name="wsrpc-aiohttp",
    version=module.__version__,
    author=module.__author__,
    author_email="me@mosquito.su",
    license=module.package_license,
    description=module.package_info,
    platforms="all",
    url="https://github.com/wsrpc/wsrpc-aiohttp",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Internet",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Microsoft",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    long_description=open("README.rst").read(),
    packages=find_packages(exclude=["tests", "doc"]),
    package_data={"wsrpc_aiohttp": ["static/*", "py.typed"]},
    install_requires=["aiohttp<4", "yarl"],
    python_requires=">3.5.*, <4",
    extras_require={
        "ujson": ["ujson"],
        "testing": [
            "async-timeout",
            "pytest",
            "pytest-aiohttp",
            "pytest-cov",
            "coverage!=4.3",
            "coveralls",
        ],
        "develop": [
            "async-timeout",
            "coverage!=4.3",
            "coveralls",
            "pytest",
            "pytest-aiohttp",
            "pytest-cov",
            "Sphinx",
            "sphinxcontrib-plantuml",
            "tox>=2.4",
        ],
    },
)
