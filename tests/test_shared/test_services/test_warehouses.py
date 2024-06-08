# Standard Library
import os

# Third Party
import pytest
from django.core.management import call_command

# First Party
from shared.exceptions import AfDuplicateException


# @pytest.fixture(scope="session", autouse=True)
def django_setup():
    os.environ["DJANGO_SETTINGS_MODULE"] = "art_factory.settings"

    # Third Party
    import django

    django.setup()

    # Run migrations before tests
    call_command("migrate")


django_setup()
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


@pytest.fixture
def default_config():
    return {
        "default_warehouse": {
            "name": "Default",
            "path": "default_warehouse",
            "is_default": True,
        }
    }


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


@pytest.mark.django_db
def test_delete_warehouse(default_config):
    init_warehouses(default_config)
    warehouse = Warehouse.objects.create(
        name="a",
        path=os.path.abspath("default_warehouse_test"),
        is_default=True,
    )
    delete_warehouse(id=warehouse.id)
