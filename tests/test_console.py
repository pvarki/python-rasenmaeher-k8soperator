"""Test CLI scripts"""

import asyncio
import sys

import pytest
from click.testing import CliRunner
from libadvian.binpackers import ensure_str

from operator import __version__
from operator.console import rmk8soperator_cli


@pytest.mark.asyncio
async def test_version_cli() -> None:
    """Test the CLI parsing for default version dumping works"""
    cmd = f"{sys.executable} -m rmk8soperator --version"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out = await asyncio.wait_for(process.communicate(), 10)
    # Demand clean exit
    assert process.returncode == 0
    # Check output
    assert ensure_str(out[0]).strip().endswith(__version__)


@pytest.mark.asyncio
async def test_cli_manifests() -> None:
    """manifests prints CRD YAML without talking to a cluster."""
    cmd = f"{sys.executable} -m rmk8soperator manifests --without-webhooks"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out = await asyncio.wait_for(process.communicate(), 15)
    assert process.returncode == 0, ensure_str(out[1])
    stdout = ensure_str(out[0])
    assert "kind: CustomResourceDefinition" in stdout
    assert "users.platform.opendefence.fi" in stdout
    assert "invites.platform.opendefence.fi" in stdout
    assert "userbindings.platform.opendefence.fi" in stdout


def test_verbose_logging_flags() -> None:
    """-v and -vv select info and debug log levels before a subcommand runs."""
    runner = CliRunner()
    info = runner.invoke(rmk8soperator_cli, ["-v", "manifests", "--without-webhooks"])
    debug = runner.invoke(rmk8soperator_cli, ["-vv", "manifests", "--without-webhooks"])
    assert info.exit_code == 0
    assert debug.exit_code == 0
    assert "CustomResourceDefinition" in info.output
