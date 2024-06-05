import subprocess
import sys

import click


@click.command()
def worker():
    """Start the worker process."""
    click.echo("Starting worker process...")
    subprocess.run([sys.executable, "processes/worker_process.py"])
