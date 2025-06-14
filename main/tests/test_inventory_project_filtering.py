"""
Test for inventory project filtering bug with batch generation.
This test reproduces the issue where only one product per order is shown
when filtering by project for batch orders.
"""

from django.test import TestCase, Client
from django.urls import reverse
from main.models import Project, Order, OrderItem, Product, FactoryMachineDefinition


class InventoryProjectFilteringTest(TestCase):
    """Test that inventory filtering by project shows all products from batch orders."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        self.project = Project.objects.create(
            name="Test Inventory Project", description="Testing inventory project filtering", status="active"
        )

        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test_inventory_machine",
            display_name="Test Inventory Machine",
            provider="test",
            modality="image",
            is_active=True,
            parameter_schema={},
            default_parameters={},
        )

    def test_inventory_shows_all_batch_products_when_filtered_by_project(self):
        """Test that inventory page shows all products from batch orders when filtered by project."""
        # Create an order with a project (simulating batch generation)
        order = Order.objects.create(
            title="Batch Order for Inventory Test",
            prompt="test batch prompt",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            project=self.project,
            quantity=4,  # Batch of 4 products
        )

        # Create an order item (representing a batch)
        order_item = OrderItem.objects.create(
            order=order, prompt="test batch prompt", parameters={}, batch_size=4, total_quantity=4
        )

        # Create 4 products in the batch (simulating what factory machine would do)
        batch_products = []
        for i in range(4):
            product = Product.objects.create(
                title=f"Batch Product {i}",
                prompt="test batch prompt",
                provider=self.factory_machine.provider,
                model_name=self.factory_machine.name,
                file_path=f"test/inventory_batch_{i}.jpg",
                file_size=1024,
                file_format="jpg",
                width=1024,
                height=1024,
                order_item=order_item,  # All products linked to same order item
            )
            batch_products.append(product)

        # Associate first product with order item for backward compatibility
        order_item.product = batch_products[0]
        order_item.save()

        # Create another order with different project to ensure filtering works
        other_project = Project.objects.create(
            name="Other Project", description="Another project for testing", status="active"
        )

        other_order = Order.objects.create(
            title="Other Order",
            prompt="other prompt",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            project=other_project,
            quantity=2,
        )

        other_order_item = OrderItem.objects.create(
            order=other_order, prompt="other prompt", parameters={}, batch_size=2, total_quantity=2
        )

        # Create 2 products for the other project
        for i in range(2):
            Product.objects.create(
                title=f"Other Product {i}",
                prompt="other prompt",
                provider=self.factory_machine.provider,
                model_name=self.factory_machine.name,
                file_path=f"test/other_{i}.jpg",
                file_size=1024,
                file_format="jpg",
                width=1024,
                height=1024,
                order_item=other_order_item,
            )

        # Test inventory page without filter (should show all 6 products)
        response = self.client.get(reverse("main:inventory"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("products_json", response.context)

        # Parse the products JSON to count products
        import json

        all_products_json = json.loads(response.context["products_json"])
        self.assertEqual(len(all_products_json), 6, "Inventory should show all 6 products when not filtered")

        # Test inventory page filtered by our test project (should show all 4 batch products)
        response = self.client.get(reverse("main:inventory"), {"project": self.project.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Inventory Project")

        # Parse the filtered products JSON
        filtered_products_json = json.loads(response.context["products_json"])

        # This is the bug: currently only showing 1 product instead of all 4 batch products
        self.assertEqual(len(filtered_products_json), 4, "Inventory should show all 4 batch products when filtered by project")

        # Verify all our batch products are in the filtered results
        filtered_product_titles = [p["title"] for p in filtered_products_json]
        for i in range(4):
            self.assertIn(f"Batch Product {i}", filtered_product_titles, f"Batch Product {i} should be in filtered inventory")

        # Verify other project's products are not included
        for i in range(2):
            self.assertNotIn(
                f"Other Product {i}", filtered_product_titles, f"Other Product {i} should not be in filtered inventory"
            )

    def test_inventory_filtering_with_multiple_batch_orders_in_same_project(self):
        """Test inventory filtering when project has multiple batch orders."""
        # Create first batch order
        order1 = Order.objects.create(
            title="First Batch Order",
            prompt="first batch prompt",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            project=self.project,
            quantity=3,
        )

        order_item1 = OrderItem.objects.create(
            order=order1, prompt="first batch prompt", parameters={}, batch_size=3, total_quantity=3
        )

        # Create 3 products for first batch
        for i in range(3):
            Product.objects.create(
                title=f"First Batch Product {i}",
                prompt="first batch prompt",
                provider=self.factory_machine.provider,
                model_name=self.factory_machine.name,
                file_path=f"test/first_batch_{i}.jpg",
                file_size=1024,
                file_format="jpg",
                width=1024,
                height=1024,
                order_item=order_item1,
            )

        # Create second batch order
        order2 = Order.objects.create(
            title="Second Batch Order",
            prompt="second batch prompt",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            project=self.project,
            quantity=2,
        )

        order_item2 = OrderItem.objects.create(
            order=order2, prompt="second batch prompt", parameters={}, batch_size=2, total_quantity=2
        )

        # Create 2 products for second batch
        for i in range(2):
            Product.objects.create(
                title=f"Second Batch Product {i}",
                prompt="second batch prompt",
                provider=self.factory_machine.provider,
                model_name=self.factory_machine.name,
                file_path=f"test/second_batch_{i}.jpg",
                file_size=1024,
                file_format="jpg",
                width=1024,
                height=1024,
                order_item=order_item2,
            )

        # Test inventory filtered by project (should show all 5 products from both batches)
        response = self.client.get(reverse("main:inventory"), {"project": self.project.id})
        self.assertEqual(response.status_code, 200)

        import json

        filtered_products_json = json.loads(response.context["products_json"])

        # Should show all 5 products (3 from first batch + 2 from second batch)
        self.assertEqual(len(filtered_products_json), 5, "Inventory should show all products from both batch orders")

        # Verify all products are present
        filtered_product_titles = [p["title"] for p in filtered_products_json]

        for i in range(3):
            self.assertIn(
                f"First Batch Product {i}", filtered_product_titles, f"First Batch Product {i} should be in filtered inventory"
            )

        for i in range(2):
            self.assertIn(
                f"Second Batch Product {i}",
                filtered_product_titles,
                f"Second Batch Product {i} should be in filtered inventory",
            )

    def test_inventory_pagination_with_project_filtering(self):
        """Test that pagination works correctly with project filtering and batch products."""
        # Create a large batch to test pagination
        order = Order.objects.create(
            title="Large Batch Order",
            prompt="large batch prompt",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            project=self.project,
            quantity=25,  # More than default page size
        )

        order_item = OrderItem.objects.create(
            order=order, prompt="large batch prompt", parameters={}, batch_size=25, total_quantity=25
        )

        # Create 25 products
        for i in range(25):
            Product.objects.create(
                title=f"Large Batch Product {i:02d}",
                prompt="large batch prompt",
                provider=self.factory_machine.provider,
                model_name=self.factory_machine.name,
                file_path=f"test/large_batch_{i:02d}.jpg",
                file_size=1024,
                file_format="jpg",
                width=1024,
                height=1024,
                order_item=order_item,
            )

        # Test first page of filtered inventory
        response = self.client.get(reverse("main:inventory"), {"project": self.project.id})
        self.assertEqual(response.status_code, 200)

        # Should show first 20 products (default page size)
        import json

        page1_products = json.loads(response.context["products_json"])
        self.assertEqual(len(page1_products), 20, "First page should show 20 products")

        # Test second page
        response = self.client.get(reverse("main:inventory"), {"project": self.project.id, "page": 2})
        self.assertEqual(response.status_code, 200)

        # Should show remaining 5 products
        page2_products = json.loads(response.context["products_json"])
        self.assertEqual(len(page2_products), 5, "Second page should show remaining 5 products")
