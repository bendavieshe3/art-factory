# config/init.py
import os
import sys

# Ensure the main module can be imported
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../web"))
)

from main.models import Warehouse


def check_initialised(config):
    check_warehouse(config)


def check_warehouse(config):
    default_warehouse = Warehouse.objects.filter(is_default=True).first()
    if not default_warehouse:
        default = config["default_warehouse"]
        Warehouse.objects.create(**default)
