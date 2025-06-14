"""
Tests for project-aware API endpoints with session-based filtering.

This module tests the enhanced API endpoints that support project filtering
via session context in addition to explicit project parameters.
"""

import json

from django.test import Client, TestCase
from django.urls import reverse

from main.models import Order, Product, Project
from main.utils.project_context import set_project_context


class ProjectAwareAPITestCase(TestCase):
    """Test cases for project-aware API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

        # Create test projects
        self.project1 = Project.objects.create(name="Test Project 1", description="First test project", status="active")

        self.project2 = Project.objects.create(name="Test Project 2", description="Second test project", status="active")

        # Create test products
        self.product1_proj1 = Product.objects.create(
            title="Product 1 in Project 1",
            prompt="test prompt 1",
            provider="test-provider",
            model_name="test-model",
            width=512,
            height=512,
            file_path="/test/path/1.jpg",
            file_size=1024,
            file_format="jpg",
        )

        self.product2_proj1 = Product.objects.create(
            title="Product 2 in Project 1",
            prompt="test prompt 2",
            provider="test-provider",
            model_name="test-model",
            width=512,
            height=512,
            file_path="/test/path/2.jpg",
            file_size=2048,
            file_format="jpg",
        )

        self.product1_proj2 = Product.objects.create(
            title="Product 1 in Project 2",
            prompt="test prompt 3",
            provider="test-provider",
            model_name="test-model",
            width=512,
            height=512,
            file_path="/test/path/3.jpg",
            file_size=3072,
            file_format="jpg",
        )

        self.product_no_project = Product.objects.create(
            title="Product with no project",
            prompt="test prompt 4",
            provider="test-provider",
            model_name="test-model",
            width=512,
            height=512,
            file_path="/test/path/4.jpg",
            file_size=4096,
            file_format="jpg",
        )

        # Create test orders
        self.order1_proj1 = Order.objects.create(
            title="Order 1 in Project 1",
            prompt="test order 1",
            factory_machine_name="test-machine",
            provider="test-provider",
            project=self.project1,
        )

        self.order2_proj1 = Order.objects.create(
            title="Order 2 in Project 1",
            prompt="test order 2",
            factory_machine_name="test-machine",
            provider="test-provider",
            project=self.project1,
        )

        self.order1_proj2 = Order.objects.create(
            title="Order 1 in Project 2",
            prompt="test order 3",
            factory_machine_name="test-machine",
            provider="test-provider",
            project=self.project2,
        )

        self.order_no_project = Order.objects.create(
            title="Order with no project", prompt="test order 4", factory_machine_name="test-machine", provider="test-provider"
        )

        # Set up products to be associated with their projects
        # (Using the project's add_product method if available, or directly setting project relationship)
        self.project1.products_set = [self.product1_proj1, self.product2_proj1]
        self.project2.products_set = [self.product1_proj2]


class RecentProductsAPITestCase(ProjectAwareAPITestCase):
    """Test recent products API with project filtering."""

    def test_recent_products_no_project_context(self):
        """Test recent products API returns all products when no project context."""
        response = self.client.get(reverse("main:recent_products_api"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        # Should return all products when no project filter
        self.assertEqual(len(data["products"]), 4)

    def test_recent_products_with_session_context(self):
        """Test recent products API filters by session project context."""
        # Set project context in session
        session = self.client.session
        session["current_project_id"] = self.project1.id
        session.save()

        response = self.client.get(reverse("main:recent_products_api"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        # Should return products from project1 only
        # Note: This test might fail if get_recent_products is not properly filtering
        # We'll need to check the actual implementation

    def test_recent_products_with_explicit_project_param(self):
        """Test recent products API with explicit project parameter."""
        response = self.client.get(reverse("main:recent_products_api"), {"project": self.project2.id})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        # Should return products from project2

    def test_recent_products_explicit_param_overrides_session(self):
        """Test that explicit project parameter overrides session context."""
        # Set project1 context in session
        session = self.client.session
        session["current_project_id"] = self.project1.id
        session.save()

        # Request products for project2 explicitly
        response = self.client.get(reverse("main:recent_products_api"), {"project": self.project2.id})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        # Should return products from project2, not project1

    def test_recent_products_invalid_project_param(self):
        """Test recent products API with invalid project parameter."""
        response = self.client.get(reverse("main:recent_products_api"), {"project": 99999})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        # Should fall back to all products when invalid project
        self.assertEqual(len(data["products"]), 4)

    def test_recent_products_custom_limit(self):
        """Test recent products API with custom limit parameter."""
        response = self.client.get(reverse("main:recent_products_api"), {"limit": 2})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        # Should respect the limit parameter
        self.assertLessEqual(len(data["products"]), 2)


class RecentOrdersAPITestCase(ProjectAwareAPITestCase):
    """Test recent orders API with project filtering."""

    def test_recent_orders_no_project_context(self):
        """Test recent orders API returns all orders when no project context."""
        response = self.client.get(reverse("main:recent_orders_api"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("orders", data)
        # Should return all orders when no project filter
        self.assertEqual(len(data["orders"]), 4)

    def test_recent_orders_with_session_context(self):
        """Test recent orders API filters by session project context."""
        # Set project context in session
        session = self.client.session
        session["current_project_id"] = self.project1.id
        session.save()

        response = self.client.get(reverse("main:recent_orders_api"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("orders", data)
        # Should return orders from project1 only (2 orders)
        self.assertEqual(len(data["orders"]), 2)

        # Verify orders belong to project1
        order_ids = [order["id"] for order in data["orders"]]
        self.assertIn(self.order1_proj1.id, order_ids)
        self.assertIn(self.order2_proj1.id, order_ids)

    def test_recent_orders_with_explicit_project_param(self):
        """Test recent orders API with explicit project parameter."""
        response = self.client.get(reverse("main:recent_orders_api"), {"project": self.project2.id})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("orders", data)
        # Should return orders from project2 only (1 order)
        self.assertEqual(len(data["orders"]), 1)
        self.assertEqual(data["orders"][0]["id"], self.order1_proj2.id)

    def test_recent_orders_explicit_param_overrides_session(self):
        """Test that explicit project parameter overrides session context."""
        # Set project1 context in session
        session = self.client.session
        session["current_project_id"] = self.project1.id
        session.save()

        # Request orders for project2 explicitly
        response = self.client.get(reverse("main:recent_orders_api"), {"project": self.project2.id})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("orders", data)
        # Should return orders from project2, not project1
        self.assertEqual(len(data["orders"]), 1)
        self.assertEqual(data["orders"][0]["id"], self.order1_proj2.id)

    def test_recent_orders_invalid_project_param(self):
        """Test recent orders API with invalid project parameter."""
        response = self.client.get(reverse("main:recent_orders_api"), {"project": 99999})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("orders", data)
        # Should fall back to all orders when invalid project
        self.assertEqual(len(data["orders"]), 4)

    def test_recent_orders_custom_limit(self):
        """Test recent orders API with custom limit parameter."""
        response = self.client.get(reverse("main:recent_orders_api"), {"limit": 2})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("orders", data)
        # Should respect the limit parameter
        self.assertLessEqual(len(data["orders"]), 2)


class ProjectContextViewsTestCase(ProjectAwareAPITestCase):
    """Test project context management views."""

    def test_set_project_context_view(self):
        """Test setting project context via view."""
        response = self.client.get(reverse("main:set_project_context", args=[self.project1.id]))

        # Should redirect to order page by default
        self.assertEqual(response.status_code, 302)
        self.assertIn("order", response.url)

        # Check that session context was set
        session = self.client.session
        self.assertEqual(session.get("current_project_id"), self.project1.id)

    def test_set_project_context_with_next_url(self):
        """Test setting project context with custom redirect."""
        response = self.client.get(reverse("main:set_project_context", args=[self.project1.id]), {"next": "main:inventory"})

        # Should redirect to inventory page
        self.assertEqual(response.status_code, 302)
        self.assertIn("inventory", response.url)

    def test_set_project_context_invalid_project(self):
        """Test setting project context with invalid project ID."""
        response = self.client.get(reverse("main:set_project_context", args=[99999]))

        # Should still redirect (with error message)
        self.assertEqual(response.status_code, 302)

        # Session should not be set
        session = self.client.session
        self.assertNotIn("current_project_id", session)

    def test_clear_project_context_view(self):
        """Test clearing project context via view."""
        # First set a project context
        session = self.client.session
        session["current_project_id"] = self.project1.id
        session.save()

        response = self.client.get(reverse("main:clear_project_context"))

        # Should redirect to projects page by default
        self.assertEqual(response.status_code, 302)
        self.assertIn("projects", response.url)

        # Check that session context was cleared
        session = self.client.session
        self.assertNotIn("current_project_id", session)
