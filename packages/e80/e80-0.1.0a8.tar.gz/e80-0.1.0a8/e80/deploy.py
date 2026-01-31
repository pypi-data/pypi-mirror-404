from math import ceil
import math
import click
from e80.archive import archive_project
from e80.create_project import create_project
from e80.lib.context import E80ContextObject
from e80.lib.project import read_project_config
from e80.lib.platform import PlatformClient
from e80.lib.user import get_auth_info
from e80.lib.constants import E80_COMMAND
from pathlib import Path

_UPLOAD_CHUNK_SIZE = 100 * 1024 * 1024  # 100 mb


def deploy_project(
    ctx_obj: E80ContextObject,
    artifact_id: str | None = None,
    no_build: bool = False,
) -> None:
    create_project(ctx_obj)

    config = read_project_config(ctx_obj)
    auth_info = get_auth_info(ctx_obj)
    if auth_info is None:
        raise click.UsageError(
            f"You are not logged in! Please run '{E80_COMMAND} login'."
        )
    pc = PlatformClient(ctx_obj, api_key=auth_info.auth_token)

    artifact_id_to_deploy: str | None = None
    if artifact_id is not None:
        artifact_id_to_deploy = artifact_id
        click.echo(f"Using artifact '{artifact_id}'")
    else:
        if not no_build:
            archive_project(ctx_obj)
        archive = Path(".8080_cache/archive.zip")
        if archive.stat().st_size > _UPLOAD_CHUNK_SIZE:
            click.echo(
                f"Archive is {math.floor(archive.stat().st_size / (1024 * 1024))}mb. Uploading in parts."
            )
            chunks = ceil(archive.stat().st_size / _UPLOAD_CHUNK_SIZE)
            start = pc.start_upload_artifact_part(config)
            click.echo(
                f"Starting multipart upload for artifact ID: {start.artifact_id}"
            )
            with archive.open("rb") as f:
                for i in range(1, chunks + 1):
                    pc.upload_artifact_part(
                        config,
                        artifact_id=start.artifact_id,
                        part_num=i,
                        part=f.read(_UPLOAD_CHUNK_SIZE),
                    )
                    click.echo(f"Finished uploading part {i}")
            pc.finish_upload_artifact_part(config, start.artifact_id)
            artifact_id_to_deploy = start.artifact_id

        else:
            with archive.open("rb") as f:
                click.echo("Uploading artifact...")
                resp = pc.upload_artifact(config, f)
                click.echo(
                    f"Uploading artifact '{resp.artifact_id}' finished. Starting deploy..."
                )
                artifact_id_to_deploy = resp.artifact_id

    deploy_resp = pc.deploy_artifact(config, artifact_id=artifact_id_to_deploy)
    if deploy_resp.deployment_id is None:
        click.echo("No change detected")
    else:
        click.echo(
            f"Deploy started! Follow along: {ctx_obj.platform_host}/o/{config.organization_slug}/p/{config.project_slug}/edge/deployment/{deploy_resp.deployment_id}"
        )
