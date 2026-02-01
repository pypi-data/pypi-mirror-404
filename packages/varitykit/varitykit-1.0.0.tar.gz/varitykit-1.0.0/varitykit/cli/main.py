"""
Main CLI entry point for VarityKit
"""

from pathlib import Path

import click
from varitykit import __version__
from varitykit.utils.logger import get_logger, set_log_level


# Global options
@click.group()
@click.version_option(version=__version__, prog_name="varitykit")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.option("--json", "json_format", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx, verbose, debug, json_format):
    """
    VarityKit - Build and deploy applications on Varity

    Build, test, and deploy applications with ease.
    """
    # Setup logging
    if debug:
        set_log_level("DEBUG")
    elif verbose:
        set_log_level("INFO")
    else:
        set_log_level("WARNING")

    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug
    ctx.obj["json_format"] = json_format
    ctx.obj["logger"] = get_logger(
        level="DEBUG" if debug else ("INFO" if verbose else "WARNING"), json_format=json_format
    )


from varitykit.cli.bootstrap import bootstrap
from varitykit.cli.completions import completions
from varitykit.cli.contract import contract
from varitykit.cli.deploy import deploy
from varitykit.cli.dev import dev

# Import commands
from varitykit.cli.doctor import doctor
from varitykit.cli.fund import fund
from varitykit.cli.init import init
from varitykit.cli.localdepin import localdepin
from varitykit.cli.localnet import localnet
from varitykit.cli.marketing import marketing
from varitykit.cli.marketplace import marketplace
from varitykit.cli.migrate import migrate
from varitykit.cli.task import task
from varitykit.cli.template import template
from varitykit.cli.thirdweb import thirdweb
from varitykit.commands.app_deploy import app
from varitykit.commands.billing import billing
from varitykit.commands.setup import setup


# Advanced command group (hidden from main help)
@cli.group(hidden=True)
def advanced():
    """Advanced commands for blockchain developers"""
    pass


# Register main commands
cli.add_command(setup)
cli.add_command(doctor)
cli.add_command(init)
cli.add_command(bootstrap)
cli.add_command(completions)
cli.add_command(task)
cli.add_command(fund)
cli.add_command(dev)
cli.add_command(localnet)
cli.add_command(localdepin)
cli.add_command(template)
cli.add_command(marketplace)
cli.add_command(marketing)
cli.add_command(migrate)
cli.add_command(app)
cli.add_command(billing)

# Register advanced commands (hidden from main help)
advanced.add_command(deploy)
advanced.add_command(contract)
advanced.add_command(thirdweb)
cli.add_command(advanced)


if __name__ == "__main__":
    cli()
