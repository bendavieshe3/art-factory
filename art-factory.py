#!/usr/bin/env python3
import click

from cli.commands.foreman import foreman
from cli.commands.run import run
from cli.commands.server import server
from cli.commands.warehouse import warehouse
from cli.commands.worker import worker
from config.config import load_config
from config.init import check_initialised

click.secho("Art Factory", fg="green")

# Load configuration and check initialization
config = load_config()
check_initialised(config)


@click.group()
def cli():
    pass


cli.add_command(run)
cli.add_command(server)
cli.add_command(worker)
cli.add_command(foreman)
cli.add_command(warehouse)

if __name__ == "__main__":
    cli()
