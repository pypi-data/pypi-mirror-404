import click
import json

from e80.lib.context import E80ContextObject
from e80_sdk.secrets import Secrets
from e80_sdk.internal.environment import Environment, UserApiKey
from e80.lib.project import read_project_config
from e80.lib.platform import PlatformClient
from e80.lib.user import get_auth_info
from e80.lib.constants import E80_COMMAND


def get_sdk_environment(ctx_obj: E80ContextObject) -> tuple[Environment, Secrets]:
    config = read_project_config(ctx_obj)
    auth_info = get_auth_info(ctx_obj)
    if auth_info is None:
        raise click.UsageError(
            f"You are not logged in! Please run '{E80_COMMAND} login'."
        )

    pc = PlatformClient(ctx_obj, api_key=auth_info.auth_token)
    secrets_resp = pc.list_secrets_for_local(config)

    return (
        Environment(
            organization_slug=config.organization_slug,
            project_slug=config.project_slug,
            identity=UserApiKey(api_key=auth_info.auth_token),
            base_platform_url=ctx_obj.platform_host,
            base_api_url=ctx_obj.api_host,
        ),
        Secrets(
            secrets_json=json.dumps([s.model_dump() for s in secrets_resp.secrets])
        ),
    )
