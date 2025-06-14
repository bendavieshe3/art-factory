"""
Test the place order API with session-based project context.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse

from main.models import Project, FactoryMachineDefinition, Order


class SessionBasedOrderAPITestCase(TestCase):
    """Test cases for session-based project context in order API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

        # Create test project
        self.project = Project.objects.create(name="Test API Project", description="Test project for API", status="active")

        # Create test machine
        self.machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512},
            is_active=True,
        )

    def test_order_api_uses_session_project_context(self):
        """Test that order API uses session context for project assignment."""
        # Set project context in session
        session = self.client.session
        session["current_project_id"] = self.project.id
        session.save()

        # Get CSRF token
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Create order via API
        order_data = {
            "machine_id": self.machine.id,
            "prompt": "A test image for API testing",
            "negative_prompt": "blurry, low quality",
            "title": "Test API Order",
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post(
            "/api/place-order/",
            data=json.dumps(order_data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data.get("success"), f"Order creation failed: {response_data}")

        # Verify the order was assigned to the project from session context
        order_id = response_data.get("order_id")
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.project, self.project, "Order should be assigned to project from session context")

    def test_order_api_without_session_context(self):
        """Test that order API works without session context (no project assignment)."""
        # Don't set any session context

        # Get CSRF token
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Create order via API
        order_data = {
            "machine_id": self.machine.id,
            "prompt": "A test image without project",
            "negative_prompt": "blurry, low quality",
            "title": "Test API Order No Project",
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post(
            "/api/place-order/",
            data=json.dumps(order_data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data.get("success"), f"Order creation failed: {response_data}")

        # Verify the order has no project assigned
        order_id = response_data.get("order_id")
        order = Order.objects.get(id=order_id)
        self.assertIsNone(order.project, "Order should not be assigned to any project without session context")

    def test_order_api_explicit_project_id_overrides_session(self):
        """Test that explicit project_id parameter overrides session context."""
        # Create second project
        project2 = Project.objects.create(name="Second Project", description="Another test project", status="active")

        # Set first project in session
        session = self.client.session
        session["current_project_id"] = self.project.id
        session.save()

        # Get CSRF token
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Create order with explicit project_id (different from session)
        order_data = {
            "machine_id": self.machine.id,
            "prompt": "A test image with explicit project",
            "project_id": project2.id,  # Explicit project override
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post(
            "/api/place-order/",
            data=json.dumps(order_data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data.get("success"), f"Order creation failed: {response_data}")

        # Verify the order was assigned to the explicit project, not session project
        order_id = response_data.get("order_id")
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.project, project2, "Order should be assigned to explicit project_id, not session project")

    def test_order_api_invalid_session_project_id(self):
        """Test that API handles invalid session project ID gracefully."""
        # Set invalid project ID in session
        session = self.client.session
        session["current_project_id"] = 99999  # Non-existent project
        session.save()

        # Get CSRF token
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Create order via API
        order_data = {
            "machine_id": self.machine.id,
            "prompt": "A test image with invalid session project",
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post(
            "/api/place-order/",
            data=json.dumps(order_data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data.get("success"), f"Order creation failed: {response_data}")

        # Verify the order has no project assigned (invalid session project ignored)
        order_id = response_data.get("order_id")
        order = Order.objects.get(id=order_id)
        self.assertIsNone(order.project, "Order should not be assigned to invalid session project")
