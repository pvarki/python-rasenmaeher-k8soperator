"""CLI entrypoints for rasenmaeher-k8soperator"""

import logging

import click

from libadvian.logging import init_logging
from rmk8soperator import __version__
from rmk8soperator.app import app


LOGGER = logging.getLogger(__name__)


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
def rmk8soperator_cli(loglevel: int, verbose: int) -> None:
    """K8s Operator and CRDs with core RASENMAEHER entities"""
    _configure_logging(loglevel, verbose)


@rmk8soperator_cli.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": False,
    }
)
@click.pass_context
def manifests(ctx: click.Context) -> None:
    """Print CRD, RBAC, and optional Deployment manifests (offline)."""
    app.main(["manifests", *ctx.args])


@rmk8soperator_cli.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": False,
    }
)
@click.pass_context
def install(ctx: click.Context) -> None:
    """Apply CRDs and runtime RBAC using the current kubeconfig."""
    app.main(["install", *ctx.args])


@rmk8soperator_cli.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": False,
    }
)
@click.pass_context
def run(ctx: click.Context) -> None:
    """Run the operator against the current cluster."""
    app.main(["run", *ctx.args])
