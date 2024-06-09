# test_view.py

import pytest
from django.urls import reverse
from main.models import Warehouse


@pytest.mark.django_db
def test_warehouse_list_view(client):
    Warehouse.objects.create(
        name="Warehouse 1", path="/path/to/warehouse1", is_default=True
    )
    Warehouse.objects.create(
        name="Warehouse 2", path="/path/to/warehouse2", is_default=False
    )

    response = client.get(reverse("warehouse_list"))

    assert response.status_code == 200
    assert "Warehouse 1" in response.content.decode()
    assert "Warehouse 2" in response.content.decode()
