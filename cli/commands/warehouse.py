# Third Party
import click

# First Party
from shared.exceptions import AfDoesNotExistException
from shared.services.warehouses import (
    create_warehouse,
    delete_warehouse,
    list_warehouses,
)

ERR_COLOR = "red"


@click.group(invoke_without_command=True)
@click.pass_context
def warehouse(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(list)


@warehouse.command(name="list", help="lists warehouses")
def list():
    """Performs CLI operations on warehouses."""
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


@warehouse.command(name="delete", help="Delete a warehouse.")
@click.option("--id", type=int, required=True, help="Warehouse ID")
def delete(id):
    try:
        delete_warehouse(id=id)
        click.echo(f"Warehouse {id} deleted successfully.")
    except AfDoesNotExistException:
        click.secho(f"A warehouse with ID {id} does not exist.", fg=ERR_COLOR)
    except Exception as e:
        click.secho(f"Error deleting warehouse: {e}", fg=ERR_COLOR)


@warehouse.command(name="create", help="Create a warehouse")
@click.option("--name", required=True, help="Name of the warehouse")
@click.option("--path", required=True, help="Path used for file storage")
@click.option(
    "--default",
    type=bool,
    required=False,
    default=False,
    help="Make this the default",
)
def create(name, path, default):
    try:
        create_warehouse(name, path, default)
        click.echo("Warehouse created successfully.")
    except Exception as e:
        click.echo(f"Error creating warehouse: {e.message}")
