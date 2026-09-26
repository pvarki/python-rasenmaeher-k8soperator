"""Test the rmcli exploration CLI"""

from typing import Any

import httpx
import pytest
from click.testing import CliRunner

from cli import __version__
from cli import console
from cli.console import rmcli


def _fake_get(status_code: int, payload: dict[str, str], seen: list[str]) -> Any:
    """Build an httpx.get replacement that records the requested URL."""

    def fake_get(url: str, timeout: float) -> httpx.Response:
        seen.append(url)
        return httpx.Response(status_code, json=payload, request=httpx.Request("GET", url))

    return fake_get


def test_version() -> None:
    """--version prints the package version"""
    result = CliRunner().invoke(rmcli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_healthcheck_prints_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """healthcheck calls the endpoint under --api-url and prints the JSON"""
    seen: list[str] = []
    monkeypatch.setattr(console.httpx, "get", _fake_get(200, {"dns": "localmaeher.dev.pvarki.fi"}, seen))
    result = CliRunner().invoke(rmcli, ["--api-url", "http://localhost:18000/", "healthcheck"])
    assert result.exit_code == 0, result.output
    assert seen == ["http://localhost:18000/api/v1/healthcheck"]
    assert '"dns": "localmaeher.dev.pvarki.fi"' in result.output


def test_healthcheck_uses_env_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """RMCLI_API_URL sets the API base URL"""
    seen: list[str] = []
    monkeypatch.setattr(console.httpx, "get", _fake_get(200, {}, seen))
    result = CliRunner().invoke(rmcli, ["healthcheck"], env={"RMCLI_API_URL": "http://rmapi:8000"})
    assert result.exit_code == 0, result.output
    assert seen == ["http://rmapi:8000/api/v1/healthcheck"]


def test_healthcheck_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-2xx responses exit non-zero with a readable message"""
    monkeypatch.setattr(console.httpx, "get", _fake_get(503, {}, []))
    result = CliRunner().invoke(rmcli, ["healthcheck"])
    assert result.exit_code == 1
    assert "Healthcheck failed" in result.output
