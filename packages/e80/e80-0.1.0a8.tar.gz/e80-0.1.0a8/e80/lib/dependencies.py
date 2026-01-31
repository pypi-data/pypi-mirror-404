import click
import subprocess

from shutil import which


def require_uv():
    if which("uv") is None:
        raise click.ClickException(
            "'uv' is not installed! Please install 'uv' and make sure it is on $PATH"
        )

    uv_version = subprocess.run(["uv", "--version"], capture_output=True, text=True)
    if uv_version.returncode > 0:
        raise click.ClickException(
            f"'uv --version' returned non-zero code: {uv_version.returncode}. Output: {uv_version.stderr}"
        )

    version_num = uv_version.stdout.removeprefix("uv ")
    if not version_num.startswith("0.9"):
        raise click.ClickException(
            f"Please use 'uv' with version 0.9.x. Parsed version number: {version_num}"
        )


def require_docker():
    if which("docker") is None:
        raise click.ClickException(
            "'docker' is not installed! We require Docker to build using platform-specific packages. Please install Docker."
        )
