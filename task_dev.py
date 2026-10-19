"""Development tasks. Run all with ``uv run pytask`` or select with ``-k``."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


def _python(*args: str) -> None:
    subprocess.run([sys.executable, "-m", *args], cwd=ROOT, check=True)


def task_lint() -> None:
    _python("ruff", "check", ".")
    _python("ruff", "format", "--check", ".")


def task_typing() -> None:
    _python("mypy", "wsrpc_aiohttp", "tests/typing_contracts.py", "task_dev.py")


def task_tests() -> None:
    _python(
        "pytest",
        "--cov=wsrpc_aiohttp",
        "--cov-report=term-missing",
        "--cov-report=xml",
    )


def task_test_readme() -> None:
    _python("pytest", "README.md")


def task_build() -> None:
    subprocess.run(["uv", "build"], cwd=ROOT, check=True)
