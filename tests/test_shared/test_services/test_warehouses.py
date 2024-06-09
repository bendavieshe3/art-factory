# Standard Library
import os

# Third Party
import pytest
from django.core.management import call_command

# First Party
from shared.exceptions import AfDoesNotExistException, AfDuplicateException


# @pytest.fixture(scope="session", autouse=True)
def django_setup():
    os.environ["DJANGO_SETTINGS_MODULE"] = "art_factory.settings"

    # Third Party
    import django

    django.setup()

    # Run migrations before tests
    call_command("migrate")


django_setup()
test_dirs = []


# First Party
from main.models import Warehouse
from shared.services.warehouses import (
    create_warehouse,
    delete_warehouse,
    init_warehouses,
)


@pytest.fixture(scope="session", autouse=True)
def django_setup():
    yield

    Warehouse.objects.all().delete()
    for test_dir in test_dirs:
        if os.path.exists(test_dir) and not os.listdir(test_dir):
            os.rmdir(test_dir)


@pytest.fixture
def default_config():
    return {
        "default_warehouse": {
            "name": "Default",
            "path": "default_warehouse",
            "is_default": True,
        }
    }


# init_warehouses


@pytest.mark.django_db
def test_init_warehouses_creates_default_warehouse(default_config):
    init_warehouses(default_config)
    default_warehouse = Warehouse.objects.get(is_default=True)
    assert default_warehouse.name == "Default"
    assert os.path.isabs(default_warehouse.path)


@pytest.mark.django_db
def test_init_warehouses_does_not_create_if_exists(default_config):
    Warehouse.objects.create(
        name="Default",
        path=os.path.abspath("default_warehouse"),
        is_default=True,
    )
    init_warehouses(default_config)
    warehouses = Warehouse.objects.filter(is_default=True)
    assert warehouses.count() == 1


# create_warehouse


@pytest.mark.django_db
def test_create_warehouse_duplicate_paths_cause_exception(default_config):
    with pytest.raises(AfDuplicateException):
        Warehouse.objects.create(
            name="a",
            path=os.path.abspath("default_warehouse"),
            is_default=True,
        )
        create_warehouse(
            name="b",
            path=os.path.abspath("default_warehouse"),
            is_default=True,
        )


def test_create_warehouse_keeps_single_default(default_config):
    init_warehouses(default_config)
    test_dirs.append("default_warehouse_test")
    create_warehouse(
        name="a",
        path=os.path.abspath("default_warehouse_test"),
        is_default=True,
    )
    default_warehouses = Warehouse.objects.filter(is_default=True)
    assert default_warehouses.count() == 1


def test_create_warehouse_defaults_is_default_to_false(default_config):
    init_warehouses(default_config)
    test_dirs.append("./warehouse_test_1")
    warehouse = create_warehouse(name="a", path="./warehouse_test_1")
    assert not warehouse.is_default


def test_create_warehouse_saves_absolute_path(default_config):
    init_warehouses(default_config)
    test_dirs.append("./warehouse_test_2")
    warehouse = create_warehouse(name="a", path="./warehouse_test_2")
    assert warehouse.path != "./warehouse_test"
    assert os.path.exists(warehouse.path)


# delete_warehouse


@pytest.mark.django_db
def test_delete_warehouse(default_config):
    init_warehouses(default_config)
    warehouse = Warehouse.objects.create(
        name="a",
        path=os.path.abspath("default_warehouse_test"),
        is_default=True,
    )
    delete_warehouse(id=warehouse.id)


def test_delete_warehouse_with_invalid_id_throws_exception(default_config):
    init_warehouses(default_config)
    with pytest.raises(AfDoesNotExistException):
        delete_warehouse(id=500)
