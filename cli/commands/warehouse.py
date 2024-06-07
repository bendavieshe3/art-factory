import click

from shared.services.warehouses import list_warehouses


@click.command()
def warehouse():
    """Return a list of warehouses."""
    click.echo("Listing warehouses...\n")
    warehouses = list_warehouses()
    table_row = "{:<5} {:<1} {:<20} {:<5}"
    click.echo(table_row.format("id", "", "name", "path"))
    for wh in warehouses:
        click.echo(
            table_row.format(
                wh.id, ("*" if wh.is_default else ""), wh.name, wh.path
            )
        )
    click.echo(f"\n{warehouses.count()} total warehouse(s).\n")
