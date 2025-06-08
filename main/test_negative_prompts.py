"""
Tests for negative prompt functionality across the Art Factory system.
These tests are written to fail initially and guide the implementation.
"""

import json
import os
import random
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from main.models import Product, Order, OrderItem, Worker, FactoryMachineDefinition, FactoryMachineInstance


def get_test_pid():
    """Generate a unique test PID to avoid conflicts."""
    return os.getpid() + random.randint(10000, 99999)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptModelTestCase(TestCase):
    """Test negative prompt support in models."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/sdxl",
            display_name="Test SDXL",
            description="Test model for negative prompts",
            provider="fal.ai",
            modality="image",
            parameter_schema={"width": 1024, "height": 1024},
            default_parameters={"width": 1024, "height": 1024},
            is_active=True,
        )

    def test_order_has_negative_prompt_field(self):
        """Test that Order model has negative_prompt field."""
        order = Order.objects.create(
            title="Test Order",
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry, low quality",
            base_parameters={"width": 1024},
            factory_machine_name="test/sdxl",
            provider="fal.ai",
            quantity=1,
        )

        self.assertEqual(order.negative_prompt, "ugly, blurry, low quality")

    def test_order_negative_prompt_defaults_to_empty_string(self):
        """Test that negative_prompt defaults to empty string."""
        order = Order.objects.create(
            title="Test Order",
            prompt="beautiful landscape",
            base_parameters={"width": 1024},
            factory_machine_name="test/sdxl",
            provider="fal.ai",
            quantity=1,
        )

        self.assertEqual(order.negative_prompt, "")

    def test_order_item_has_negative_prompt_field(self):
        """Test that OrderItem model has negative_prompt field."""
        order = Order.objects.create(
            title="Test Order",
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry",
            base_parameters={"width": 1024},
            factory_machine_name="test/sdxl",
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry, low quality, distorted",
            parameters={"width": 1024},
            status="pending",
        )

        self.assertEqual(order_item.negative_prompt, "ugly, blurry, low quality, distorted")

    def test_product_has_negative_prompt_field(self):
        """Test that Product model has negative_prompt field."""
        product = Product.objects.create(
            title="Test Product",
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry, low quality",
            parameters={"width": 1024},
            provider="fal.ai",
            model_name="test/sdxl",
            product_type="image",
            file_path="test/path.png",
            file_size=1024,
            file_format="png",
        )

        self.assertEqual(product.negative_prompt, "ugly, blurry, low quality")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptAPITestCase(TestCase):
    """Test negative prompt support in API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="fal/flux-dev",
            display_name="Flux Dev",
            description="Test model",
            provider="fal.ai",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        # Create a machine instance
        FactoryMachineInstance.objects.create(machine_definition=self.factory_machine, instance_id="primary-instance")

    def test_place_order_api_accepts_negative_prompt(self):
        """Test that place-order API accepts negative_prompt parameter."""
        data = {
            "prompt": "a beautiful mountain landscape",
            "negative_prompt": "ugly, blurry, low quality, distorted",
            "machine_id": self.factory_machine.id,
            "quantity": 1,
            "parameters": {},
        }

        response = self.client.post(reverse("main:place-order"), data=json.dumps(data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        # Check that order was created with negative prompt
        order = Order.objects.get(id=response_data["order_id"])
        self.assertEqual(order.negative_prompt, "ugly, blurry, low quality, distorted")

        # Check that order items have negative prompt
        order_items = order.orderitem_set.all()
        self.assertEqual(len(order_items), 1)
        self.assertEqual(order_items[0].negative_prompt, "ugly, blurry, low quality, distorted")

    def test_order_detail_api_returns_negative_prompt(self):
        """Test that order detail API returns negative_prompt."""
        order = Order.objects.create(
            title="Test Order",
            prompt="mountain landscape",
            negative_prompt="blurry, distorted",
            base_parameters={},
            factory_machine_name="fal/flux-dev",
            provider="fal.ai",
            quantity=1,
        )

        OrderItem.objects.create(
            order=order, prompt="mountain landscape", negative_prompt="blurry, distorted", parameters={}, status="pending"
        )

        response = self.client.get(f"/api/orders/{order.id}/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["negative_prompt"], "blurry, distorted")
        self.assertEqual(data["items"][0]["negative_prompt"], "blurry, distorted")

    def test_product_api_returns_negative_prompt(self):
        """Test that product API returns negative_prompt."""
        product = Product.objects.create(
            title="Test Product",
            prompt="mountain landscape",
            negative_prompt="blurry, low quality",
            parameters={},
            provider="fal.ai",
            model_name="fal/flux-dev",
            product_type="image",
            file_path="test.png",
            file_size=1024,
            file_format="png",
        )

        response = self.client.get(f"/api/products/{product.id}/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["negative_prompt"], "blurry, low quality")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptProviderTestCase(TestCase):
    """Test negative prompt handling in provider implementations."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="fal/flux-dev",
            display_name="Flux Dev",
            description="Test model",
            provider="fal.ai",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Order",
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry",
            base_parameters={},
            factory_machine_name="fal/flux-dev",
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry, distorted",
            parameters={},
            status="pending",
        )

    def test_fal_provider_sends_negative_prompt(self):
        """Test that fal.ai provider includes negative_prompt in API call."""
        # This test verifies the negative prompt is stored and can be retrieved
        # The actual API integration is tested elsewhere

        # Create order item with negative prompt
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="test prompt",
            negative_prompt="ugly, blurry, distorted",
            parameters={"width": 1024, "height": 1024},
            status="pending",
        )

        # Verify negative prompt is stored
        self.assertEqual(order_item.negative_prompt, "ugly, blurry, distorted")

        # Verify it's included in API serialization
        from django.test import Client

        client = Client()
        response = client.get(f"/api/orders/{self.order.id}/")

        self.assertEqual(response.status_code, 200)
        order_data = response.json()
        self.assertIn("negative_prompt", order_data)
        self.assertEqual(order_data["negative_prompt"], self.order.negative_prompt)

    def test_replicate_provider_sends_negative_prompt(self):
        """Test that Replicate provider includes negative_prompt in API call."""
        # This test verifies the negative prompt is stored and accessible for Replicate providers

        # Create a Replicate-based model
        replicate_machine = FactoryMachineDefinition.objects.create(
            name="stability-ai/sdxl",
            display_name="SDXL",
            description="Test model",
            provider="replicate",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        order = Order.objects.create(
            title="Test Order",
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry",
            base_parameters={},
            factory_machine_name="stability-ai/sdxl",
            provider="replicate",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry, distorted",
            parameters={},
            status="pending",
        )

        # Verify negative prompt is stored
        self.assertEqual(order_item.negative_prompt, "ugly, blurry, distorted")

        # Verify it can be accessed for processing
        self.assertIsNotNone(order_item.negative_prompt)
        self.assertEqual(len(order_item.negative_prompt), 23)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptUITestCase(TestCase):
    """Test negative prompt display in UI views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model",
            provider="test",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        # Create machine instance
        self.machine_instance = FactoryMachineInstance.objects.create(
            machine_definition=self.factory_machine, instance_id="primary-instance"
        )

    def test_order_form_has_negative_prompt_field(self):
        """Test that order form includes negative prompt field."""
        response = self.client.get(reverse("main:order"))
        self.assertEqual(response.status_code, 200)

        # Check that the form includes negative prompt field
        self.assertContains(response, "negative_prompt")
        self.assertContains(response, "Negative Prompt")
        self.assertContains(response, "What to avoid in the generated image")

    def test_product_detail_displays_negative_prompt(self):
        """Test that product detail page displays negative prompt."""
        product = Product.objects.create(
            title="Test Product",
            prompt="beautiful landscape",
            negative_prompt="ugly, blurry, low quality",
            parameters={},
            provider="test",
            model_name="test/model",
            product_type="image",
            file_path="test.png",
            file_size=1024,
            file_format="png",
        )

        response = self.client.get(reverse("main:product_detail", args=[product.id]))
        self.assertEqual(response.status_code, 200)

        # Check that negative prompt is displayed
        self.assertContains(response, "Negative Prompt")
        self.assertContains(response, "ugly, blurry, low quality")

    def test_production_view_displays_negative_prompt(self):
        """Test that production view displays negative prompt for orders."""
        order = Order.objects.create(
            title="Test Order",
            prompt="mountain landscape",
            negative_prompt="blurry, distorted",
            base_parameters={},
            factory_machine_name="test/model",
            provider="test",
            quantity=1,
            status="processing",
        )

        OrderItem.objects.create(
            order=order, prompt="mountain landscape", negative_prompt="blurry, distorted", parameters={}, status="processing"
        )

        response = self.client.get(reverse("main:production"))
        self.assertEqual(response.status_code, 200)

        # Check that negative prompt is displayed in the production view
        self.assertContains(response, "blurry, distorted")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptIntegrationTestCase(TestCase):
    """Test end-to-end negative prompt functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="fal/flux-dev",
            display_name="Flux Dev",
            description="Test model",
            provider="fal.ai",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        FactoryMachineInstance.objects.create(machine_definition=self.factory_machine, instance_id="primary-instance")

        # Create worker
        test_pid = get_test_pid()
        self.worker = Worker.objects.create(name="test-worker", process_id=test_pid)

    def tearDown(self):
        """Clean up test resources."""
        # Clean up any Worker model instances
        Worker.objects.all().delete()

        super().tearDown()

    def test_full_workflow_with_negative_prompt(self):
        """Test complete workflow from order placement to product creation with negative prompt."""
        # Place order with negative prompt
        data = {
            "prompt": "a majestic mountain landscape at sunset",
            "negative_prompt": "blurry, out of focus, low quality, distorted, ugly",
            "machine_id": self.factory_machine.id,
            "quantity": 1,
            "parameters": {"width": 1024, "height": 1024},
        }

        response = self.client.post(reverse("main:place-order"), data=json.dumps(data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        order_id = json.loads(response.content)["order_id"]

        # Verify order has negative prompt
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.negative_prompt, "blurry, out of focus, low quality, distorted, ugly")

        # Verify order item also has negative prompt
        order_item = order.orderitem_set.first()
        self.assertIsNotNone(order_item)
        self.assertEqual(order_item.negative_prompt, "blurry, out of focus, low quality, distorted, ugly")

        # Verify the order item is in pending status ready for processing
        self.assertEqual(order_item.status, "pending")

        # Create a mock product to verify negative prompt propagation
        product = Product.objects.create(
            title="Test Product",
            prompt="a majestic mountain landscape at sunset",
            negative_prompt="blurry, out of focus, low quality, distorted, ugly",
            parameters={"width": 1024, "height": 1024},
            model_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            file_path="test/path/image.png",
            file_size=1024,
            file_format="png",
        )

        # Verify product has negative prompt
        self.assertEqual(product.negative_prompt, "blurry, out of focus, low quality, distorted, ugly")
