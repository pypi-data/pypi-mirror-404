import click

from pathlib import Path
from pydantic import BaseModel


class E80ContextObject(BaseModel):
    config_path: Path | None
    verbose: bool
    api_host: str
    platform_host: str


def must_get_ctx_object(ctx: click.Context) -> E80ContextObject:
    obj = ctx.find_object(E80ContextObject)
    if obj is None:
        raise click.ClickException(
            "8080 encountered an unrecoverable error! Please raise a bug."
        )
    return ctx.obj
