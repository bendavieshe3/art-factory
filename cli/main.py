#!/usr/bin/env python3
import os
import sys

import click
from commands.foreman import foreman
from commands.run import run
from commands.server import server
from commands.worker import worker

# Ensure the shared module can be imported
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


@click.group()
def cli():
    pass


cli.add_command(run)
cli.add_command(server)
cli.add_command(worker)
cli.add_command(foreman)

if __name__ == "__main__":
    cli()
