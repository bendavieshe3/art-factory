import os

import pytest
from django.core.management import call_command


# @pytest.fixture(scope="session", autouse=True)
def django_setup():
    os.environ["DJANGO_SETTINGS_MODULE"] = "art_factory.settings"

    import django

    django.setup()

    # Run migrations before tests
    call_command("migrate")


django_setup()
from main.models import Warehouse

from shared.services.warehouses import init_warehouses


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
