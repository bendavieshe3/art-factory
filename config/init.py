# config/init.py
from shared.services.warehouses import init_warehouses


def check_initialised(config):
    init_warehouses(config)
