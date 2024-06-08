# shared/services/warehouses
# Standard Library
import os

# Third Party
from django.db.utils import IntegrityError

# First Party
from main.models import Warehouse
from shared.exceptions import AfConfigurationException, AfDuplicateException


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
            raise AfConfigurationException(
                f"Directory or parent does not exist: {path}"
            )
    try:
        Warehouse.objects.create(name=name, path=path, is_default=is_default)
    except IntegrityError:
        raise AfDuplicateException


def delete_warehouse(id):
    Warehouse.objects.filter(id=id).first().delete()


class BadFilePathException(Exception):
    pass
