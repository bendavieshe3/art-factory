#!/usr/bin/env python
"""Test the fixed SDXL model."""

import json
import os
import sys

import django
from django.http import JsonResponse
from django.test import RequestFactory

from main.models import FactoryMachineDefinition, Order
from main.views import place_order_api

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_art_factory.settings")
django.setup()


def test_sdxl_fix():
    """Test the corrected SDXL model with safety checker disabled."""

    # Get the SDXL machine
    machine = FactoryMachineDefinition.objects.get(display_name="Stable Diffusion XL (Replicate)")
    if not machine:
        print("SDXL machine not found!")
        return

    print(f"Using machine: {machine.display_name}")
    print(f"Model name: {machine.name}")
    print(f"Default safety checker: {machine.default_parameters.get('disable_safety_checker')}")

    # Create a test order with a safe prompt
    factory = RequestFactory()
    request_data = {
        "title": "SDXL Fix Test",
        "prompt": "A beautiful mountain landscape at sunset",
        "machine_id": machine.id,
        "generation_count": 1,
        "batch_size": 1,
        "parameters": {"width": 1024, "height": 1024, "disable_safety_checker": True},  # Explicitly disable
    }

    request = factory.post("/api/place-order/", data=json.dumps(request_data), content_type="application/json")

    # Call the API view
    response = place_order_api(request)

    if isinstance(response, JsonResponse):
        response_data = json.loads(response.content)
        if response_data.get("success"):
            order_id = response_data["order_id"]
            order = Order.objects.get(id=order_id)

            print(f"\n✅ Order {order_id} created successfully!")

            # Check the order item
            item = order.orderitem_set.first()
            print(f"Order item parameters: {item.parameters}")

            # Process the item to test the fix
            from main.factory_machines_sync import execute_order_item_sync_batch

            print(f"\nProcessing item {item.id}...")
            success = execute_order_item_sync_batch(item.id)

            # Check result
            item.refresh_from_db()
            print(f"Final status: {item.status}")

            if item.status == "completed":
                print("✅ SDXL model working correctly!")
                products = item.products.all()
                print(f"Products created: {products.count()}")
                return True
            elif item.status == "failed":
                print(f"❌ Processing failed: {item.error_message}")
                return False
        else:
            print(f"❌ Order failed: {response_data.get('error')}")
            return False
    else:
        print(f"❌ Unexpected response type: {type(response)}")
        return False


if __name__ == "__main__":
    success = test_sdxl_fix()
    if success:
        print("\n✅ SDXL fix verified!")
    else:
        print("\n❌ SDXL still has issues!")
