#!/usr/bin/env python3
import click

from cli.commands.foreman import foreman
from cli.commands.run import run
from cli.commands.server import server
from cli.commands.worker import worker
from config.config import load_config
from config.init import check_initialised

# Load configuration and check initialization
config = load_config()
check_initialised(config)


@click.group()
def cli():
    pass


@cli.command()
def warehouse():
    click.echo("Listing warehouses...")
    # Logic to list warehouses


cli.add_command(run)
cli.add_command(server)
cli.add_command(worker)
cli.add_command(foreman)

if __name__ == "__main__":
    cli()
