# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
from shared.messages import get_test_message
from .models import Warehouse


def index(request):
    return HttpResponse(get_test_message())


def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    return render(
        request, "settings/warehouse_list.html", {"warehouses": warehouses}
    )
