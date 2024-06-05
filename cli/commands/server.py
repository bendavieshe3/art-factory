import subprocess

import click


@click.command()
@click.option(
    "--dev", is_flag=True, help="Run the server in development mode."
)
def server(dev):
    """Run the Django development server."""
    if dev:
        click.echo("Starting Django development server...")
        subprocess.run(["python", "web/manage.py", "runserver"])
    else:
        click.echo("Starting production server...")
        subprocess.run(
            [
                "python",
                "web/manage.py",
                "runserver",
                "--settings=art_factory.production_settings",
            ]
        )
