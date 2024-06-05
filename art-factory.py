#!/usr/bin/env python3

import os
import sys

import click

# Ensure the shared module can be imported
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "shared"))
)

from cli.commands.foreman import foreman
from cli.commands.run import run
from cli.commands.server import server
from cli.commands.worker import worker


@click.group()
def cli():
    pass


cli.add_command(run)
cli.add_command(server)
cli.add_command(worker)
cli.add_command(foreman)

if __name__ == "__main__":
    cli()
