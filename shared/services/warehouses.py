# shared/services/warehouses
import os

from main.models import Warehouse

from shared.exceptions import ConfigurationException


def init_warehouses(config):
    default_warehouse = Warehouse.objects.filter(is_default=True).first()
    if not default_warehouse:
        default = config["default_warehouse"]
        default["path"] = os.path.abspath(default["path"])
        create_warehouse(**default)


def list_warehouses():
    return Warehouse.objects.all()


def create_warehouse(name, path, is_default):
    # Check if the path exists
    if not os.path.exists(path):
        parent_folder = os.path.dirname(path)
        # Check if the parent folder exists
        if os.path.exists(parent_folder):
            # Create the subfolder
            os.makedirs(path)
            # Log that a folder was created with path
        else:
            raise ConfigurationException(
                f"Directory or parent does not exist: {path}"
            )

    Warehouse.objects.create(name=name, path=path, is_default=is_default)


class BadFilePathException(Exception):
    pass
