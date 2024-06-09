# shared/services/warehouses
# Standard Library
import os

# Third Party
from django.db.utils import IntegrityError

# First Party
from main.models import Warehouse
from shared.exceptions import (
    AfConfigurationException,
    AfDoesNotExistException,
    AfDuplicateException,
)


def init_warehouses(config):
    default_warehouse = Warehouse.objects.filter(is_default=True).first()
    if not default_warehouse:
        default = config["default_warehouse"]
        default["path"] = os.path.abspath(default["path"])
        create_warehouse(**default)


def list_warehouses():
    return Warehouse.objects.all()


def create_warehouse(name, path, is_default=False):
    abs_path = check_and_make_valid_path_param(path)
    try:
        wh = Warehouse.objects.create(
            name=name, path=abs_path, is_default=is_default
        )
        if is_default:
            # find any other defaults and unset them
            other_default_warehouses = Warehouse.objects.filter(
                # id != wh.id,
                is_default=True,
            ).all()
            for other_warehouse in other_default_warehouses:
                if other_warehouse.id != wh.id:
                    other_warehouse.is_default = False
                    other_warehouse.save()

        return wh

    except IntegrityError:
        raise AfDuplicateException


def delete_warehouse(id):
    wh = Warehouse.objects.filter(id=id).first()
    if wh:
        wh.delete()
    else:
        raise AfDoesNotExistException(
            f"A warehouse with ID {id} does not exist"
        )


def check_and_make_valid_path_param(path):
    """Checks to see if path or path's parent exists. If parent creates
    child directory. If not exists throws configuration error. Returns
    absolute path"""

    if not os.path.exists(path):
        parent_folder = os.path.dirname(path)
        if os.path.exists(parent_folder):
            os.makedirs(path)
        else:
            raise AfConfigurationException(
                f"Directory or parent does not exist: {path}"
            )
    return os.path.abspath(path)
