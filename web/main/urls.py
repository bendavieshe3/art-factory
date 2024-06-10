# Third Party
from django.urls import path

from . import views

urlpatterns = [
    path("sitemap.json", views.sitemap, name="sitemap"),
    path("", views.index, name="index"),
    path("settings/warehouses/", views.warehouse_list, name="warehouse_list"),
]
