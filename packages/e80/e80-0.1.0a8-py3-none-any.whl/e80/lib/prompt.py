import sys
import click


def require_tty(option: str):
    if not sys.stdin.isatty():
        raise click.UsageError(f"Non-interactive mode. Please set '{option}'.")


def tty_or_pipe() -> str | None:
    if sys.stdin.isatty():
        return None
    piped = sys.stdin.read()
    if not piped:
        raise click.UsageError("Non-interactive mode. Please enter an argument.")
    return piped
