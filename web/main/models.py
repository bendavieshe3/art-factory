# web/main/models.py
# Third Party
from django.db import models


class Warehouse(models.Model):
    name = models.CharField(max_length=100, null=False)
    path = models.CharField(max_length=255, unique=True)
    is_default = models.BooleanField(null=False, default=False)

    def __str__(self):
        return f"{self.name}"
