"""Include the pinned wsrpc-ts browser client before delegating to uv_build."""

from typing import Any

import uv_build

from .client import ensure_client


def __getattr__(name: str) -> Any:
    return getattr(uv_build, name)


def build_sdist(sdist_directory: str, config_settings: Any = None) -> str:
    ensure_client()
    return uv_build.build_sdist(sdist_directory, config_settings)


def build_wheel(
    wheel_directory: str,
    config_settings: Any = None,
    metadata_directory: str | None = None,
) -> str:
    ensure_client()
    return uv_build.build_wheel(
        wheel_directory, config_settings, metadata_directory
    )


def build_editable(
    wheel_directory: str,
    config_settings: Any = None,
    metadata_directory: str | None = None,
) -> str:
    ensure_client()
    return uv_build.build_editable(
        wheel_directory, config_settings, metadata_directory
    )
