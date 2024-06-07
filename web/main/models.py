# web/main/models.py
from django.db import models


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name
