# Third Party
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("settings/warehouses/", views.warehouse_list, name="warehouse_list"),
    path("settings/console/", views.console, name="console"),
]
