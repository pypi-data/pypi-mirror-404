import unittest
from pathlib import Path

from e80.archive import (
    _base_image_for_archive,
    _build_docker_run_command,
    _build_shell_command,
)


class ArchiveCommandTests(unittest.TestCase):
    def test_base_image_for_http(self) -> None:
        self.assertEqual(
            _base_image_for_archive(False),
            "ghcr.io/astral-sh/uv:python3.13-alpine",
        )

    def test_base_image_for_cuda(self) -> None:
        self.assertEqual(
            _base_image_for_archive(True),
            "ghcr.io/astral-sh/uv:python3.13-trixie",
        )

    def test_shell_command_includes_build_requirements(self) -> None:
        command = _build_shell_command(
            build_system_requirements=["hatchling", "setuptools"],
            python_version="3.13",
        )

        self.assertIn("uv pip install hatchling setuptools;", command)
        self.assertIn("uv pip compile /builder/pyproject.toml", command)
        self.assertIn("--python-version 3.13", command)
        self.assertIn("uv pip install --target /builder/output", command)
        self.assertIn("done < /builder/local_sources.txt;", command)

    def test_shell_command_skips_build_requirements_when_empty(self) -> None:
        command = _build_shell_command(
            build_system_requirements=[],
            python_version="3.13",
        )

        self.assertNotIn("uv pip install ;", command)
        self.assertNotIn("uv pip install ;", command)
        self.assertIn("uv pip compile /builder/pyproject.toml", command)

    def test_build_docker_run_command_layout(self) -> None:
        command = _build_docker_run_command(
            base_image="ghcr.io/astral-sh/uv:python3.13-alpine",
            pyproject_path=Path("/tmp/project/pyproject.toml"),
            project_root=Path("/tmp/project"),
            packages_path=Path("/tmp/output"),
            constraints_path=Path("/tmp/constraints.txt"),
            local_sources_path=Path("/tmp/local_sources.txt"),
            shell_command="echo ok",
        )

        self.assertEqual(command[0:3], ["docker", "run", "--rm"])
        self.assertIn("/tmp/project/pyproject.toml:/builder/pyproject.toml", command)
        self.assertIn("/tmp/project:/builder/project", command)
        self.assertIn("/tmp/output:/builder/output", command)
        self.assertIn("/tmp/constraints.txt:/builder/constraints.txt", command)
        self.assertIn("/tmp/local_sources.txt:/builder/local_sources.txt", command)
        self.assertEqual(command[-3:], ["/bin/sh", "-c", "echo ok"])

