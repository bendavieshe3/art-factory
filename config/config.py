# config/config.py
# Standard Library
import os
import sys

# Third Party
import django
import yaml

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../web"))
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "art_factory.settings")
django.setup()


def load_config():
    with open("config/settings.yaml", "r") as file:
        config = yaml.safe_load(file)
    return config
