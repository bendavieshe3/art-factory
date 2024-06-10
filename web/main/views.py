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


from django.http import JsonResponse


def sitemap(request):
    sitemap_data = {
        "sections": {
            "Projects": {
                "Overview": "/projects/overview",
                "Portfolio": "/projects/portfolio",
                "Browse": "/projects/browse",
            },
            "Production": {"Overview": "/production/overview"},
            "Compositions": {
                "Batches": "/compositions/batches",
                "Search": "/compositions/search",
            },
            "Lab": {
                "Image Comparator": "/lab/image-comparator",
                "Factory Settings": "/lab/factory-settings",
                "Replacement Parts": "/lab/replacement-parts",
            },
            "Process": {
                "Pipelines": "/process/pipelines",
                "Factory Processes": "/process/factory-processes",
                "Replacement Parts": "/process/replacement-parts",
                "Warehouses": "/process/warehouses/",
            },
            "Settings": {"Warehouses": "/settings/warehouses/"},
        }
    }
    return JsonResponse(sitemap_data)
