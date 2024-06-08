# Third Party
import click

# First Party
from shared.exceptions import AfDoesNotExist
from shared.services.warehouses import delete_warehouse, list_warehouses


@click.command(
    help="Perform operations with warehouses. Lists warehouses by default."
)
@click.option("--delete", type=int, help="Delete warehouse by ID")
def warehouse(delete):
    """Performs CLI operations on warehouses."""
    if delete:
        try:
            delete_warehouse(id=delete)
            click.echo(f"Warehouse {delete} deleted successfully.")
        except AfDoesNotExist:
            click.echo(f"Warehouse with ID {delete} does not exist.")
        except Exception as e:
            click.echo(f"Error deleting warehouse: {e}")
    else:
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
