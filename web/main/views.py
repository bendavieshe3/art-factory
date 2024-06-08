# Create your views here.
# Third Party
from django.http import HttpResponse
from django.shortcuts import render

# First Party
from shared.messages import get_test_message
from shared.services.warehouses import list_warehouses

from .models import Warehouse


def index(request):
    return HttpResponse(get_test_message())


def warehouse_list(request):
    warehouses = list_warehouses()
    return render(
        request, "settings/warehouse_list.html", {"warehouses": warehouses}
    )
