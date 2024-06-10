# Create your views here.
# Third Party
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# First Party
from shared.messages import get_test_message
from shared.services.warehouses import list_warehouses

from .models import Warehouse


def index(request):
    return render(request, "index.html", {})


def warehouse_list(request):
    warehouses = list_warehouses()
    return render(
        request, "settings/warehouse_list.html", {"warehouses": warehouses}
    )


def console(request):
    return render(request, "settings/console.html", {})
