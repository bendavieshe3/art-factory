import click

from shared.messages import get_test_message


@click.command()
def run():
    """Run the main operation and display the test message."""
    click.echo("Running main operation...")
    message = get_test_message()
    click.echo(message)


if __name__ == "__main__":
    run()
