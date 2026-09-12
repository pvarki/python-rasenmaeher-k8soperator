"""Provider selection shared by the local cluster tasks and Tilt."""

import asyncio
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ["Linux", "Darwin"])
@pytest.mark.parametrize("provider", [None, "", "docker", "podman", "invalid"])
async def test_runtime_selection(tmp_path: Path, platform: str, provider: str | None) -> None:
    """Linux needs only Docker; explicit providers override both platform defaults."""
    uname = tmp_path / "uname"
    uname.write_text('#!/bin/sh\nprintf "%s\\n" "$TEST_PLATFORM"\n')
    uname.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}", TEST_PLATFORM=platform)
    env.pop("KIND_EXPERIMENTAL_PROVIDER", None)
    if provider is not None:
        env["KIND_EXPERIMENTAL_PROVIDER"] = provider

    # The first command is used by Tilt; the second verifies task exports.
    commands = [
        ["bash", str(ROOT / "tilt/runtime.sh")],
        [
            "bash",
            "-euc",
            'source "$1"; test "$RUNTIME" = "$KIND_EXPERIMENTAL_PROVIDER"; '
            'bash -c \'printf "%s\\n" "$KIND_EXPERIMENTAL_PROVIDER"\'',
            "runtime-test",
            str(ROOT / "tilt/env.sh"),
        ],
    ]
    for command in commands:
        process = await asyncio.create_subprocess_exec(
            *command,
            env=env,
            cwd=tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        if provider == "invalid":
            assert process.returncode != 0
            assert stdout == b""
            assert b"KIND_EXPERIMENTAL_PROVIDER must be docker or podman" in stderr
        else:
            expected = provider or ("docker" if platform == "Linux" else "podman")
            assert process.returncode == 0, stderr.decode()
            assert stdout.decode().strip() == expected
