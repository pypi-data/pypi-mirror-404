import click
import subprocess
import os

from dataclasses import dataclass
from typing import cast
from pathlib import Path
from shutil import which
from e80.lib.context import E80ContextObject
from e80.lib.user import read_user_config, AuthInfo
from e80.lib.project import write_project_config, CloudProjectConfig
from e80.lib.platform import PlatformClient, OrganizationMembership
from e80.lib.constants import E80_COMMAND, E80_VERSION
from e80.lib.prompt import require_tty
from rich.prompt import IntPrompt
from rich import print as rich_print


def init_project(
    ctx_obj: E80ContextObject,
    project_slug: str | None,
    install_path: str | None,
    gpu_count: int,
    cpu: int,
    memory_size_mb: int,
    organization_slug: str | None,
    use_git: bool,
):
    user_config = read_user_config()
    if user_config is None:
        raise click.UsageError(
            f"You are not logged in! Please run '{E80_COMMAND} login'."
        )

    auth_info = user_config.auth_info.get(ctx_obj.platform_host)
    if auth_info is None:
        raise click.UsageError(
            f"You are not logged in to {ctx_obj.platform_host}. Please run '{E80_COMMAND} login --host \"{ctx_obj.platform_host}\"' first!"
        )

    org_slug = _get_org_slug(ctx_obj, auth_info, organization_slug)
    names_and_dirs = _get_names_and_dirs(install_path)

    with open(names_and_dirs.path / "pyproject.toml", "w") as f:
        if gpu_count > 0:
            f.write(
                build_gpu_pyproject(python_project_name=names_and_dirs.python_package)
            )
        else:
            f.write(build_pyproject(python_project_name=names_and_dirs.python_package))

    with open(names_and_dirs.path / "README.md", "w") as f:
        f.write(build_readme(project_name=names_and_dirs.e80_name))

    with open(names_and_dirs.path / "AGENTS.md", "w") as f:
        f.write(build_agents_md(project_name=names_and_dirs.e80_name))

    # All the code goes into its own module
    module_path = Path(names_and_dirs.path / names_and_dirs.python_module)
    module_path.mkdir()
    (module_path / "__init__.py").touch()
    with open(module_path / "main.py", "w") as f:
        f.write(build_initial_file(project_name=names_and_dirs.e80_name))

    cwd = Path(".").resolve()

    os.chdir(names_and_dirs.path)

    write_project_config(
        ctx_obj,
        CloudProjectConfig(
            project=names_and_dirs.e80_name,
            organization_slug=org_slug,
            project_slug=project_slug,
            entrypoint=f"{names_and_dirs.python_module}.main:app",
            gpu_count=gpu_count,
            cpu_mhz=cpu,
            memory_size_mb=memory_size_mb,
        ),
        bootstrap=True,
    )

    subprocess.check_call(["uv", "sync"])

    if use_git and which("git") is not None:
        subprocess.check_call(["git", "init", "."])

    os.chdir(cwd)

    click.echo(f"8080 cloud project initialized in '{names_and_dirs.path}'")
    if names_and_dirs.path == cwd:
        click.echo(f"Run the test server with: '{E80_COMMAND} dev'")
    else:
        click.echo(
            f"Run the test server with: 'cd \"{names_and_dirs.path.relative_to(cwd)}\"; {E80_COMMAND} dev'"
        )


def _get_org_slug(
    ctx_obj: E80ContextObject,
    auth_info: AuthInfo,
    explicit_org_slug: str | None = None,
) -> str:
    mr = PlatformClient(
        ctx_obj, api_key=auth_info.auth_token
    ).list_organization_memberships()
    if len(mr.memberships) == 0:
        raise click.UsageError(
            'You are not part of any organizations. Please go to "https://app.8080.io" to create your first organization',
        )
    elif explicit_org_slug is not None:
        selected = next(
            (m for m in mr.memberships if m.organization_slug == explicit_org_slug),
            None,
        )
        if selected is None:
            raise click.UsageError(
                f'Organization with slug "{explicit_org_slug}" not found. Please enter a valid organization slug.'
            )
    elif len(mr.memberships) == 1:
        selected = mr.memberships[0]
    else:
        selected = None

        while selected is None:
            for [idx, ms] in enumerate(mr.memberships):
                rich_print(
                    f"[bold bright_blue][{idx}][/bold bright_blue] - {ms.organization_name} - ({ms.organization_slug})"
                )
            require_tty("--org")
            value = IntPrompt.ask(
                "[white]Please selected an organization[/white]",
                default=0,
                choices=[str(i) for i in range(len(mr.memberships))],
            )
            selected = mr.memberships[value]

    selected = cast(OrganizationMembership, selected)  # Make mypy happy.
    click.echo(
        f"Creating a project for organization: {selected.organization_name} ({selected.organization_slug})"
    )
    return selected.organization_slug


@dataclass
class _NamesAndDirs:
    path: Path
    e80_name: str
    python_module: str
    python_package: str


def _get_names_and_dirs(
    explicit_install_path: str | None,
) -> _NamesAndDirs:
    """
    The reason this is required, is because the conventional Python package and Python module is different.

    Both are lowercase alphanumeric, but a Python package prefers dash (-), while a Python module prefers underscore (_).
    """
    if explicit_install_path:
        project_dir = Path(explicit_install_path).resolve()
    else:
        project_dir = Path(".").resolve()

    proposed_name = project_dir.name
    if len(proposed_name) > 64:
        raise click.ClickException(
            f"Project name {proposed_name} is greater than 64 characters. Please choose a shorter name"
        )
    if proposed_name[0].isdigit():
        raise click.ClickException(
            f"Project name {proposed_name} cannot start with a number. Please choose a name that starts with a letter."
        )

    if project_dir.exists():
        if project_dir.is_file():
            click.echo(
                f"Path {project_dir} was a file. Please choose a new directory.",
                err=True,
            )
        if project_dir.is_dir() and any(project_dir.iterdir()):
            click.echo(
                f"Directory {project_dir} was not empty! Please choose a new or empty directory"
            )
    else:
        project_dir.mkdir(parents=True, exist_ok=True)

    python_module_name = proposed_name.lower().replace(" ", "_").replace("-", "_")
    python_package_name = python_module_name.replace("_", "-")

    return _NamesAndDirs(
        path=project_dir,
        e80_name=proposed_name,
        python_module=python_module_name,
        python_package=python_package_name,
    )


def build_initial_file(project_name: str) -> str:
    # TODO: Put an actual example that calls to the LLM here.
    return f"""from e80_sdk import Eighty80, eighty80_app

app = eighty80_app()

# Get an OpenAI SDK-compatible object to talk to the 8080 
api = Eighty80().completion_sdk()

# If you previously saved OpenAI SDK credentials to the 8080 platform,
# you can quickly create an OpenAI SDK like this:
# another_openai_compatible_api = Eighty80().completion_sdk("secret_name")

@app.get("/example")
def completion_example():
    # For more information about the OpenAI SDK, see the OpenAI SDK API reference here:
    # https://platform.openai.com/docs/api-reference/chat/create
    return api.chat.completions.create(
        messages=[
            {{
                "role": "user",
                "content": "Tell me a joke."
            }}
        ],
        model="gpt-oss-20b",
        stream=False,
    )


@app.get("/")
def hello_world():
    return {{"message": "Hello from {project_name}" }}
"""


def build_pyproject(python_project_name: str) -> str:
    # TODO: Put the 8080 SDK as a dependency in here once it's released.
    return f"""[project]
name = "{python_project_name}"
version = "0.1.0"
description = "A 8080 cloud project."
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "e80-sdk>={E80_VERSION}",
]

[dependency-groups]
dev = [
  "uvicorn>=0.38.0",
]"""


def build_gpu_pyproject(python_project_name: str) -> str:
    return f"""[project]
name = "{python_project_name}"
version = "0.1.0"
description = "A 8080 cloud project."
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "e80-sdk>={E80_VERSION}",
    "torch==2.9.1+cu130",
]

[dependency-groups]
dev = [
  "uvicorn>=0.38.0",
]

[tool.uv.sources]
torch = [
  {{ index = "pytorch" }},
]

# This version of pytorch matches
# the CUDA version on the 8080 base image.
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu130"
explicit = true
"""


def build_readme(project_name: str) -> str:
    return f"""# {project_name}

This is an 8080 project, made using the `{E80_COMMAND} init` command.

## Running

To run the dev server, run `{E80_COMMAND} dev` in your terminal.

## Deploy to 8080

To build the artifact and deploy it to 8080, run `{E80_COMMAND} deploy` in your terminal.
"""


def build_agents_md(project_name: str) -> str:
    return f"""# Project Guidelines

## Project Structure & Module Organization

- `{project_name}/` contains the app code. The entrypoint is `{project_name}.main:app`.
- `pyproject.toml` declares dependencies and metadata.

## Build and Development Commands

- `{E80_COMMAND} dev`: run the dev server.
- `{E80_COMMAND} deploy`: build and deploy the project.

## Coding Style & Naming Conventions

- Language: Python 3.13+.
- Follow PEP 8 (4-space indentation, `snake_case` for functions/vars, `PascalCase` for classes).
"""
