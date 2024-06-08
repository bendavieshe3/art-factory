# Third Party
import click

# First Party
from shared.messages import get_test_message


@click.command()
def run():
    """Run the main operation and display the test message."""
    click.echo("Running main operation...")
    message = get_test_message()
    click.echo(message)
