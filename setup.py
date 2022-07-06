# encoding: utf-8
import os
from importlib.machinery import SourceFileLoader

from setuptools import find_packages, setup


module = SourceFileLoader(
    "version", os.path.join("wsrpc_aiohttp", "version.py")
).load_module()


TEST_REQUIRES = [
    "async-timeout~=4.0.2",
    "pytest~=7.1.2",
    "pytest-aiohttp~=1.0.4",
    "pytest-cov~=3.0.0",
    "coverage!=4.3",
    "coveralls~=3.3.1",
]


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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "doc"]),
    package_data={"wsrpc_aiohttp": ["static/*", "py.typed"]},
    install_requires=["aiohttp<4", "yarl"],
    python_requires=">3.5.*, <4",
    extras_require={
        "ujson": ["ujson"],
        "testing": TEST_REQUIRES,
        "develop": [
            "Sphinx",
            "sphinxcontrib-plantuml",
            "tox>=2.4",
        ] + TEST_REQUIRES,
    },
)
