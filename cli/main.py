#!/usr/bin/env python3
import os
import sys

import click
from commands.run import run
from commands.server import server

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


@click.group()
def cli():
    pass


cli.add_command(run)
cli.add_command(server)

if __name__ == "__main__":
    cli()
