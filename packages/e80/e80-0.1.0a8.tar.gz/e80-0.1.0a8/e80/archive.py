import click
import zipfile
import subprocess
import shutil
import requirements
import os
from pathlib import Path
from e80.lib.context import E80ContextObject
from e80.lib.project import read_project_config
from e80.lib.pyproject import (
    get_local_sources,
    get_build_system_requirements,
)
from e80.lib.constants import E80_HTTP_CUDA_PACKAGES


def _build_shell_command(
    *,
    build_system_requirements: list[str],
    python_version: str | None,
) -> str:
    return (
        "set -e;"
        f"uv pip install --target /builder/output --no-deps --python-version {python_version} -r /builder/requirements.txt; "
        f"chown {os.getuid()}:{os.getgid()} -R /builder/output; "
    )


def archive_project(ctx_obj: E80ContextObject):
    project_config = read_project_config(ctx_obj)
    local_sources = get_local_sources()
    build_system_requirements = get_build_system_requirements()
    cuda_base_image = project_config.gpu_count > 0

    cache_root = Path(".8080_cache")

    if cache_root.exists():
        shutil.rmtree(cache_root)

    cache_root.mkdir()

    click.echo("Compiling requirements...")

    compile_logs = cache_root / "uv-pip-compile.logs.txt"
    unfiltered_requirements = cache_root / "unfiltered_requirements.txt"
    with open(compile_logs, "w") as f:
        result = subprocess.run(
            [
                "uv",
                "pip",
                "compile",
                "pyproject.toml",
                "--python-version",
                "3.13",
                "-o",
                unfiltered_requirements,
            ],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
        if result.returncode != 0:
            raise click.ClickException(
                f"Compiling requirements failed. Please check {compile_logs}."
            )

    tmp_constraints = cache_root / "constraints.txt"
    with open(tmp_constraints, "w") as f:
        f.write(E80_HTTP_CUDA_PACKAGES if cuda_base_image else "")

    # Run pip compile again, this time with the constraints.
    # That way, if this one fails, we know for certain it is because of
    # constraints.txt and can return a suitable error message.
    compatibility_logs = cache_root / "pip-compatibility.logs.txt"
    with open(compatibility_logs, "w") as f:
        result = subprocess.run(
            [
                "uv",
                "pip",
                "compile",
                "pyproject.toml",
                "--python-version",
                "3.13",
                "-c",
                tmp_constraints,
                "-o",
                unfiltered_requirements,
            ],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
        if result.returncode != 0:
            raise click.ClickException(
                f"Your package dependencies is incompatible with the 8080 runtime environment. Please see {compatibility_logs} for more info."
            )

    # If we got to this point, we know for a fact the user's packages
    # are compatible with the packages on the base image.
    # We now remove them if they are part of requirements.txt, so as to
    # not shadow the packages on the base image.
    # This should reduce the archive size by a lot, as the CUDA packages
    # are hefty.
    shadow_packages_set: set[str] = set()
    if cuda_base_image:
        for req in requirements.parse(E80_HTTP_CUDA_PACKAGES):
            if req.name:
                shadow_packages_set.add(req.name)
    filtered_requirements = cache_root / "requirements.txt"
    with open(filtered_requirements, "w") as fr:
        with open(unfiltered_requirements, "r") as f:
            for line in f:
                try:
                    reqs = list(requirements.parse(line))
                except Exception as e:
                    click.echo(
                        f"WARNING: Error parsing requirements: {e}. This could be okay if you have tool.uv.sources set"
                    )
                if not reqs:
                    continue
                if reqs[0].name not in shadow_packages_set:
                    fr.write(line)
                elif ctx_obj.verbose:
                    click.echo(
                        f"WARNING: Not including dependency: {line.strip()}, as it shadows a dependency on the 8080 runtime environment. This should be okay."
                    )

    click.echo("Building dependencies in Docker...")

    packages_path = cache_root / "archive"
    if packages_path.exists():
        shutil.rmtree(packages_path)
    packages_path.mkdir(parents=True)

    base_image = (
        "ghcr.io/astral-sh/uv:python3.13-trixie"
        if cuda_base_image
        else "ghcr.io/astral-sh/uv:python3.13-alpine"
    )
    build_logs = cache_root / "docker-build.logs.txt"
    shell_command = _build_shell_command(
        build_system_requirements=build_system_requirements,
        python_version="3.13",
    )
    with open(build_logs, "w") as f:
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--platform",
                "linux/amd64",
                "-a",
                "stderr",
                "-a",
                "stdout",
                "-v",
                f"{filtered_requirements.resolve()}:/builder/requirements.txt",
                "-v",
                f"{packages_path.resolve()}:/builder/output",
                "-w",
                "/builder",
                base_image,
                "/bin/sh",
                "-c",
                shell_command,
            ],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
        if result.returncode != 0:
            raise click.ClickException(
                f"Docker build failed. Please check {build_logs}"
            )

    click.echo("Creating final archive...")
    archive_path = Path(".8080_cache/archive.zip")

    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        # 1. Archive the fully-linked dependencies and local sources
        # packages_path contains everything installed via the --target commands
        for file_path in packages_path.rglob("*"):
            if file_path.is_file():
                # We store the file relative to the packages directory
                # so 'packages/pydantic/main.py' becomes 'pydantic/main.py' in the zip
                archive_name = file_path.relative_to(packages_path)
                archive.write(file_path, arcname=archive_name)

        for source in local_sources:
            source_path = Path(source.path)
            for root, _, files in source_path.walk():
                stripped = root.relative_to(source_path)
                if root == source_path:
                    continue
                for file in files:
                    archive.write(root / file, stripped / file)

        # Archive all the user's code
        # Everything in the module used in the entrypoint will be archived.
        ep_split = project_config.entrypoint.split(".")
        if len(ep_split) < 2:
            raise click.ClickException(
                f"Could not find module from entrypoint: '{project_config.entrypoint}'. Your entrypoint should be in a module like: 'foo.bar:app'",
            )
        module = ep_split[0]

        for root, _, files in Path(module).walk():
            for file in files:
                archive.write(root / file)

    click.echo(f"Successfully created {archive_path}")
