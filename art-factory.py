#!/usr/bin/env python3
# Third Party
import click

"""
Reserved general switches

-p --preview
-v --verbose
__ --debug

Reserved general options



Reserved command options


(without optons) - show a list

-c <params> -create
-r <id> --read
-u <id> <params> --update
-d <id> --delete
__ <id> --make-default

"""


# First Party
# Load configuration and check initialization
from config.config import load_config
from config.init import check_initialised

ERR_COLOR = "red"

config = load_config()
check_initialised(config)

click.secho("Art Factory", fg="green")

# First Party
from cli.commands.foreman import foreman
from cli.commands.run import run
from cli.commands.server import server
from cli.commands.warehouse import warehouse
from cli.commands.worker import worker


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
