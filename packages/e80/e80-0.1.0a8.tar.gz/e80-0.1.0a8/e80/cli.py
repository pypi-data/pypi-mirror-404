import rich_click as click

from typing import Any
from rich.tree import Tree
from rich import print as rich_print
from rich.prompt import Prompt, IntPrompt
from collections import defaultdict
from pathlib import Path
from e80_sdk import Eighty80

from e80.oauth_handler import start_oauth_flow
from e80.init import init_project
from e80.archive import archive_project
from e80.deploy import deploy_project
from e80.dev import run_dev_server
from e80.lib.constants import E80_VERSION
from e80.lib.sdk import get_sdk_environment
from e80.lib.dependencies import require_uv, require_docker
from e80.lib.prompt import require_tty, tty_or_pipe
from e80.lib.context import E80ContextObject, must_get_ctx_object


@click.group()
@click.option(
    "--config",
    type=click.Path(path_type=Path, dir_okay=False, file_okay=True, exists=False),
    help="Path to 8080.yaml or the directory containing it.",
)
@click.option("--e80-api-host", type=str, envvar="E80_API_HOST", hidden=True)
@click.option("--e80-platform-host", type=str, envvar="E80_PLATFORM_HOST", hidden=True)
@click.version_option(E80_VERSION)
@click.option("--verbose", is_flag=True)
@click.pass_context
def cli(
    ctx: click.Context,
    config: Path | None,
    e80_api_host: str | None,
    e80_platform_host: str | None,
    verbose: bool,
) -> None:
    """CLI tool for creating projects and interacting with the 8080 platform."""
    ctx.obj = E80ContextObject(
        api_host=e80_api_host.rstrip("/") if e80_api_host else "https://api.8080.io",
        config_path=config,
        platform_host=e80_platform_host.rstrip("/")
        if e80_platform_host
        else "https://app.8080.io",
        verbose=verbose,
    )


@cli.command()
@click.pass_context
def archive(ctx: click.Context) -> None:
    """Just build this project."""
    require_uv()
    require_docker()

    archive_project(must_get_ctx_object(ctx))


@cli.command()
@click.option("--bind", default="0.0.0.0", help="Interface to bind the dev server to")
@click.option(
    "--port", default=8080, type=int, help="The port to bind the dev server to"
)
@click.option("--no-reload", is_flag=True, default=False, help="Disable hot reloading")
@click.pass_context
def dev(ctx: click.Context, bind, port, no_reload) -> None:
    """Runs the dev server."""
    run_dev_server(
        must_get_ctx_object(ctx),
        bind,
        port,
        not no_reload,
    )


@cli.command()
@click.option("--artifact-id", default=None, help="Redeploy this artifact ID")
@click.option(
    "--no-build",
    is_flag=True,
    help="Do not create a new archive locally",
)
@click.pass_context
def deploy(ctx: click.Context, artifact_id, no_build: bool) -> None:
    """Builds and deploys this project."""
    require_uv()
    require_docker()

    deploy_project(must_get_ctx_object(ctx), artifact_id, no_build)


@cli.command()
@click.argument(
    "directory",
    help="Optional. The name of the directory to create and initialize the project in. If not given, it will initialize the project inside the current directory.",
    type=str,
    required=False,
)
@click.option(
    "--git/--no-git",
    is_flag=True,
    help="Initialize a git repository inside the directory",
)
@click.option(
    "--gpu-count",
    type=int,
    default=0,
    help="Number of GPUs. Setting this to a value over 0 will add 'torch' as a dependency.",
)
@click.option("--cpu-mhz", "cpu", type=int, default=500, help="CPU reserved MHz.")
@click.option(
    "--memory-size-mb",
    "memory_size_mb",
    type=int,
    default=256,
    help="Memory size in MB.",
)
@click.option(
    "--org",
    "organization_slug",
    help="Organization slug to create the project under (skips prompt).",
)
@click.option("--project", "project_slug", help="The existing project slug")
@click.pass_context
def init(
    ctx: click.Context,
    directory: str | None,
    gpu_count: int,
    cpu: int,
    memory_size_mb: int,
    organization_slug: str | None,
    project_slug: str | None,
    git: bool,
) -> None:
    """Initializes an 8080 cloud project."""
    require_uv()
    init_project(
        must_get_ctx_object(ctx),
        install_path=directory,
        gpu_count=gpu_count,
        cpu=cpu,
        memory_size_mb=memory_size_mb,
        organization_slug=organization_slug,
        project_slug=project_slug,
        use_git=git,
    )


@cli.command()
@click.pass_context
def login(ctx: click.Context) -> None:
    """Login into 8080 and fetch an access token."""
    start_oauth_flow(must_get_ctx_object(ctx))


@cli.command()
@click.option(
    "--json",
    "json_output",
    default=False,
    is_flag=True,
    help="Return the response as JSON",
)
@click.pass_context
def models(ctx: click.Context, json_output: bool) -> None:
    """List all models."""
    env, secrets = get_sdk_environment(must_get_ctx_object(ctx))
    models = Eighty80(env=env, secrets=secrets).completion_sdk().models.list()

    if json_output:
        click.echo(models.model_dump_json())
    else:
        by_provider = defaultdict(list)
        for model in models.data:
            by_provider[model.owned_by].append(model)
        for provider, model_list in by_provider.items():
            tree = Tree(f"[bold]{provider}[/]", guide_style="grey42")
            for model in sorted(model_list, key=lambda x: x.id):
                tree.add(f"{model.id}")
            rich_print(tree)


@cli.command()
@click.argument("text", type=str, required=False)
@click.option("--model", default=None, help="Model to use (optional)")
@click.option("--system", help="System message (optional)")
@click.option(
    "--temperature",
    default=1,
    type=float,
    show_default=True,
    help="Sampling temperature",
)
@click.option(
    "--max-tokens",
    type=int,
    default=None,
    help="Maximum tokens to generate (leave empty for model default)",
)
@click.option("--stream", default=False, is_flag=True, help="Stream the response")
@click.option(
    "--json",
    "json_output",
    default=False,
    is_flag=True,
    help="Return the response as JSON",
)
@click.pass_context
def chat(
    ctx: click.Context,
    text: str | None,
    model: str | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
    stream: bool,
    json_output: bool,
) -> None:
    """Chat with a model."""
    env, secrets = get_sdk_environment(must_get_ctx_object(ctx))
    app = Eighty80(env=env, secrets=secrets).completion_sdk()

    _emph = "bold bright_blue"

    if text is None:
        text = tty_or_pipe()
    if text is None:
        text = Prompt.ask("[white]Message[/white]")

    if model is None:
        models_resp = app.models.list()
        if not models_resp.data:
            raise click.ClickException("No models available to select.")
        rich_print("[white]Available models:[/white]")
        for idx, m in enumerate(models_resp.data):
            rich_print(f"[{_emph}][{idx}][/{_emph}] {m.id} ({m.owned_by})")

        require_tty("--model")
        selection = IntPrompt.ask(
            "[white]Select a model[/white]",
            default=0,
            choices=[str(i) for i in range(0, len(models_resp.data))],
        )

        model = models_resp.data[selection].id

    # OpenAI SDK makes typing this hard, since we can't import the type
    messages: Any = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": text})

    # We want to use custom fields, which won't be part of the type.
    # For the sake of ease, we type the CompletionUsage as Any.
    completion_usage: Any = None

    if stream:
        sresp = app.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream_options={"include_usage": True},
            stream=True,
        )
        for stream_chunk in sresp:
            if json_output:
                click.echo(stream_chunk.model_dump_json())
            else:
                if stream_chunk.choices:
                    click.echo(stream_chunk.choices[0].delta.content)
                if stream_chunk.usage:
                    completion_usage = stream_chunk.usage

    else:
        resp = app.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        if json_output:
            click.echo(resp.model_dump_json())
        else:
            click.echo(resp.choices[0].message.content)
            completion_usage = resp.usage

    if hasattr(completion_usage, "prefill_tokens"):
        usage_values = [
            ("time", completion_usage.total_time, "s"),
            (
                "prefill_tokens",
                completion_usage.prefill_tokens,
                " tokens",
            ),
            ("decode_tokens", completion_usage.decode_tokens, " tokens"),
            ("prefill_rate", completion_usage.prefill_rate, "tps"),
            ("decode_rate", completion_usage.decode_rate, "tps"),
        ]
        rich_print(
            " ".join(f"{n}: [{_emph}]{v}{u}[/{_emph}]" for n, v, u in usage_values)
        )


def main():
    """Entry point for the CLI tool."""
    cli()
