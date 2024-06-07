# shared/services/warehouses
from main.models import Warehouse


def init_warehouses(config):
    default_warehouse = Warehouse.objects.filter(is_default=True).first()
    if not default_warehouse:
        default = config["default_warehouse"]
        Warehouse.objects.create(**default)
