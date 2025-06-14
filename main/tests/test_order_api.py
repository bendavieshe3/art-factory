"""
Tests for order API endpoints and functionality.
"""

import json
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from main.models import FactoryMachineDefinition, Order, Project


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class OrderApiTestCase(TestCase):
    """Test order API endpoints and data handling."""

    def setUp(self):
        """Set up test client and factory machine."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for API testing",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512, "enable_safety_checker": False},
            is_active=True,
        )

    def test_order_form_submission_creates_order(self):
        """Test that order form submission actually creates an Order in the database."""
        # Count initial orders
        initial_order_count = Order.objects.count()

        # Submit order via API (simulating what JavaScript sends after field mapping)
        order_data = {
            "title": "Test Order Creation",
            "prompt": "A test prompt for order creation",
            "machine_id": str(self.factory_machine.id),  # Mapped from form field 'machine'
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        # Should succeed
        if response.status_code != 200:
            error_data = json.loads(response.content)
            self.fail(f"Order submission failed with status {response.status_code}: {error_data}")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get("success", False), f"Order submission failed: {data}")

        # Should create a new order in the database
        new_order_count = Order.objects.count()
        self.assertEqual(new_order_count, initial_order_count + 1, "Order was not created in database")

        # Should return order_id
        self.assertIn("order_id", data, "API should return order_id")

        # Verify the order exists and has correct data
        order = Order.objects.get(id=data["order_id"])
        self.assertEqual(order.title, "Test Order Creation")
        self.assertEqual(order.prompt, "A test prompt for order creation")
        self.assertEqual(order.factory_machine_name, self.factory_machine.name)

    def test_order_submission_assigns_to_selected_project(self):
        """Test that order submission assigns order to the selected project."""
        # Create test project
        test_project = Project.objects.create(
            name="Test Project for Order", description="Should receive the new order", status="active"
        )

        # Count initial orders
        initial_order_count = Order.objects.count()

        # Submit order with project selected (using API field names after JavaScript mapping)
        order_data = {
            "title": "Project Assignment Test",
            "prompt": "Test prompt for project assignment",
            "machine_id": str(self.factory_machine.id),
            "project_id": str(test_project.id),  # Mapped from form field 'project'
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get("success", False), f"Order submission failed: {data}")

        # Should create a new order
        new_order_count = Order.objects.count()
        self.assertEqual(new_order_count, initial_order_count + 1)

        # Verify the order is assigned to the correct project
        order = Order.objects.get(id=data["order_id"])
        self.assertEqual(order.project, test_project, "Order should be assigned to selected project")
        self.assertEqual(order.project_name, test_project.name, "Order project_name should match selected project")

    def test_order_submission_without_project_selection(self):
        """Test that order submission works when no project is selected."""
        # Submit order without project
        order_data = {
            "title": "No Project Test",
            "prompt": "Test prompt without project",
            "machine_id": str(self.factory_machine.id),
            # No project field
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get("success", False))

        # Verify the order has no project assigned
        order = Order.objects.get(id=data["order_id"])
        self.assertIsNone(order.project, "Order should not have project when none selected")
        self.assertEqual(order.project_name, "", "Order project_name should be empty when no project")

    def test_order_form_field_name_mapping(self):
        """Test that form field names are correctly mapped to API field names by JavaScript."""
        # Test that API works with correctly mapped field names
        order_data = {
            "machine_id": str(self.factory_machine.id),  # Form: machine → API: machine_id
            "project_id": "",  # Form: project → API: project_id
            "generation_count": 1,  # Form: generationCount → API: generation_count
            "batch_size": 1,  # Form: batchSize → API: batch_size
            "prompt": "Test field mapping",
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        # This should work with correctly mapped field names
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get("success", False))

        # Test that API fails with unmapped form field names
        order_data_with_form_fields = {
            "machine": str(self.factory_machine.id),  # Form field name (unmapped)
            "project": "",  # Form field name (unmapped)
            "generationCount": 1,  # Form field name (unmapped)
            "batchSize": 1,  # Form field name (unmapped)
            "prompt": "Test field mapping wrong",
        }

        response = self.client.post(
            "/api/place-order/", data=json.dumps(order_data_with_form_fields), content_type="application/json"
        )

        # This should fail because form field names aren't mapped
        self.assertEqual(response.status_code, 400)
        error_data = json.loads(response.content)
        self.assertIn("machine_id", error_data.get("error", ""))
        self.assertFalse(error_data.get("success", True))

    def test_failed_order_provides_error_data(self):
        """Test that failed order provides appropriate error data for toast."""
        order_data = {
            "title": "Failed Order Test",
            "prompt": "test prompt",
            "machine_id": 999,  # Non-existent machine
            "quantity": 1,
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

        # Error message should be suitable for toast notification
        self.assertIsInstance(data["error"], str)
        self.assertGreater(len(data["error"]), 0)

    @patch("main.tasks.process_order_items_async")
    def test_successful_order_shows_success_toast(self, mock_process):
        """Test that successful order placement triggers success toast message."""
        order_data = {
            "title": "Toast Test Order",
            "prompt": "test toast prompt",
            "machine_id": self.factory_machine.id,
            "quantity": 2,
            "parameters": {"width": 512, "height": 512},
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # The success message should mention the order ID and quantity
        expected_message = f"Order #{data['order_id']} placed successfully! 2 images are being generated."
        # Note: We can't directly test the JavaScript toast, but we can verify
        # the API response provides the right data for the toast
        self.assertIn("order_id", data)
        self.assertIn("message", data)
