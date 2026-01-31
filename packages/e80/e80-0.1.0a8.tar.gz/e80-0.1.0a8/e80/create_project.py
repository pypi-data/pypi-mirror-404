import click
from e80.lib.context import E80ContextObject
from e80.lib.project import read_project_config, write_project_config
from e80.lib.platform import PlatformClient
from e80.lib.user import get_auth_info
from e80.lib.constants import E80_COMMAND


def create_project(ctx_obj: E80ContextObject):
    config = read_project_config(ctx_obj)
    auth_info = get_auth_info(ctx_obj)
    if auth_info is None:
        raise click.UsageError(
            f"You are not logged in! Please run '{E80_COMMAND} login'."
        )

    pc = PlatformClient(ctx_obj, api_key=auth_info.auth_token)
    if config.project_slug is None:
        cr = pc.create_project(config)
        config.project_slug = cr.project_slug
        write_project_config(ctx_obj, config)
        click.echo(f"Successfully created your project: {cr.project_slug}")
