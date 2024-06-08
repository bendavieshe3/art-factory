# Standard Library
import subprocess
import sys

# Third Party
import click


@click.command()
def worker():
    """Start the worker process."""
    click.echo("Starting worker process...")
    subprocess.run([sys.executable, "processes/worker_process.py"])
