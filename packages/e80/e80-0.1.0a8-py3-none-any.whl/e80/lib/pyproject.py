import tomllib
from dataclasses import dataclass


def get_local_sources() -> "list[LocalUVSource]":
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

        uv_sources = data.get("tool", {}).get("uv", {}).get("sources", {})

        sources = [
            LocalUVSource(pkg, data["path"])
            for pkg, data in uv_sources.items()
            if isinstance(data, dict) and data.get("path") is not None
        ]

        return sources


def get_build_system_requirements() -> list[str]:
    """Extract build-system requirements from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

        build_system = data.get("build-system", {})
        requires = build_system.get("requires", [])

        return requires


@dataclass
class LocalUVSource:
    pkg: str
    path: str
