import subprocess
import sys

import click


@click.command()
def foreman():
    """Start the foreman process."""
    click.echo("Starting foreman process...")
    subprocess.run([sys.executable, "processes/foreman_process.py"])
