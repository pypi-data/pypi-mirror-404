import click
from e80.lib.context import E80ContextObject
import yaml

from typing import Optional
from pydantic import BaseModel
from pathlib import Path


DEFAULT_CONFIG_FILENAME = "8080.yaml"


class CloudProjectConfig(BaseModel):
    project: str
    project_slug: Optional[str] = None
    organization_slug: str
    entrypoint: str
    env_vars: dict[str, str] = {}
    gpu_count: int = 0
    cpu_mhz: int = 500
    memory_size_mb: int = 256

    def require_project(self):
        if self.project_slug is None:
            raise Exception(
                "Project was not created! Please create the project on the platform first."
            )


def read_project_config(ctx_obj: E80ContextObject) -> CloudProjectConfig:
    path = _find_config_path(ctx_obj)

    with path.open() as f:
        yaml_dict = yaml.safe_load(f)
        parsed = CloudProjectConfig.model_validate(yaml_dict)
        return parsed


def write_project_config(
    ctx_obj: E80ContextObject, config: CloudProjectConfig, bootstrap=False
):
    if bootstrap:
        path = (
            ctx_obj.config_path
            if ctx_obj.config_path
            else Path(DEFAULT_CONFIG_FILENAME)
        )
    else:
        path = _find_config_path(ctx_obj)

    with path.open(mode="w") as f:
        model_dict = config.model_dump(exclude_none=True, exclude_unset=True)
        model_str = yaml.dump(model_dict)
        f.write(model_str)


def _find_config_path(ctx_obj: E80ContextObject) -> Path:
    if ctx_obj.config_path is not None:
        if not ctx_obj.config_path.exists():
            raise click.ClickException(
                f"Config file '{ctx_obj.config_path}' was not found. Please make sure it exists, or run 8080 init to create one."
            )
        return ctx_obj.config_path
    else:
        start = Path.cwd()
        for directory in (start, *start.parents):
            candidate = directory / DEFAULT_CONFIG_FILENAME
            if candidate.exists():
                return candidate.resolve()

        raise click.ClickException(
            "Config not found. Run `8080 init` or provide --config to point to your 8080.yaml."
        )
