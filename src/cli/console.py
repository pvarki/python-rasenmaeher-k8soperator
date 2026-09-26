"""CLI entrypoints for exploring a running RASENMAEHER deployment"""

import json
import logging

import click
import httpx

from libadvian.logging import init_logging
from cloudcoil.apimachinery import ObjectMeta
from cloudcoil.errors import APIError

from api.lib.common.codes import generate_code
from cli import __version__
from k8soperator.models.v1alpha1.common import API_VERSION, ObjectRef
from k8soperator.models.v1alpha1.invite import Invite, InviteSpec


LOGGER = logging.getLogger(__name__)
DEFAULT_API_URL = "http://rmapi.opendefence-system.svc.cluster.local:8000"
ADMIN_CODE_LENGTH = 16


def _configure_logging(loglevel: int, verbose: int) -> None:
    """Apply verbose shorthand and initialize logging."""
    if verbose == 1:
        loglevel = 20
    if verbose >= 2:
        loglevel = 10
    init_logging(loglevel)
    LOGGER.setLevel(loglevel)


@click.group()
@click.version_option(version=__version__)
@click.option("-l", "--loglevel", help="Python log level, 10=DEBUG, 20=INFO, 30=WARNING, 40=CRITICAL", default=30)
@click.option("-v", "--verbose", count=True, help="Shorthand for info/debug loglevel (-v/-vv)")
@click.option(
    "--api-url",
    envvar="RMCLI_API_URL",
    default=DEFAULT_API_URL,
    show_default=True,
    help="Base URL of the RASENMAEHER API",
)
@click.pass_context
def rmcli(ctx: click.Context, loglevel: int, verbose: int, api_url: str) -> None:
    """Explore a running RASENMAEHER deployment"""
    _configure_logging(loglevel, verbose)
    ctx.obj = api_url.rstrip("/")


@rmcli.command()
@click.option("--timeout", default=5.0, show_default=True, help="Request timeout in seconds")
@click.pass_obj
def healthcheck(api_url: str, timeout: float) -> None:
    """Call the API healthcheck endpoint and print its response."""
    url = f"{api_url}/api/v1/healthcheck"
    LOGGER.debug("GET %s", url)
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise click.ClickException(f"Healthcheck failed: {exc}") from exc
    click.echo(json.dumps(response.json(), indent=2))


@rmcli.command(name="addcode")
def add_code() -> None:
    """Create a single-use invite that makes an approved superadmin, and print its code."""
    code = generate_code(ADMIN_CODE_LENGTH)
    try:
        Invite(
            api_version=API_VERSION,
            kind="Invite",
            metadata=ObjectMeta(generate_name="admin-"),
            spec=InviteSpec(
                code=code,
                role_refs=[ObjectRef(name="superadmin")],
                use_count=1,
                auto_approve=True,
            ),
        ).create()
    except APIError as exc:
        raise click.ClickException(f"Creating invite failed: {exc}") from exc
    click.echo(code)
